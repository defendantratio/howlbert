"""Medic den checkup, observe, ritual, naming, lay to rest, swim therapy."""

from __future__ import annotations

import random

import database as db
from config import PUP_MAX_MOONS
from engine.conditions import medicine_check, parse_injuries
from engine.diseases import contagious_rate, disease_display, parse_disease
from engine.role_features import has_any_role, is_full_medic, wolf_role_key
from engine.sacred_visits import format_sacred_visit_reminder, sacred_visit_due
from engine.surgery import participant_has_herb
from herbs import HERBS

RITUAL_HERB_KEYS = frozenset({"douglas_sagewort", "lavender", "mountain_ash", "rowan"})
LAY_TO_REST_HERBS = frozenset({"rosemary", "lavender", "garden_mint", "watermint", "mint"})
BONE_REST_DAYS = 7
SWIM_REST_BONUS_HP = 2


def _herb_name(key: str) -> str:
    if key == "rowan":
        key = "mountain_ash"
    return HERBS.get(key, {}).get("name", key.replace("_", " ").title())


def run_medic_rounds(medic, *, day: int) -> tuple[bool, str]:
    """Den health scan for /medic action:checkup (full Medics only)."""
    if wolf_role_key(medic) != "medic":
        return (
            False,
            "only full **medics** may walk den checkups. "
            "apprentices observe cases with `/medic action:observe`.",
        )
    last = int(medic["last_medic_rounds_day"] if "last_medic_rounds_day" in medic.keys() else 0)
    if day > 0 and last >= day:
        return (
            False,
            "you already walked den checkups this sunrise. "
            "wait for the next `/rollover` (or ask an admin to call one).",
        )
    pack_id = medic["pack_id"] if "pack_id" in medic.keys() else None
    if not pack_id:
        return False, "join a pack to walk the sick den."
    wolves = db.get_pack_den_wolves(pack_id)
    if not wolves:
        return False, "the den is empty."

    contagious: list[str] = []
    bleeding: list[str] = []
    sacred_due: list[str] = []
    low_herbs: list[str] = []
    dying: list[str] = []
    bone_rest: list[str] = []
    mental: list[str] = []
    quarantined: list[str] = []

    from engine.quarantine import is_quarantined
    from engine.whispering_wild import format_mental_rounds_line

    for wolf in wolves:
        name = wolf["wolf_name"]
        if is_quarantined(wolf):
            ill = disease_display(wolf)
            label = ill[0] if ill else "isolated"
            quarantined.append(f"**{name}**: {label}")
        raw = wolf["disease"] if "disease" in wolf.keys() else None
        dkey, stage = parse_disease(raw)
        if dkey and contagious_rate(dkey) > 0:
            ill = disease_display(wolf)
            label = ill[0] if ill else dkey
            contagious.append(f"**{name}**: {label}")
        mind_line = format_mental_rounds_line(wolf)
        if mind_line:
            mental.append(mind_line)
        injuries = parse_injuries(wolf["active_injuries"] if "active_injuries" in wolf.keys() else None)
        if any(i in injuries for i in ("deep_gash", "infected_wound", "punctured_paw")):
            bleeding.append(f"**{name}**: bleeding risk")
        if is_full_medic(wolf) and sacred_visit_due(wolf, day):
            sacred_due.append(f"**{name}**: sacred visit due")
        inv_count = sum(
            int(row["quantity"])
            for row in db.get_inventory(wolf["discord_id"])
            if row["key"].startswith("herb_") or row["key"] == "stick"
        )
        if inv_count < 2:
            low_herbs.append(f"**{name}**: low herbs ({inv_count} in inventory)")
        cond = wolf["condition"] if "condition" in wolf.keys() else "healthy"
        if cond == "dying" or (int(wolf["hp"]) <= 0 and cond != "dead"):
            dying.append(f"**{name}**: **dying**")
        rest_until = int(wolf["bone_rest_until"] if "bone_rest_until" in wolf.keys() else 0)
        if rest_until > day:
            bone_rest.append(f"**{name}**: splint rest **{rest_until - day}** sunrise(s)")

    lines = [f"**den checkup**: **{len(wolves)}** wolves checked."]
    if dying:
        lines.append("\n**dying** (healer's code)\n" + "\n".join(dying))
    if contagious:
        lines.append("\n**contagious**\n" + "\n".join(contagious[:8]))
    if quarantined:
        lines.append(
            "\n**quarantined** (`/medic action:quarantine`)\n" + "\n".join(quarantined[:8])
        )
    if mental:
        lines.append("\n**mind & spirit**\n" + "\n".join(mental[:8]))
    if bleeding:
        lines.append("\n**bleeding / open wounds**\n" + "\n".join(bleeding[:8]))
    if bone_rest:
        lines.append("\n**splint confinement**\n" + "\n".join(bone_rest[:8]))
    if sacred_due:
        lines.append("\n**sacred visit due**\n" + "\n".join(sacred_due))
    if low_herbs:
        lines.append("\n**low herb warning**\n" + "\n".join(low_herbs))

    from engine.restricted_herbs import medic_rounds_scan_hoarders

    hoard_caught, hoard_suspicious = medic_rounds_scan_hoarders(pack_id)
    if hoard_caught:
        lines.append(
            "\n**poison herb hoarders caught**\n"
            + "\n".join(f"**{row['wolf_name']}**: {row['note']}" for row in hoard_caught[:6])
        )
    if hoard_suspicious:
        lines.append(
            "\n**suspicious scent (not proven)**\n" + "\n".join(hoard_suspicious[:6])
        )

    if len(lines) == 1:
        lines.append("\n_den is quiet; no urgent cases._")

    db.update_user_by_id(medic["id"], last_medic_rounds_day=day)
    return True, "\n".join(lines)


