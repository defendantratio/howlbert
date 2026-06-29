"""Prone, disarm, pin, and attack-roll modifiers during combat."""

from __future__ import annotations

import json

from engine.combat_display import fighter_val
from engine.combat_guide import COMBAT_MANEUVERS
from engine.combat_size import can_pin_target, can_scruff_target
from engine.rolls import roll_d20
from engine.injury_effects import attack_roll_modifiers


def parse_combat_flags(fighter) -> dict:
    if not fighter or "combat_flags" not in fighter.keys():
        return {}
    raw = fighter["combat_flags"]
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def get_pinner_fighter_id(fighter) -> int | None:
    flags = parse_combat_flags(fighter)
    pinned_by = flags.get("pinned_by")
    return int(pinned_by) if pinned_by else None


def is_holding_pin(fighter_id: int, encounter_id: int) -> bool:
    import database as db

    for fighter in db.get_combat_fighters(encounter_id):
        flags = parse_combat_flags(fighter)
        if flags.get("pinned") and flags.get("pinned_by") == fighter_id:
            return True
    return False


def format_combat_flags(
    flags: dict,
    *,
    fighter_id: int | None = None,
    encounter_id: int | None = None,
) -> str:
    tags: list[str] = []
    if flags.get("pinned"):
        tags.append("pinned")
    if flags.get("prone"):
        tags.append("prone")
    if flags.get("disarmed"):
        tags.append("disarmed")
    if flags.get("obscured"):
        tags.append("hidden")
    if flags.get("attack_disadvantage"):
        tags.append("strained")
    if fighter_id and encounter_id and is_holding_pin(fighter_id, encounter_id):
        tags.append("pinning")
    return ", ".join(tags)


def set_fighter_pinned(fighter_id: int, pinner_fighter_id: int, encounter_id: int) -> None:
    import database as db

    for fighter in db.get_combat_fighters(encounter_id):
        flags = parse_combat_flags(fighter)
        if flags.get("pinned_by") == fighter_id:
            clear_fighter_pin(fighter["id"])
    db.update_fighter_combat_flags(
        fighter_id,
        pinned=True,
        pinned_by=pinner_fighter_id,
        prone=True,
    )


def clear_fighter_pin(fighter_id: int) -> None:
    import database as db

    db.update_fighter_combat_flags(fighter_id, pinned=False, pinned_by=None, prone=False)


def release_pin_states(fighter_id: int, encounter_id: int) -> None:
    """Clear pin on this fighter and on anyone they were pinning."""
    import database as db

    clear_fighter_pin(fighter_id)
    for fighter in db.get_combat_fighters(encounter_id):
        flags = parse_combat_flags(fighter)
        if flags.get("pinned") and flags.get("pinned_by") == fighter_id:
            clear_fighter_pin(fighter["id"])


def roll_attack_die(
    *,
    disadvantage: bool = False,
    advantage: bool = False,
) -> int:
    if disadvantage and advantage:
        return roll_d20()
    if disadvantage:
        return min(roll_d20(), roll_d20())
    if advantage:
        return max(roll_d20(), roll_d20())
    return roll_d20()


def attacker_roll_modifiers(
    attacker,
    attack_type: str,
    attacker_f,
    defender_f,
    *,
    encounter_id: int | None = None,
) -> tuple[bool, bool, str]:
    """Return (disadvantage, advantage, flavor_note) for the attack roll."""
    a_flags = parse_combat_flags(attacker_f)
    d_flags = parse_combat_flags(defender_f)
    disadvantage = False
    advantage = bool(d_flags.get("prone") or d_flags.get("pinned"))

    if d_flags.get("obscured"):
        disadvantage = True

    if encounter_id and attacker_f and defender_f:
        from engine.role_features import guard_imposes_attack_disadvantage

        if guard_imposes_attack_disadvantage(
            encounter_id, attacker_f["id"], defender_f["id"]
        ):
            disadvantage = True

    if a_flags.get("pinned"):
        disadvantage = True
    if a_flags.get("prone"):
        disadvantage = True
    if a_flags.get("attack_disadvantage"):
        disadvantage = True
    if a_flags.get("disarmed") and attack_type == "claw":
        disadvantage = True

    if attacker and "exhaustion" in attacker.keys():
        if int(attacker["exhaustion"]) >= 3:
            disadvantage = True

    hunger_note = ""
    if attacker:
        from config import HUNGER_LOW_THRESHOLD, THIRST_LOW_THRESHOLD

        hunger = int(attacker["hunger"]) if "hunger" in attacker.keys() else 100
        thirst = int(attacker["thirst"]) if "thirst" in attacker.keys() else 100
        if hunger < HUNGER_LOW_THRESHOLD or thirst < THIRST_LOW_THRESHOLD:
            disadvantage = True
            hunger_note = "running on empty; hunger/thirst cost you the edge (disadvantage)"

    _, bite_disadv = attack_roll_modifiers(attacker, attack_type)
    if bite_disadv:
        disadvantage = True

    from engine.disease_effects import disease_attack_disadvantage

    if attacker and disease_attack_disadvantage(attacker, attack_type):
        disadvantage = True

    from engine.reptile_fear import reptile_fear_roll_modifiers

    rf_dis, rf_adv, rf_note = reptile_fear_roll_modifiers(attacker_f, defender_f)
    if rf_dis:
        disadvantage = True
    if rf_adv:
        advantage = True

    return disadvantage, advantage, rf_note or hunger_note


