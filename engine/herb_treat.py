# herb_treat.py
"""treat from prepared herb inventory."""

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
    apply_cough_dose,
    apply_supplemental_herb,
    grant_disease_save_advantage,
)
from engine.herb_properties import can_use_form, herb_form_rule
from engine.medical_access import can_medic_treat_cross_pack
from engine.character_traits import trait_clears_infection_on_heal, trait_treat_heal_bonus
from engine.role_features import is_full_medic
from herbs import HERBS
from engine.diseases import parse_disease
from engine.herb_admin import DEFAULT_METHOD_REQS


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
    """check if a fresh herb is toxic and apply effects."""
    rule = herb_form_rule(herb_key)
    if form != "fresh" or not rule.toxic_if_fresh:
        return True, ""
    profs = parse_proficiencies(user["skill_proficiencies"])
    result = resolve_check(
        user,
        attr_keys=("attr_con",),
        skill="survival",
        dc=rule.toxic_dc,
        proficient="survival" in profs or "herblore" in profs,
        skill_key="survival",
        game_day=day,
    )
    if result["success"]:
        return True, format_roll_result(result) + "\n_you spit out the worst of it in time._"
    dmg = _roll_toxic_damage(rule)
    new_hp = max(0, int(user["hp"]) - dmg)
    db.set_user_conditions(user["discord_id"], hp=new_hp)
    return (
        False,
        format_roll_result(result)
        + f"\n**toxic fresh plant**; **-{dmg} hp**. {rule.notes}",
    )


def heal_amount_for_form(form: str, *, complex_wound: bool) -> tuple[int, int]:
    """return (min_heal, max_heal) based on preparation form."""
    if form in ("poultice", "ointment", "sap"):
        return (1, 4)
    if form in ("juice",):
        return (1, 3)
    if form in ("tea", "raw", "cooked", "simmered_milk", "sweetened", "gargle", "rub"):
        return (1, 2)
    if complex_wound:
        return (1, 2)
    return (1, 4)


def _stabilize_bonus(herb_key: str, form: str) -> tuple[bool, bool, bool, bool]:
    """return (yarrow, yarrow_fresh, oak_bark, cattail) flags for stabilize_check."""
    yarrow = herb_key == "yarrow"
    yarrow_fresh = yarrow and form == "fresh"
    oak = herb_key == "oak_bark"
    cattail = herb_key == "cattail"
    return yarrow, yarrow_fresh, oak, cattail


def _get_prepared_herb_from_inventory(user, herb_key: str, required_form: str | None = None):
    """find a prepared herb in inventory matching the herb_key and optionally required form."""
    rows = db.get_inventory_for_wolf(user["id"])
    for row in rows:
        if not row["key"].startswith("herb_"):
            continue
        key = row["key"].replace("herb_", "", 1)
        # check if it matches the herb_key and has the right form suffix
        if required_form:
            if key == f"{herb_key}_{required_form}":
                return row
        else:
            # any prepared form is fine
            if key == herb_key or key.startswith(f"{herb_key}_"):
                return row
    return None


def _consume_inventory_herb(user, item_id: int, quantity: int = 1) -> bool:
    """consume an herb from inventory."""
    return db.consume_item_for_wolf(user["id"], item_id, quantity=quantity)