def run_observe_apprentice(
    medic, patient, *, day: int, guild_id: int | None = None
) -> tuple[bool, str]:
    """Apprentice RP observation; quest progress, no surgery cooldown."""
    if not has_any_role(medic, "medic_apprentice") and not is_full_medic(medic):
        return False, "only **medics** and **medic apprentices** may observe surgery."
    if medic["id"] == patient["id"]:
        return False, "observe another wolf's case; not your own."
    if guild_id:
        from engine.medical_access import can_medic_treat_cross_pack

        ok_cross, cross_msg = can_medic_treat_cross_pack(
            medic, patient, guild_id, emergency_stabilize=False
        )
        if not ok_cross:
            return False, cross_msg
    last = int(medic["last_observe_day"] if "last_observe_day" in medic.keys() else 0)
    if last >= day:
        return False, "you already observed a case this sunrise."
    injuries = parse_injuries(patient["active_injuries"] if "active_injuries" in patient.keys() else None)
    ill = disease_display(patient)
    focus = ill[0] if ill else (_injury_label(injuries) if injuries else "general wellness")
    db.update_user_by_id(medic["id"], last_observe_day=day)
    role_note = (
        "_apprentice paws; watch and learn before you hold the stick._"
        if has_any_role(medic, "medic_apprentice") and not is_full_medic(medic)
        else "_senior medic oversees the teaching den._"
    )
    return True, (
        f"**{medic['wolf_name']}** watches **{patient['wolf_name']}**'s **{focus}** case.\n"
        f"{role_note}\n"
        "_No surgery performed; cooldown untouched._"
    )


def _injury_label(injuries: list[str]) -> str:
    from herbs import INJURIES

    if not injuries:
        return "general wellness"
    info = INJURIES.get(injuries[0], {})
    return info.get("name", injuries[0])


def run_spirit_ritual(
    medic, patient, herb_key: str, *, day: int, guild_id: int | None = None
) -> tuple[bool, str]:
    """Douglas sagewort / lavender / rowan for shock_emotional or spirit cleanse."""
    if not is_medic(medic) and not has_any_role(medic, "medic_apprentice"):
        return False, "only **medics** lead cleansing rituals."
    if guild_id and medic["id"] != patient["id"]:
        from engine.medical_access import can_medic_treat_cross_pack

        ok_cross, cross_msg = can_medic_treat_cross_pack(
            medic, patient, guild_id, emergency_stabilize=False
        )
        if not ok_cross:
            return False, cross_msg
    key = herb_key.strip().lower()
    if key == "rowan":
        key = "mountain_ash"
    if key not in RITUAL_HERB_KEYS - {"rowan"}:
        allowed = ", ".join(_herb_name(k) for k in sorted(RITUAL_HERB_KEYS - {"rowan"}))
        return False, f"use **douglas_sagewort**, **lavender**, or **mountain_ash** (rowan). ({allowed})"
    if not participant_has_herb(medic, key):
        return False, f"no **{_herb_name(key)}** in your herb bag or inventory."

    from engine.surgery import consume_participant_herb

    consume_participant_herb(medic, key)
    dkey, stage = parse_disease(patient["disease"] if "disease" in patient.keys() else None)
    check = medicine_check(medic, dc=15)
    lines = [
        f"**cleansing ritual**: {_herb_name(key)} smoke over **{patient['wolf_name']}**",
        f"herblore: **{check['total']}** vs dc **15**",
    ]
    if not check["success"]:
        from engine.supernatural import apply_spirit_curse

        apply_spirit_curse(patient["id"], source="botched cleansing smoke")
        return False, "\n".join(lines + ["_smoke wrong; curse scent clings._"])

    from engine.supernatural import lift_spirit_curse

    if lift_spirit_curse(patient["id"]):
        lines.append("_spirit curse broken; the den breathes easier._")

    if dkey == "shock_emotional":
        db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], clear_disease=True, condition="healthy")
        db.adjust_mood(patient["id"], 10)
        lines.append("_emotional shock eases; breath returns to the den._")
    else:
        db.adjust_mood(patient["id"], 6)
        db.update_user_by_id(patient["id"], distressed=0)
        lines.append("_spirit weight lifts; `/skills category:spiritual check:spirit_cleanse` fulfilled in ritual._")
    return True, "\n".join(lines)