def maneuver_pin_block(
    spec: dict,
    attacker_f,
    defender_f,
    *,
    defender_hp: int | None = None,
    defender_max_hp: int | None = None,
    attacker_stats=None,
    defender_stats=None,
) -> str | None:
    """Return a block reason when pin requirements aren't met."""
    name = spec["name"]
    a_flags = parse_combat_flags(attacker_f)
    d_flags = parse_combat_flags(defender_f)
    encounter_id = fighter_val(attacker_f, "encounter_id")

    if spec.get("requires_self_pinned") and not a_flags.get("pinned"):
        return f"**{name}** only works while you are **pinned**."
    if spec.get("requires_self_unpinned") and a_flags.get("pinned"):
        return f"you can't use **{name}** while **pinned**."
    if spec.get("requires_no_active_pin") and encounter_id and is_holding_pin(attacker_f["id"], encounter_id):
        return f"you can't use **{name}** while already **pinning** someone."
    if spec.get("target_must_be_pinner"):
        pinner_id = get_pinner_fighter_id(attacker_f)
        if not pinner_id or defender_f["id"] != pinner_id:
            return f"**{name}** must target the fighter pinning you."
    if d_flags.get("pinned") and spec.get("requires_target_unpinned"):
        return f"**{name}** can't land on a foe already **pinned**."
    if spec.get("applies_pin_on_hit") and attacker_stats and defender_stats:
        if not can_pin_target(attacker_stats, defender_stats):
            return (
                f"**{name}** can't hold down a foe that much larger; "
                "try **badger defence** or rake from below."
            )
    if spec.get("requires_smaller_target") and attacker_stats and defender_stats:
        if not can_scruff_target(attacker_stats, defender_stats):
            return f"**{name}** only works on a **smaller** opponent."
    min_pct = spec.get("min_defender_hp_pct")
    if min_pct is not None and defender_hp is not None and defender_max_hp:
        wounded = defender_hp <= defender_max_hp * min_pct
        if not d_flags.get("pinned") and not wounded:
            return (
                f"**{name}** needs a **pinned** or badly wounded foe "
                f"(below {int(min_pct * 100)}% hp)."
            )
    return None


def attack_target_block(
    attacker_f,
    defender_f,
    *,
    maneuver_key: str | None = None,
) -> str | None:
    """Realistic reach limits for bite/claw while pinned or holding a pin."""
    if maneuver_key:
        return None
    a_flags = parse_combat_flags(attacker_f)
    d_flags = parse_combat_flags(defender_f)
    encounter_id = fighter_val(attacker_f, "encounter_id")

    if a_flags.get("pinned"):
        pinner_id = get_pinner_fighter_id(attacker_f)
        if pinner_id and defender_f["id"] != pinner_id:
            return (
                "while **pinned**, you can only bite/claw your **pinner**; "
                "use an escape maneuver."
            )
    if encounter_id and is_holding_pin(attacker_f["id"], encounter_id):
        if not (d_flags.get("pinned") and d_flags.get("pinned_by") == attacker_f["id"]):
            return (
                "you're **pinning** a foe; only your pinned target is in reach "
                "for bite/claw."
            )
    return None


def apply_maneuver_pin_effects(
    attacker_f,
    defender_f,
    maneuver_key: str,
    *,
    hit: bool,
    defender_name: str,
    attacker_stats=None,
    defender_stats=None,
) -> str | None:
    if not hit or not maneuver_key or not attacker_f or not defender_f:
        return None
    spec = COMBAT_MANEUVERS.get(maneuver_key)
    if not spec:
        return None

    notes: list[str] = []
    if spec.get("applies_pin_on_hit") and fighter_val(defender_f, "id"):
        if attacker_stats and defender_stats and not can_pin_target(attacker_stats, defender_stats):
            notes.append(
                f"_you land on **{defender_name}**, but you're too light to force them **pinned**._"
            )
        else:
            encounter_id = int(fighter_val(defender_f, "encounter_id") or 0)
            set_fighter_pinned(defender_f["id"], attacker_f["id"], encounter_id)
            notes.append(f"**{defender_name}** is **pinned** on their back.")
    if spec.get("clears_self_pin_on_hit") and fighter_val(attacker_f, "id"):
        if parse_combat_flags(attacker_f).get("pinned"):
            clear_fighter_pin(attacker_f["id"])
            notes.append("You **break free** of the pin.")
    return "\n".join(notes) if notes else None


def apply_crit_status_effects(defender_fighter_id: int, crit_effect: int | None) -> str | None:
    if not crit_effect:
        return None
    import database as db

    if crit_effect == 2:
        db.update_fighter_combat_flags(defender_fighter_id, prone=True)
        return "**knocked prone.**"
    if crit_effect == 3:
        db.update_fighter_combat_flags(defender_fighter_id, disarmed=True)
        return "**disarmed**; grip lost."
    return None


def apply_fumble_status_effects(attacker_fighter_id: int, fumble_effect: int | None) -> str | None:
    if not fumble_effect:
        return None
    import database as db

    if fumble_effect == 2:
        db.update_fighter_combat_flags(attacker_fighter_id, attack_disadvantage=True)
        return "**strained muscle**; disadvantage on your next attack."
    if fumble_effect == 3:
        db.update_fighter_combat_flags(attacker_fighter_id, prone=True)
        return "**you stumble prone.**"
    return None


def clear_attack_disadvantage(fighter_id: int) -> None:
    import database as db

    db.update_fighter_combat_flags(fighter_id, attack_disadvantage=False)
