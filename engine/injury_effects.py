"""Mechanical effects of active injuries in combat and activities."""

from __future__ import annotations

from engine.character import attr_modifier, parse_proficiencies
from engine.conditions import parse_injuries
from herbs import INJURIES


def active_injury_keys(user) -> list[str]:
    raw = user["active_injuries"] if user and "active_injuries" in user.keys() else None
    return parse_injuries(raw)


def has_injury(user, key: str) -> bool:
    return key in active_injury_keys(user)


def bite_attack_blocked(user) -> bool:
    return has_injury(user, "broken_jaw")


def has_paralysis(user) -> bool:
    return has_injury(user, "spinal_injury") or has_injury(user, "paralyzed")


def hunt_blocked_by_injury(user) -> str | None:
    """Fractured ribs or paralysis rule out running, fighting prey, and long treks."""
    if has_injury(user, "paralyzed"):
        return (
            "**paralyzed**: the spine is severed. you cannot leave the den for field commands."
        )
    if has_injury(user, "spinal_injury"):
        return (
            "**spinal injury**: hindquarters won't obey. rest and splint before hunting, "
            "patrol, or ranging out."
        )
    if has_injury(user, "fractured_rib"):
        return (
            "a **fractured rib** keeps you from strenuous activity; "
            "rest and comfrey before hunting, tracking, or ranging out."
        )
    return None


def bone_rest_activity_block(user, *, day: int | None = None) -> str | None:
    rest_until = int(user["bone_rest_until"] if "bone_rest_until" in user.keys() else 0)
    if not rest_until or day is None:
        if rest_until and day is None:
            return (
                "**splint confinement**: bone rest after surgery. "
                "no hunt, patrol, or ranging until the medic clears you."
            )
        return None
    if rest_until > day:
        left = rest_until - day
        return (
            f"**splint confinement**: **{left}** sunrise(s) of bone rest. "
            "den activities only; `/medic action:swim` may ease recovery."
        )
    return None


# Alias for clarity at call sites
strenuous_activity_blocked_by_injury = hunt_blocked_by_injury


def meal_blocked_by_injury(user) -> str | None:
    if has_injury(user, "broken_jaw"):
        shield = int(user["jaw_meal_shield"]) if "jaw_meal_shield" in user.keys() else 0
        if shield:
            return None
        return (
            "a **broken jaw**; you cannot eat solid food. "
            "liquid diet (broth, milk) and slippery elm until it heals."
        )
    return None


def attack_roll_modifiers(user, attack_type: str) -> tuple[int, bool]:
    """
    returns (extra damage modifier, disadvantage on attack roll).
    torn_claw: −1 claw damage · broken_tooth: disadvantage on bite.
    """
    injuries = active_injury_keys(user)
    damage_mod = 0
    disadvantage = False
    if attack_type == "claw" and "torn_claw" in injuries:
        damage_mod -= 1
    if attack_type == "bite" and "broken_tooth" in injuries:
        disadvantage = True
    return damage_mod, disadvantage


def perception_penalty(user) -> int:
    from engine.genetics import genetic_perception_penalty

    penalty = genetic_perception_penalty(user)
    if has_injury(user, "torn_ear"):
        penalty -= 1
    return penalty


def check_penalty_for_injury(user, attr: str) -> int:
    """flat penalty on attribute checks from injuries."""
    injuries = active_injury_keys(user)
    penalty = 0
    if attr == "int" and "concussion" in injuries:
        penalty -= 1
    if attr == "wis" and "torn_ear" in injuries:
        penalty -= 1
    if attr == "dex" and "punctured_paw" in injuries:
        penalty -= 1
    if attr == "str" and "fractured_rib" in injuries:
        penalty -= 1
    return penalty


def injury_check_adjustments(
    user, attr_keys: tuple[str, ...], skill: str | None
) -> tuple[int, bool]:
    """
    Returns (flat_modifier, disadvantage) for skill/attribute checks.
    Disadvantage = roll 2d20 keep lower.
    """
    injuries = active_injury_keys(user)
    penalty = 0
    disadvantage = False
    attrs = set(attr_keys)
    if "concussion" in injuries and "attr_int" in attrs:
        disadvantage = True
    if "fractured_rib" in injuries and "attr_str" in attrs:
        disadvantage = True
    if ("spinal_injury" in injuries or "paralyzed" in injuries) and bool(
        attrs & {"attr_str", "attr_dex"}
    ):
        disadvantage = True
    if "punctured_paw" in injuries and "attr_dex" in attrs:
        disadvantage = True
    if "torn_ear" in injuries and "attr_wis" in attrs:
        penalty -= 1
    smoke = int(user["smoke_debuff"]) if user and "smoke_debuff" in user.keys() else 0
    if smoke and "attr_wis" in attrs:
        disadvantage = True
    return penalty, disadvantage


def format_injury_brief(key: str) -> str:
    info = INJURIES.get(key)
    if not info:
        return key
    return f"**{info['name']}**; {info['effect']}"