def run_naming_ceremony(medic, pup, *, day: int) -> tuple[bool, str]:
    """naming at sacred visit site (~3 weeks / under 1 moon)."""
    if not is_full_medic(medic):
        return False, "only a full **medic** may name pups at the sacred place."
    age = int(pup["age_months"] if "age_months" in pup.keys() else 99)
    if age > 1 or age >= PUP_MAX_MOONS:
        return False, (
            f"**{pup['wolf_name']}** is too old for the naming rite "
            f"(pups ~3 weeks / under **1** moon only)."
        )
    named = int(pup["naming_ceremony_day"] if "naming_ceremony_day" in pup.keys() else 0)
    if named > 0:
        return False, f"**{pup['wolf_name']}** already received a naming blessing."
    db.update_user_by_id(pup["id"], naming_ceremony_day=day)
    from engine.sacred_visits import apply_sacred_visit_blessings

    blessings, blessed = apply_sacred_visit_blessings(medic, day=day)
    bless_note = ""
    if blessed:
        bless_note = f"\n\n**blessings:** {' · '.join(blessings)}"
    elif int(medic["last_sacred_day"] if "last_sacred_day" in medic.keys() else 0) >= day:
        bless_note = "\n\n_half-moon sacred visit already recorded this sunrise._"
    return True, (
        f"at the **sacred place**, **{medic['wolf_name']}** speaks **{pup['wolf_name']}** "
        "into the ancestors' hearing; eyes open, name bound to the pack."
        f"{bless_note}"
    )


def run_lay_to_rest(medic, deceased, herb_key: str, *, day: int) -> tuple[bool, str]:
    """Prepare the dead with rosemary / lavender / mint."""
    if not is_medic(medic) and not has_any_role(medic, "medic_apprentice"):
        return False, "only **medics** prepare the dead."
    cond = deceased["condition"] if "condition" in deceased.keys() else "healthy"
    if cond != "dead":
        return False, f"**{deceased['wolf_name']}** is not among the dead."
    key = herb_key.strip().lower()
    if key == "mint":
        key = "garden_mint"
    if key not in LAY_TO_REST_HERBS:
        return False, "use **rosemary**, **lavender**, or **mint** (garden_mint / watermint)."
    if not participant_has_herb(medic, key):
        return False, f"no **{_herb_name(key)}** in your herb bag or inventory."
    from engine.surgery import consume_participant_herb

    consume_participant_herb(medic, key)
    return True, (
        f"**{medic['wolf_name']}** lays **{_herb_name(key)}** over **{deceased['wolf_name']}**; "
        "death-scent masked, paws ready for the silent path.\n"
        "_Consumable herbs spent in the rite. Bonded mates may need chamomile or borage._"
    )


def run_swim_therapy(user, *, day: int, season: str) -> tuple[bool, str]:
    """River territory swim; recovery bonus for sprain / bone rest."""
    if season == "winter":
        return False, "the river is ice-bound in **leaf-bare**; no swim therapy."
    last = int(user["last_swim_day"] if "last_swim_day" in user.keys() else 0)
    if last >= day:
        return False, "you already swam the healing pool this sunrise."
    injuries = parse_injuries(user["active_injuries"] if "active_injuries" in user.keys() else None)
    rest_until = int(user["bone_rest_until"] if "bone_rest_until" in user.keys() else 0)
    eligible = bool(injuries & {"sprained_leg", "fractured_rib", "punctured_paw"}) or rest_until > day
    if not eligible:
        return False, (
            "swim therapy helps **sprains**, **fractured ribs**, or wolves in **splint confinement** "
            "after bone-setting."
        )
    bonus = SWIM_REST_BONUS_HP
    if rest_until > day:
        bonus += 1
    new_hp = min(int(user["max_hp"]), int(user["hp"]) + bonus)
    db.set_user_conditions(user["discord_id"], wolf_id=user["id"], hp=new_hp)
    db.update_user_by_id(user["id"], last_swim_day=day)
    if rest_until > day and random.random() < 0.35:
        db.update_user_by_id(user["id"], bone_rest_until=max(day, rest_until - 1))
        shorten = "\n_Cold water eases the splint; **1** sunrise less confinement._"
    else:
        shorten = ""
    return True, (
        f"**{user['wolf_name']}** swims the pack river shallows; muscles loosen, pain fades "
        f"(**+{bonus} hp**, now **{new_hp}/{user['max_hp']}**).{shorten}"
    )


def apply_bone_rest(patient_id: int, *, day: int, days: int = BONE_REST_DAYS) -> None:
    db.update_user_by_id(patient_id, bone_rest_until=day + days)
