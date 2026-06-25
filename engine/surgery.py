"""Medic surgery: stitch, set bone, extract, amputate."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass

import database as db
from engine.conditions import medicine_check, parse_injuries
from engine.dice import format_roll_result
from engine.role_features import has_any_role, is_full_medic
from herbs import INJURIES, herb_inventory_key

REALISM_NOTE = (
    "_A Note on Realism: While we use real plants and their properties for inspiration, "
    "wolves can't perform complex surgery, set complex broken bones, or cure every ailment. "
    "This guide is designed to enhance storytelling, offering a grounded and believable "
    "framework for the struggles and triumphs of a pack's Healer._"
)

# Optional herbs when the surgeon passes explicit /medic flags (herb → (bonus, flavor))
OPTIONAL_SURGERY_HERBS: dict[str, dict[str, tuple[int, str]]] = {
    "stitch": {
        "purple_loosestrife": (1, "_Purple loosestrife staunches the wound (+1)._"),
        "meadowsweet": (1, "_Meadowsweet dulls the pain (+1)._"),
    },
    "set_bone": {
        "rush_stalks": (2, "_Rush stalks lash the splint tight (+2)._"),
        "meadowsweet": (1, "_Meadowsweet eases the setting (+1)._"),
    },
    "extract": {
        "plantain": (1, "_Plantain soothes the paw as you work (+1)._"),
    },
    "amputate": {
        "meadowsweet": (1, "_Meadowsweet dulls the worst of it (+1)._"),
    },
}


@dataclass(frozen=True)
class SurgeryProcedure:
    key: str
    label: str
    dc: int
    injury_keys: tuple[str, ...]
    herbs: tuple[str, ...]
    optional_herbs: tuple[str, ...] = ()
    stick_count: int = 0
    success: str = ""
    failure: str = ""
    crit_fail: str = ""
    heal_dice: tuple[int, int] | None = None
    clear_injuries: tuple[str, ...] = ()
    fail_long_term: str | None = None
    success_long_term: str | None = None


SURGERY_PROCEDURES: dict[str, SurgeryProcedure] = {
    "stitch": SurgeryProcedure(
        key="stitch",
        label="Stitch wound",
        dc=15,
        injury_keys=("deep_gash", "infected_wound"),
        herbs=("cobwebs", "yarrow"),
        stick_count=1,
        success="Needlework holds; the bleeding stops.",
        failure="The stitches pull free; blood runs again.",
        crit_fail="The wound turns foul; **infected_wound** if not already present.",
        heal_dice=(1, 4),
        clear_injuries=("deep_gash", "infected_wound"),
    ),
    "set_bone": SurgeryProcedure(
        key="set_bone",
        label="Set bone / splint",
        dc=20,
        injury_keys=("fractured_rib", "sprained_leg", "broken_jaw", "spinal_injury"),
        herbs=("comfrey", "bindweed", "stick"),
        stick_count=2,
        success="Bone aligned; sticks and bindweed hold the splint. Rest and herbs do the rest.",
        failure="The splint slips before it sets; the break still grinds.",
        crit_fail="The bone sets crooked; the patient may never run straight again.",
        clear_injuries=("fractured_rib", "sprained_leg", "broken_jaw", "spinal_injury"),
        fail_long_term="limp",
    ),
    "extract": SurgeryProcedure(
        key="extract",
        label="Extract deep thorn or splinter",
        dc=12,
        injury_keys=("punctured_paw",),
        herbs=("yarrow",),
        optional_herbs=("comfrey", "plantain"),
        success="The splinter comes free; the paw can heal.",
        failure="The thorn slides deeper; infection may follow by next sunrise.",
        crit_fail="Pus and heat spread through the pad; **infected_wound**.",
        clear_injuries=("punctured_paw",),
    ),
    "amputate": SurgeryProcedure(
        key="amputate",
        label="Amputate ruined limb",
        dc=18,
        injury_keys=("infected_wound", "sprained_leg", "punctured_paw"),
        herbs=("yarrow",),
        optional_herbs=("poppy_seeds",),
        stick_count=1,
        success="The ruined limb is taken; the patient lives with a stark scar.",
        failure="Shock on the table; the patient falters.",
        crit_fail="The patient collapses into **shock (physical)**.",
        heal_dice=(0, 0),
        clear_injuries=("infected_wound", "sprained_leg", "punctured_paw"),
        success_long_term="scarring",
    ),
}


def surgery_dc_for_surgeon(surgeon, base_dc: int) -> int:
    if is_full_medic(surgeon):
        return base_dc
    if has_any_role(surgeon, "medic_apprentice"):
        return base_dc + 2
    return base_dc + 5


def _herb_label(herb_key: str) -> str:
    from herbs import HERBS

    return HERBS.get(herb_key, {}).get("name", herb_key.replace("_", " ").title())


def participant_has_herb(user, herb_key: str) -> bool:
    for stack in db.get_herb_stacks(user["id"]):
        if stack["herb_key"] == herb_key:
            return True
    item = db.get_item_by_key(herb_inventory_key(herb_key))
    if item and db.get_inventory_quantity(user["discord_id"], item["id"]) > 0:
        return True
    return False


def consume_participant_herb(user, herb_key: str) -> bool:
    for stack in db.get_herb_stacks(user["id"]):
        if stack["herb_key"] == herb_key:
            db.remove_herb_stack(stack["id"])
            return True
    item = db.get_item_by_key(herb_inventory_key(herb_key))
    if item and db.get_inventory_quantity(user["discord_id"], item["id"]) > 0:
        db.consume_item(user["discord_id"], item["id"], quantity=1)
        return True
    return False


# Back-compat aliases
surgeon_has_herb = participant_has_herb
consume_surgeon_herb = consume_participant_herb


def _stick_count(user) -> int:
    count = sum(1 for stack in db.get_herb_stacks(user["id"]) if stack["herb_key"] == "stick")
    item = db.get_item_by_key(herb_inventory_key("stick"))
    if item:
        count += db.get_inventory_quantity(user["discord_id"], item["id"])
    return count


def _sticks_available(patient, surgeon) -> int:
    return _stick_count(patient) + _stick_count(surgeon)


def _patient_can_bite_stick(patient) -> bool:
    cond = patient["condition"] if "condition" in patient.keys() else "healthy"
    if cond in ("dying", "dead"):
        return False
    return int(patient["hp"]) > 0


def _consume_bite_stick(patient, surgeon) -> str:
    """Consume stick from patient first, then surgeon. Returns flavor line."""
    if consume_participant_herb(patient, "stick"):
        return f"**{patient['wolf_name']}** bites down hard on a stick."
    consume_participant_herb(surgeon, "stick")
    return f"A stick is placed between **{patient['wolf_name']}**'s jaws."


def _consume_splint_sticks(patient, surgeon, count: int) -> None:
    for _ in range(count):
        if not consume_participant_herb(surgeon, "stick"):
            consume_participant_herb(patient, "stick")


def missing_surgery_herbs(surgeon, patient, procedure: SurgeryProcedure) -> list[str]:
    missing: list[str] = []
    if procedure.stick_count and _sticks_available(patient, surgeon) < procedure.stick_count:
        missing.append("stick")
    for herb_key in procedure.herbs:
        if herb_key == "stick":
            continue
        if not participant_has_herb(surgeon, herb_key):
            missing.append(herb_key)
    return missing


def _validate_optional_herb_flags(
    surgeon,
    procedure_key: str,
    spec: SurgeryProcedure,
    *,
    use_poppy: bool,
    use_meadowsweet: bool,
    use_loosestrife: bool,
    use_plantain: bool,
    use_rush_stalks: bool = False,
) -> str | None:
    optional = OPTIONAL_SURGERY_HERBS.get(procedure_key, {})

    if use_loosestrife:
        if procedure_key != "stitch":
            return "**Purple loosestrife** is only used when stitching wounds."
        if not participant_has_herb(surgeon, "purple_loosestrife"):
            return "No **purple loosestrife** in your herb bag or inventory."

    if use_plantain:
        if procedure_key != "extract":
            return "**Plantain** is only used when extracting splinters."
        if not participant_has_herb(surgeon, "plantain"):
            return "No **plantain** in your herb bag or inventory."

    if use_meadowsweet:
        if "meadowsweet" not in optional:
            return f"**Meadowsweet** is not used for **{spec.label}**."
        if not participant_has_herb(surgeon, "meadowsweet"):
            return "No **meadowsweet** in your herb bag or inventory."

    if use_poppy and "poppy_seeds" in spec.optional_herbs:
        if not participant_has_herb(surgeon, "poppy_seeds"):
            return "No **poppy seeds** for sedation."

    if use_rush_stalks:
        if procedure_key != "set_bone":
            return "**Rush stalks** lash splints only during **set bone** surgery."
        if not participant_has_herb(surgeon, "rush_stalks"):
            return "No **rush stalks** in your herb bag or inventory."

    return None


def _apply_optional_surgery_herbs(
    surgeon,
    procedure_key: str,
    *,
    use_poppy: bool,
    use_meadowsweet: bool,
    use_loosestrife: bool,
    use_plantain: bool,
    use_rush_stalks: bool = False,
    spec: SurgeryProcedure,
) -> tuple[int, list[str]]:
    bonus = 0
    notes: list[str] = []
    optional = OPTIONAL_SURGERY_HERBS.get(procedure_key, {})

    if use_meadowsweet and "meadowsweet" in optional:
        herb_bonus, flavor = optional["meadowsweet"]
        consume_participant_herb(surgeon, "meadowsweet")
        bonus += herb_bonus
        notes.append(flavor)

    if use_loosestrife and procedure_key == "stitch" and "purple_loosestrife" in optional:
        herb_bonus, flavor = optional["purple_loosestrife"]
        consume_participant_herb(surgeon, "purple_loosestrife")
        bonus += herb_bonus
        notes.append(flavor)

    if use_plantain and procedure_key == "extract" and "plantain" in optional:
        herb_bonus, flavor = optional["plantain"]
        consume_participant_herb(surgeon, "plantain")
        bonus += herb_bonus
        notes.append(flavor)

    if use_poppy and "poppy_seeds" in spec.optional_herbs:
        consume_participant_herb(surgeon, "poppy_seeds")
        bonus += 2
        notes.append("_Poppy seeds sedate the patient (+2)._")

    if use_rush_stalks and procedure_key == "set_bone" and "rush_stalks" in optional:
        herb_bonus, flavor = optional["rush_stalks"]
        consume_participant_herb(surgeon, "rush_stalks")
        bonus += herb_bonus
        notes.append(flavor)

    return bonus, notes


def matching_injury(patient, procedure: SurgeryProcedure) -> str | None:
    injuries = parse_injuries(
        patient["active_injuries"] if "active_injuries" in patient.keys() else None
    )
    for key in procedure.injury_keys:
        if key in injuries:
            return key
    return None


def procedure_for_patient(patient, procedure_key: str) -> tuple[SurgeryProcedure | None, str | None]:
    spec = SURGERY_PROCEDURES.get(procedure_key)
    if not spec:
        return None, f"Unknown surgery **{procedure_key}**."
    injury = matching_injury(patient, spec)
    if not injury:
        names = ", ".join(INJURIES.get(k, {}).get("name", k) for k in spec.injury_keys)
        return None, f"**{patient['wolf_name']}** has no injury for **{spec.label}** ({names})."
    return spec, None


def _remove_injuries(patient_id: int, keys: tuple[str, ...]) -> None:
    patient = db.get_user_by_id(patient_id)
    if not patient:
        return
    injuries = parse_injuries(
        patient["active_injuries"] if "active_injuries" in patient.keys() else None
    )
    changed = False
    for key in keys:
        if key in injuries:
            injuries.remove(key)
            db.clear_injury_since(patient_id, key)
            changed = True
    if changed:
        db.update_user_by_id(patient_id, active_injuries=json.dumps(injuries))


def _add_injury(patient_id: int, key: str) -> None:
    patient = db.get_user_by_id(patient_id)
    if not patient:
        return
    injuries = parse_injuries(
        patient["active_injuries"] if "active_injuries" in patient.keys() else None
    )
    if key not in injuries:
        injuries.append(key)
        db.update_user_by_id(patient_id, active_injuries=json.dumps(injuries))


def run_surgery(
    surgeon,
    patient,
    procedure_key: str,
    *,
    day: int,
    use_poppy: bool = False,
    use_meadowsweet: bool = False,
    use_loosestrife: bool = False,
    use_plantain: bool = False,
    use_rush_stalks: bool = False,
    helper=None,
    guild_id: int | None = None,
) -> tuple[bool, str]:
    """
    Perform surgery on patient. Surgeon must be Medic (apprentice +2 DC).
    Returns (success, message body).
    """
    if not is_full_medic(surgeon) and not has_any_role(surgeon, "medic_apprentice"):
        return False, "Only **Medics** and **medic apprentices** may perform surgery."

    if surgeon["id"] == patient["id"]:
        return False, (
            "You cannot operate on yourself; another **Medic** must hold the stick "
            "and work the splint while you lie still."
        )

    if guild_id:
        from engine.medical_access import can_medic_treat_cross_pack

        ok_cross, cross_msg = can_medic_treat_cross_pack(
            surgeon, patient, guild_id, emergency_stabilize=False
        )
        if not ok_cross:
            return False, cross_msg

    spec, err = procedure_for_patient(patient, procedure_key)
    if err or not spec:
        return False, err or "Invalid procedure."

    last = int(surgeon["last_surgery_day"] if "last_surgery_day" in surgeon.keys() else 0)
    if last >= day:
        return False, "You already operated this sunrise."

    missing = missing_surgery_herbs(surgeon, patient, spec)
    if missing:
        labels = ", ".join(_herb_label(h) for h in missing)
        hint = ""
        if "stick" in missing:
            if spec.stick_count > 1:
                hint = (
                    f" (need **{spec.stick_count} sticks**: one to bite, one to lash the splint; "
                    "patient or Medic herb bag/inventory)"
                )
            else:
                hint = " (stick: patient or Medic herb bag/inventory)"
        return False, f"Missing supplies for **{spec.label}**: {labels}.{hint}"

    if spec.stick_count and not _patient_can_bite_stick(patient):
        return False, (
            f"**{patient['wolf_name']}** is too far gone to bite a stick; "
            "stabilize them first (`/medic action:stabilize`)."
        )

    flag_err = _validate_optional_herb_flags(
        surgeon,
        procedure_key,
        spec,
        use_poppy=use_poppy,
        use_meadowsweet=use_meadowsweet,
        use_loosestrife=use_loosestrife,
        use_plantain=use_plantain,
        use_rush_stalks=use_rush_stalks,
    )
    if flag_err:
        return False, flag_err

    assist_note = ""
    advantage = False
    dc = surgery_dc_for_surgeon(surgeon, spec.dc)
    if helper:
        if helper["id"] == surgeon["id"]:
            return False, "Pick another **Medic** as **helper**, not yourself."
        from engine.group_checks import run_assisted_check

        _, assist_body = run_assisted_check(
            surgeon,
            helper,
            dc=dc,
            attr_keys=("attr_wis",),
            skill_key="medicine",
            skill_label="Medicine",
            day=day,
        )
        assist_note = assist_body
        advantage = "Assisted; primary took the higher" in assist_body

    stick_notes: list[str] = []
    if spec.stick_count >= 1:
        stick_notes.append(_consume_bite_stick(patient, surgeon))
    splint_sticks = max(0, spec.stick_count - 1)
    if splint_sticks:
        _consume_splint_sticks(patient, surgeon, splint_sticks)

    for herb in spec.herbs:
        if herb == "stick":
            continue
        consume_participant_herb(surgeon, herb)

    herb_bonus, herb_notes = _apply_optional_surgery_herbs(
        surgeon,
        procedure_key,
        use_poppy=use_poppy,
        use_meadowsweet=use_meadowsweet,
        use_loosestrife=use_loosestrife,
        use_plantain=use_plantain,
        use_rush_stalks=use_rush_stalks,
        spec=spec,
    )

    if advantage:
        r1 = medicine_check(surgeon, dc=dc)
        r2 = medicine_check(surgeon, dc=dc)
        roll = r1 if r1["total"] >= r2["total"] else r2
    else:
        roll = medicine_check(surgeon, dc=dc)
    if herb_bonus:
        roll = dict(roll)
        roll["modifier"] = roll["modifier"] + herb_bonus
        roll["total"] = roll["die"] + roll["modifier"] + roll["proficiency"]
    die = roll["die"]
    success = die == 20 or (die != 1 and roll["total"] >= dc)
    roll = dict(roll)
    roll["success"] = success
    roll["dc"] = dc
    roll["outcome"] = "critical_failure" if die == 1 else ("critical_success" if die == 20 else ("success" if success else "failure"))
    roll["attr_label"] = "WIS"

    lines = [
        f"**{spec.label}** on **{patient['wolf_name']}**",
    ]
    if assist_note:
        lines.append(assist_note)
    lines.append(format_roll_result(roll))
    if not is_full_medic(surgeon) and has_any_role(surgeon, "medic_apprentice"):
        lines.insert(1, "_Apprentice paws; a full Medic should oversee this work._")
    lines.extend(stick_notes)
    if splint_sticks:
        lines.append("_Straight sticks align the break; bindweed will lash the splint._")
    lines.extend(herb_notes)

    die = roll["die"]
    patient_id = patient["id"]

    if die == 1:
        lines.append(spec.crit_fail or spec.failure)
        if spec.fail_long_term:
            from engine.long_term_injuries import add_long_term_injury

            add_long_term_injury(patient_id, spec.fail_long_term)
            lines.append(f"_Permanent mark: **{spec.fail_long_term}**._")
        if procedure_key == "extract":
            _add_injury(patient_id, "infected_wound")
        elif procedure_key == "stitch":
            injuries = parse_injuries(
                patient["active_injuries"] if "active_injuries" in patient.keys() else None
            )
            if "infected_wound" not in injuries:
                _add_injury(patient_id, "infected_wound")
        elif procedure_key == "amputate":
            db.update_user_by_id(patient_id, disease="shock_physical:active")
        lines.append(REALISM_NOTE)
        db.update_user_by_id(surgeon["id"], last_surgery_day=day)
        return False, "\n".join(lines)

    if success:
        injuries = parse_injuries(
            patient["active_injuries"] if "active_injuries" in patient.keys() else None
        )
        to_clear = [k for k in spec.clear_injuries if k in injuries]
        if to_clear:
            _remove_injuries(patient_id, tuple(to_clear))
        if spec.heal_dice and spec.heal_dice != (0, 0):
            from engine.exhaustion_effects import effective_max_hp

            heal = random.randint(*spec.heal_dice)
            fresh = db.get_user_by_id(patient_id)
            cap = effective_max_hp(fresh) if fresh else 10
            new_hp = min(cap, int(fresh["hp"]) + heal) if fresh else heal
            db.set_user_conditions(fresh["discord_id"], wolf_id=patient_id, hp=new_hp)
            lines.append(f"{spec.success} **+{heal} HP**.")
        else:
            lines.append(spec.success)
        if procedure_key == "set_bone":
            lines.append("_Splint lashed with bindweed; the patient keeps biting the stick._")
            from engine.medical_care import apply_bone_rest

            apply_bone_rest(patient_id, day=day)
            lines.append(
                f"_**Splint confinement**: den rest until sunrise **{day + 7}** "
                f"(`/medic action:swim` may shorten)._"
            )
        if spec.success_long_term:
            from engine.long_term_injuries import add_long_term_injury

            add_long_term_injury(patient_id, spec.success_long_term)
            lines.append("_Visible **scarring** from the amputation._")
        db.update_user_by_id(surgeon["id"], last_surgery_day=day)
        return True, "\n".join(lines)

    lines.append(spec.failure)
    if procedure_key == "stitch":
        dmg = random.randint(1, 4)
        fresh = db.get_user_by_id(patient_id)
        if fresh:
            new_hp = max(0, int(fresh["hp"]) - dmg)
            db.set_user_conditions(fresh["discord_id"], wolf_id=patient_id, hp=new_hp)
            lines.append(f"**−{dmg} HP**")
    elif procedure_key == "amputate":
        dmg = random.randint(1, 6)
        fresh = db.get_user_by_id(patient_id)
        if fresh:
            new_hp = max(0, int(fresh["hp"]) - dmg)
            db.set_user_conditions(fresh["discord_id"], wolf_id=patient_id, hp=new_hp)
            lines.append(f"**−{dmg} HP**")
    if procedure_key == "extract":
        if random.random() < 0.35:
            _add_injury(patient_id, "infected_wound")
            lines.append("_Infection takes hold._")
    lines.append(REALISM_NOTE)
    db.update_user_by_id(surgeon["id"], last_surgery_day=day)
    return False, "\n".join(lines)
