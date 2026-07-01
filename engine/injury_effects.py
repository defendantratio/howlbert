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


def injury_hunt_multiplier(user) -> tuple[float, str]:
    """
    Non-blocking injuries still cost hunt yield — sprained leg, infected wound,
    etc. slow a wolf without stopping them entirely. Stacks up to −50%.
    """
    injuries = active_injury_keys(user)
    if not injuries:
        return 1.0, ""
    PENALTIES: dict[str, tuple[float, str]] = {
        "sprained_leg":   (0.25, "sprained leg; speed cut on the hunt (**−25%**)"),
        "punctured_paw":  (0.20, "punctured paw; every stride costs (**−20%**)"),
        "concussion":     (0.20, "concussion; disoriented tracking (**−20%**)"),
        "deep_gash":      (0.15, "deep gash; blood loss and pain (**−15%**)"),
        "infected_wound": (0.15, "infected wound; fever and fatigue (**−15%**)"),
        "torn_claw":      (0.10, "torn claw; reduced grip on prey (**−10%**)"),
        "broken_tooth":   (0.10, "broken tooth; bite strength reduced (**−10%**)"),
        "torn_ear":       (0.05, "torn ear; tracking by sound impaired (**−5%**)"),
    }
    total = 0.0
    worst_label = ""
    worst_pen = 0.0
    for key in injuries:
        pen, label = PENALTIES.get(key, (0.0, ""))
        if pen > worst_pen:
            worst_pen = pen
            worst_label = label
        total += pen
    total = min(total, 0.50)
    if total <= 0:
        return 1.0, ""
    pct = int(total * 100)
    note = worst_label if pct == int(worst_pen * 100) else f"injuries; reduced effectiveness (**−{pct}%**)"
    return 1.0 - total, note


def injury_patrol_standing_bonus(user) -> int:
    """
    Standing bonus for patrolling with a non-blocking physical injury — putting
    the pack ahead of your own pain is noticed and respected. Capped at +2.
    """
    injuries = active_injury_keys(user)
    PATROL_BONUSES: dict[str, int] = {
        "sprained_leg": 1,
        "punctured_paw": 1,
        "deep_gash": 1,
        "infected_wound": 1,
        "concussion": 1,
    }
    return min(2, sum(PATROL_BONUSES.get(k, 0) for k in injuries))


def injury_caught_standing_penalty(user) -> int:
    """
    Extra standing loss when a patrol goes wrong (spotted, ambushed) and the
    wolf was already hurt — the injury is why they couldn't get away clean.
    """
    injuries = active_injury_keys(user)
    CAUGHT_PENALTIES: dict[str, int] = {
        "sprained_leg": -1,
        "punctured_paw": -1,
        "deep_gash": -1,
        "infected_wound": -1,
        "concussion": -1,
    }
    return max(-2, sum(CAUGHT_PENALTIES.get(k, 0) for k in injuries))


def format_injury_brief(key: str) -> str:
    info = INJURIES.get(key)
    if not info:
        return key
    return f"**{info['name']}**; {info['effect']}"


def try_prey_counter_injury(user, amount: int, day: int) -> str | None:
    """15% chance of sprained_leg or punctured_paw on a failed hunt (amount <= 0)."""
    import json
    import random
    from engine.conditions import add_injury, parse_injuries
    import database as db

    if amount > 0:
        return None
    if random.random() >= 0.15:
        return None
    key = random.choice(("sprained_leg", "punctured_paw"))
    current = parse_injuries(user["active_injuries"] if "active_injuries" in user.keys() else None)
    if key in current:
        return None
    updated = add_injury(current, key)
    db.set_user_conditions(user["discord_id"], active_injuries=json.dumps(updated), wolf_id=user["id"])
    info = INJURIES.get(key)
    name = info["name"] if info else key
    return f"_prey fought back; **{name}** ({info['effect'] if info else ''})._"
