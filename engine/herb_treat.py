"""Treat from fresh/prepared herb stacks."""

from __future__ import annotations

import json
import random

import database as db
from engine.character import parse_proficiencies
from engine.conditions import (
    herb_special_effect,
    medicine_check,
    parse_injuries,
    roll_poison_herb_misuse,
    treat_with_herb,
)
from engine.dice import format_roll_result, resolve_check
from engine.exhaustion_effects import effective_max_hp
from engine.herb_buffs import (
    POISON_MISUSE_HERBS,
    apply_cough_dose,
    apply_supplemental_herb,
    grant_disease_save_advantage,
)
from engine.herb_properties import can_use_form, herb_form_rule
from engine.medical_access import can_medic_treat_cross_pack
from engine.character_traits import trait_clears_infection_on_heal, trait_treat_heal_bonus
from engine.role_features import is_full_medic
from herbs import HERBS


def _complex_wound(user) -> bool:
    injuries = parse_injuries(user["active_injuries"] if "active_injuries" in user.keys() else None)
    return bool(
        injuries
        & {
            "deep_gash",
            "fractured_rib",
            "sprained_leg",
            "broken_jaw",
            "punctured_paw",
            "infected_wound",
        }
    )


def _roll_toxic_damage(rule) -> int:
    lo, hi = rule.toxic_damage
    return random.randint(lo, hi)


def check_fresh_toxicity(user, herb_key: str, form: str, *, day: int) -> tuple[bool, str]:
    rule = herb_form_rule(herb_key)
    if form != "fresh" or not rule.toxic_if_fresh:
        return True, ""
    profs = parse_proficiencies(user["skill_proficiencies"])
    result = resolve_check(
        user,
        attr_keys=("attr_con",),
        skill="Survival",
        dc=rule.toxic_dc,
        proficient="survival" in profs or "herblore" in profs,
        skill_key="survival",
        game_day=day,
    )
    if result["success"]:
        return True, format_roll_result(result) + "\n_You spit out the worst of it in time._"
    dmg = _roll_toxic_damage(rule)
    new_hp = max(0, int(user["hp"]) - dmg)
    db.set_user_conditions(user["discord_id"], hp=new_hp)
    return (
        False,
        format_roll_result(result)
        + f"\n**Toxic fresh plant**; **−{dmg} HP**. {rule.notes}",
    )


def heal_amount_for_form(form: str, *, complex_wound: bool) -> tuple[int, int]:
    if form in ("poultice", "decoction"):
        return (1, 4)
    if form == "tonic":
        return (1, 3)
    if complex_wound:
        return (1, 2)
    return (1, 4)


def _stabilize_stack_bonus(herb_key: str, form: str) -> tuple[bool, bool, bool, bool]:
    """Return (yarrow, yarrow_fresh, oak_bark, cattail) flags for stabilize_check."""
    yarrow = herb_key == "yarrow"
    yarrow_fresh = yarrow and form == "fresh"
    oak = herb_key == "oak_bark"
    cattail = herb_key == "cattail"
    return yarrow, yarrow_fresh, oak, cattail