def treat_from_herb_stack(
    healer,
    stack_id: int,
    *,
    day: int,
    patient=None,
    guild_id: int | None = None,
) -> tuple[bool, str]:
    """
    apply herb treatment from inventory (legacy stack_id support for backwards compat).
    defaults to self-treat when patient is omitted.
    """
    # NOTE: stack_id is now used to look up the herb from inventory
    # we treat it as the item id or key
    patient = patient or healer
    cond = patient["condition"] if "condition" in patient.keys() else "healthy"
    emergency = cond in ("dying",) or int(patient["hp"]) <= 0

    if guild_id and healer["id"] != patient["id"]:
        ok, reason = can_medic_treat_cross_pack(
            healer, patient, guild_id, emergency_stabilize=emergency
        )
        if not ok:
            return False, reason

    # get the herb from inventory using the stack_id as an item id or fallback to key
    herb_item = None
    herb_key = None
    form = None

    # try using stack_id as item id first
    item = db.get_item_by_id(stack_id) if stack_id else None
    if item and item["key"].startswith("herb_"):
        herb_item = item
        herb_key = item["key"].replace("herb_", "", 1)
        # parse form from key if present
        if "_" in herb_key:
            parts = herb_key.split("_")
            herb_key = parts[0]
            form = "_".join(parts[1:])
        else:
            form = "dried"

    # if not found, try as herb_key string
    if not herb_item:
        # try to find the herb in inventory
        rows = db.get_inventory_for_wolf(healer["id"])
        for row in rows:
            if not row["key"].startswith("herb_"):
                continue
            key = row["key"].replace("herb_", "", 1)
            if key == str(stack_id) or key.startswith(f"{stack_id}_"):
                herb_item = row
                herb_key = stack_id
                if "_" in key:
                    form = key.split("_", 1)[1]
                else:
                    form = "dried"
                break

    if not herb_item:
        return False, "that herb isn't in your inventory. use `/bones action:inventory` to see your herbs."

    # check quantity
    qty = db.get_inventory_quantity_for_wolf(healer["id"], herb_item["id"])
    if qty < 1:
        return False, f"you don't have **{herb_item['name']}** in your inventory."

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
        _consume_inventory_herb(healer, herb_item["id"])
        return False, toxic_msg

    from engine.long_term_injuries import CURE_HERBS, try_cure_long_term

    if herb_key in CURE_HERBS:
        cured, cure_msg = try_cure_long_term(herb_key, patient)
        if cured:
            _consume_inventory_herb(healer, herb_item["id"])
            prefix = (toxic_msg + "\n\n") if toxic_msg else ""
            if standing_note:
                prefix = standing_note + prefix
            return True, prefix + cure_msg

    if is_restricted_herb(herb_key) and not is_full_medic(healer):
        _consume_inventory_herb(healer, herb_item["id"])
        survived, poison_msg, _ = roll_poison_herb_misuse(patient, herb_key, day=day)
        return survived, standing_note + poison_msg

    # ---- preparation requirement check ----
    target_disease_raw = patient.get("disease", "")
    disease_key, stage = parse_disease(target_disease_raw)

    if disease_key:
        method_reqs = meta.get("method_requirements", {})
        required_method = method_reqs.get(disease_key)
        if required_method is None:
            required_method = DEFAULT_METHOD_REQS.get(disease_key)

        if required_method and required_method in ("poultice", "tea", "ointment"):
            # check if the herb is in the correct form
            if form != required_method:
                return False, (
                    f"**{name}** must be prepared as **{required_method}** to treat **{disease_key}**.\n"
                    f"use `/herbs action:prepare herb:herb_{herb_key} method:{required_method}` first.\n"
                    f"_(your {form} is not strong enough for this illness.)_"
                )

    outcome = treat_with_herb(patient, herb_key, meta)
    special = herb_special_effect(herb_key, patient)

    if outcome == "cough_dose":
        stage_cured, dose_fields, dose_msg = apply_cough_dose(patient, herb_key, day=day)
        _consume_inventory_herb(healer, herb_item["id"])
        prefix = (toxic_msg + "\n\n") if toxic_msg else ""
        if dose_fields:
            db.update_user(patient["discord_id"], wolf_id=patient["id"], **dose_fields)
        if stage_cured:
            db.set_user_conditions(
                patient["discord_id"], wolf_id=patient["id"], clear_disease=True, condition="healthy"
            )
            return True, prefix + f"**{name}**; {dose_msg} cough cleared."
        return True, prefix + f"**{name}**; {dose_msg}"

    if outcome == "no_effect" and not special and herb_key not in ("comfrey", "cobwebs"):
        check = medicine_check(healer, dc=15)
        from engine.herb_buffs import consume_herb_check_buffs

        consume_fields = consume_herb_check_buffs(healer, skill_key="medicine")
        if consume_fields:
            db.update_user(healer["discord_id"], wolf_id=healer["id"], **consume_fields)
        if not check["success"] and not is_full_medic(healer):
            return False, f"medicine check: {check['total']} vs dc 15: no effect."

    _consume_inventory_herb(healer, herb_item["id"])
    prefix = (toxic_msg + "\n\n") if toxic_msg else ""
    if standing_note:
        prefix = standing_note + prefix
    injuries = parse_injuries(patient["active_injuries"] if "active_injuries" in patient.keys() else None)
    form_tag = f" ({form})" if form not in ("fresh", "dried") else ""
    msg = ""
    target_note = ""
    if healer["id"] != patient["id"]:
        target_note = f" on **{patient['wolf_name']}**"

    if special == "reduce_exhaustion":
        old_ex = int(patient["exhaustion"])
        new_ex = max(0, old_ex - 1)
        db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], exhaustion=new_ex)
        msg = f"**{name}**{form_tag}{target_note}; exhaustion **{old_ex}** -> **{new_ex}**."
    elif special == "feed_pup_honey":
        from config import HONEY_PUP_HUNGER_BONUS
        from engine.nursing import apply_honey_to_pup

        fields = apply_honey_to_pup(patient, day_number=day)
        db.update_user(patient["discord_id"], wolf_id=patient["id"], **fields)
        ex_note = ""
        if "exhaustion" in fields:
            ex_note = f" exhaustion **-> {fields['exhaustion']}**."
        msg = (
            f"**{name}**{form_tag}{target_note}; warm sweetness (**+{HONEY_PUP_HUNGER_BONUS}** hunger)."
            f"{ex_note}"
        )
    elif special == "honey_pup_not_depleted":
        return False, "honey feeds starving pups; hunger or hydration must be low first."
    elif outcome == "cured_disease":
        db.set_user_conditions(
            patient["discord_id"], wolf_id=patient["id"], clear_disease=True, condition="healthy"
        )
        msg = f"**{name}**{form_tag}{target_note} cured the disease."
    elif outcome == "rabies_ease":
        db.update_user(patient["discord_id"], wolf_id=patient["id"], **grant_disease_save_advantage(patient))
        msg = (
            f"**{name}**{form_tag}{target_note}; herbs slow early cloudmouth; **advantage** on next disease save "
            "(one sunrise). cloudmouth is not cured."
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
        tea_wash = " hot tea wash burns the wound clean." if form == "tea" else ""
        msg = f"**{name}**{form_tag}{target_note} treated the injury.{tea_wash}"
    elif outcome == "cured_genetic":
        from engine.genetics import genetic_keys_matching_cures, remove_genetic_keys

        matched = genetic_keys_matching_cures(patient, meta.get("cures", ()))
        new_genetics = remove_genetic_keys(patient, matched)
        db.update_user(patient["discord_id"], wolf_id=patient["id"], genetic_conditions=new_genetics)
        names = ", ".join(m.replace("_", " ").title() for m in matched)
        msg = f"**{name}**{form_tag}{target_note} eased **{names}**."
    elif outcome == "stabilized":
        db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], hp=1, condition="stable")
        msg = f"**{name}**{form_tag}{target_note} stabilized at 1 hp."
    elif outcome == "healed" or herb_key == "comfrey":
        lo, hi = heal_amount_for_form(form, complex_wound=complex_wound)
        # potency from the herb item (we don't track potency in inventory directly,
        # but we can use a default or check herb_stacks for a matching record)
        potency = 100
        stacks = db.get_herb_stacks(patient["id"])
        for s in stacks:
            if s["herb_key"] == herb_key and s["form"] == form:
                potency = int(s["potency"])
                break
        heal = max(1, int(random.randint(lo, hi) * (potency / 100.0)))
        heal += trait_treat_heal_bonus(healer)
        if guild_id:
            from engine.plot_blinking import plot_healer_heal_bonus

            heal += plot_healer_heal_bonus(healer, patient, guild_id)
        cap = effective_max_hp(patient)
        new_hp = min(cap, int(patient["hp"]) + heal)
        db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], hp=new_hp)
        msg = f"**{name}**{form_tag}{target_note} healed **{heal} hp**."
        if trait_clears_infection_on_heal(healer) and "infected_wound" in injuries:
            injuries.remove("infected_wound")
            db.clear_injury_since(patient["id"], "infected_wound")
            db.set_user_conditions(
                patient["discord_id"],
                wolf_id=patient["id"],
                active_injuries=json.dumps(injuries),
                condition="healthy" if not injuries else patient["condition"],
            )
            msg += " infection drawn out overnight."
    elif outcome == "symptom_ease":
        if meta.get("poison") and is_restricted_herb(herb_key) and not is_full_medic(healer):
            survived, poison_msg, _ = roll_poison_herb_misuse(patient, herb_key, day=day)
            return survived, prefix + poison_msg
        msg = f"**{name}**{form_tag}{target_note}; {meta.get('effect', 'symptoms ease')}."
    elif outcome == "poison_herb":
        if is_full_medic(healer):
            msg = f"**{name}**; restricted; medic knowledge only."
        else:
            survived, poison_msg, _ = roll_poison_herb_misuse(patient, herb_key, day=day)
            return survived, prefix + poison_msg

    supplemental = apply_supplemental_herb(herb_key, patient, day=day, outcome=outcome)
    if supplemental:
        kind = supplemental["kind"]
        sfields = supplemental.get("fields") or {}
        if kind == "mercy":
            db.set_user_conditions(
                patient["discord_id"],
                wolf_id=patient["id"],
                condition="dead",
                hp=0,
                death_cause=f"mercy ({name})",
            )
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
    from engine.herb_side_effects import roll_herb_side_effects
    fresh_patient = db.get_user_by_id(patient["id"]) or patient
    side_note = roll_herb_side_effects(fresh_patient, herb_key, form, day=day)
    from engine.herb_benefits import roll_herb_benefits
    fresh_patient2 = db.get_user_by_id(patient["id"]) or fresh_patient
    benefit_note = roll_herb_benefits(fresh_patient2, herb_key, form, day=day)
    from engine.herb_addiction import register_herb_dose
    addiction_note = register_herb_dose(fresh_patient, herb_key, day=day)
    return True, prefix + msg + side_note + benefit_note + addiction_note


def stabilize_bonus_from_stack(herb_key: str, form: str) -> int:
    """public helper for stabilize paths using herbs."""
    from engine.death_saves import stabilize_bonus

    yarrow, yarrow_fresh, oak, cattail = _stabilize_bonus(herb_key, form)
    return stabilize_bonus(
        yarrow=yarrow,
        yarrow_fresh=yarrow_fresh,
        oak_bark=oak,
        cattail=cattail,
    )