def treat_from_herb_stack(
    healer,
    stack_id: int,
    *,
    day: int,
    patient=None,
    guild_id: int | None = None,
) -> tuple[bool, str]:
    """
    Apply herb treatment. Stack is consumed from healer's bag; effect applies to patient.
    Defaults to self-treat when patient is omitted.
    """
    patient = patient or healer
    cond = patient["condition"] if "condition" in patient.keys() else "healthy"
    emergency = cond in ("dying",) or int(patient["hp"]) <= 0
    if guild_id and healer["id"] != patient["id"]:
        ok, reason = can_medic_treat_cross_pack(
            healer, patient, guild_id, emergency_stabilize=emergency
        )
        if not ok:
            return False, reason

    stack = db.get_herb_stack(stack_id)
    if not stack or stack["wolf_id"] != healer["id"]:
        return False, "That herb isn't in your forage bag."
    herb_key = stack["herb_key"]
    form = stack["form"]
    meta = HERBS.get(herb_key, {"cures": (), "effect": "", "name": herb_key})
    name = meta.get("name", herb_key)
    rule = herb_form_rule(herb_key)
    complex_wound = _complex_wound(patient)

    from engine.restricted_herbs import is_restricted_herb, on_restricted_herb_treat

    standing_note = ""
    if is_restricted_herb(herb_key):
        standing_note = on_restricted_herb_treat(healer, herb_key)
        if standing_note:
            standing_note = standing_note + "\n\n"

    ok, block = can_use_form(rule, form, complex_wound=complex_wound)
    if not ok:
        return False, block

    toxic_ok, toxic_msg = check_fresh_toxicity(healer, herb_key, form, day=day)
    if not toxic_ok:
        db.remove_herb_stack(stack_id)
        return False, toxic_msg

    from engine.long_term_injuries import CURE_HERBS, try_cure_long_term

    if herb_key in CURE_HERBS:
        cured, cure_msg = try_cure_long_term(herb_key, patient)
        if cured:
            db.remove_herb_stack(stack_id)
            prefix = (toxic_msg + "\n\n") if toxic_msg else ""
            if standing_note:
                prefix = standing_note + prefix
            return True, prefix + cure_msg

    if is_restricted_herb(herb_key) and not is_full_medic(healer):
        db.remove_herb_stack(stack_id)
        survived, poison_msg, _ = roll_poison_herb_misuse(patient, herb_key, day=day)
        return survived, standing_note + poison_msg

    outcome = treat_with_herb(patient, herb_key, meta)
    special = herb_special_effect(herb_key, patient)

    if outcome == "cough_dose":
        stage_cured, dose_fields, dose_msg = apply_cough_dose(patient, herb_key, day=day)
        db.remove_herb_stack(stack_id)
        prefix = (toxic_msg + "\n\n") if toxic_msg else ""
        if dose_fields:
            db.update_user(patient["discord_id"], wolf_id=patient["id"], **dose_fields)
        if stage_cured:
            db.set_user_conditions(
                patient["discord_id"], wolf_id=patient["id"], clear_disease=True, condition="healthy"
            )
            return True, prefix + f"**{name}**; {dose_msg} Cough cleared."
        return True, prefix + f"**{name}**; {dose_msg}"

    if outcome == "no_effect" and not special and herb_key not in ("comfrey", "cobwebs"):
        check = medicine_check(healer, dc=15)
        if not check["success"] and not is_full_medic(healer):
            return False, f"Medicine check: {check['total']} vs DC 15: no effect."

    db.remove_herb_stack(stack_id)
    prefix = (toxic_msg + "\n\n") if toxic_msg else ""
    if standing_note:
        prefix = standing_note + prefix
    injuries = parse_injuries(patient["active_injuries"] if "active_injuries" in patient.keys() else None)
    form_tag = f" ({form})" if form != "fresh" else ""
    msg = ""
    target_note = ""
    if healer["id"] != patient["id"]:
        target_note = f" on **{patient['wolf_name']}**"

    if special == "reduce_exhaustion":
        old_ex = int(patient["exhaustion"])
        new_ex = max(0, old_ex - 1)
        db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], exhaustion=new_ex)
        msg = f"**{name}**{form_tag}{target_note}; exhaustion **{old_ex}** → **{new_ex}**."
    elif special == "feed_pup_honey":
        from config import HONEY_PUP_HUNGER_BONUS
        from engine.nursing import apply_honey_to_pup

        fields = apply_honey_to_pup(patient, day_number=day)
        db.update_user(patient["discord_id"], wolf_id=patient["id"], **fields)
        ex_note = ""
        if "exhaustion" in fields:
            ex_note = f" Exhaustion **→ {fields['exhaustion']}**."
        msg = (
            f"**{name}**{form_tag}{target_note}; warm sweetness (**+{HONEY_PUP_HUNGER_BONUS}** hunger)."
            f"{ex_note}"
        )
    elif special == "honey_pup_not_depleted":
        return False, "Honey feeds starving pups; hunger or thirst must be low first."
    elif outcome == "cured_disease":
        db.set_user_conditions(
            patient["discord_id"], wolf_id=patient["id"], clear_disease=True, condition="healthy"
        )
        msg = f"**{name}**{form_tag}{target_note} cured the disease."
    elif outcome == "rabies_ease":
        db.update_user(patient["discord_id"], wolf_id=patient["id"], **grant_disease_save_advantage(patient))
        msg = (
            f"**{name}**{form_tag}{target_note}; herbs slow early cloudmouth; **advantage** on next disease save "
            "(one sunrise). Cloudmouth is not cured."
        )
    elif outcome == "cured_injury":
        for inj in meta.get("cures", ()):
            if inj in injuries:
                injuries.remove(inj)
                db.clear_injury_since(patient["id"], inj)
        db.set_user_conditions(
            patient["discord_id"],
            wolf_id=patient["id"],
            active_injuries=json.dumps(injuries),
            condition="healthy" if not injuries else patient["condition"],
        )
        decoct = " Decoction burned the wound clean." if form == "decoction" else ""
        msg = f"**{name}**{form_tag}{target_note} treated the injury.{decoct}"
    elif outcome == "cured_genetic":
        from engine.genetics import genetic_keys_matching_cures, remove_genetic_keys

        matched = genetic_keys_matching_cures(patient, meta.get("cures", ()))
        new_genetics = remove_genetic_keys(patient, matched)
        db.update_user(patient["discord_id"], wolf_id=patient["id"], genetic_conditions=new_genetics)
        names = ", ".join(m.replace("_", " ").title() for m in matched)
        msg = f"**{name}**{form_tag}{target_note} eased **{names}**."
    elif outcome == "stabilized":
        db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], hp=1, condition="stable")
        msg = f"**{name}**{form_tag}{target_note} stabilized at 1 HP."
    elif outcome == "healed" or herb_key == "comfrey":
        lo, hi = heal_amount_for_form(form, complex_wound=complex_wound)
        heal = max(1, int(random.randint(lo, hi) * (int(stack["potency"]) / 100.0)))
        heal += trait_treat_heal_bonus(healer)
        cap = effective_max_hp(patient)
        new_hp = min(cap, int(patient["hp"]) + heal)
        db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], hp=new_hp)
        msg = f"**{name}**{form_tag}{target_note} healed **{heal} HP**."
        if trait_clears_infection_on_heal(healer) and "infected_wound" in injuries:
            injuries.remove("infected_wound")
            db.clear_injury_since(patient["id"], "infected_wound")
            db.set_user_conditions(
                patient["discord_id"],
                wolf_id=patient["id"],
                active_injuries=json.dumps(injuries),
                condition="healthy" if not injuries else patient["condition"],
            )
            msg += " Infection drawn out overnight."
    elif outcome == "symptom_ease":
        if meta.get("poison") and is_restricted_herb(herb_key) and not is_full_medic(healer):
            survived, poison_msg, _ = roll_poison_herb_misuse(patient, herb_key, day=day)
            return survived, prefix + poison_msg
        msg = f"**{name}**{form_tag}{target_note}; {meta.get('effect', 'symptoms ease')}."
    elif outcome == "poison_herb":
        if is_full_medic(healer):
            msg = f"**{name}**; restricted; Medic knowledge only."
        else:
            survived, poison_msg, _ = roll_poison_herb_misuse(patient, herb_key, day=day)
            return survived, prefix + poison_msg

    supplemental = apply_supplemental_herb(herb_key, patient, day=day, outcome=outcome)
    if supplemental:
        kind = supplemental["kind"]
        sfields = supplemental.get("fields") or {}
        if kind == "mercy":
            db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], condition="dead", hp=0)
            msg = f"**{name}**{form_tag}{target_note}; {supplemental['message']}"
        elif kind == "stabilize" and outcome != "stabilized":
            db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], hp=1, condition="stable")
            msg = f"**{name}**{form_tag}{target_note}; {supplemental['message']}"
        else:
            if sfields:
                db.update_user(patient["discord_id"], wolf_id=patient["id"], **sfields)
            extra = supplemental["message"]
            if not msg:
                msg = f"**{name}**{form_tag}{target_note}; {extra}"
            elif kind in ("disease_save_buff", "minor_relief", "heal", "symptom_relief", "infection_ward"):
                msg += f" {extra}"

    if not msg:
        msg = f"**{name}**{form_tag}{target_note}; {meta.get('effect', 'minor relief')}."
    return True, prefix + msg


def stabilize_bonus_from_stack(herb_key: str, form: str) -> int:
    """Public helper for cog stabilize paths using herb stacks."""
    from engine.death_saves import stabilize_bonus

    yarrow, yarrow_fresh, oak, cattail = _stabilize_stack_bonus(herb_key, form)
    return stabilize_bonus(
        yarrow=yarrow,
        yarrow_fresh=yarrow_fresh,
        oak_bark=oak,
        cattail=cattail,
    )
