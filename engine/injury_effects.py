"""Mechanical effects of active injuries in combat and activities."""

from __future__ import annotations

from config import MOOD_CRITICAL_THRESHOLD
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
    # no injury blocks eating outright; broken jaw adds pain exhaustion (see meal_jaw_pain_note)
    return None


def meal_jaw_pain_note(user) -> str:
    """Apply +3 pain exhaustion when eating with a broken jaw (waived by jaw_meal_shield).
    Returns a player-facing note, or empty string if no penalty."""
    if not has_injury(user, "broken_jaw"):
        return ""
    shield = int(user["jaw_meal_shield"]) if "jaw_meal_shield" in user.keys() else 0
    if shield:
        return ""
    import database as _inj_db
    from engine.exhaustion_effects import PAIN_EXHAUSTION_MAX as _PE_MAX
    old_pe = int(user["pain_exhaustion"]) if "pain_exhaustion" in user.keys() else 0
    new_pe = min(_PE_MAX, old_pe + 3)
    _inj_db.update_user(int(user["discord_id"]), wolf_id=int(user["id"]), pain_exhaustion=new_pe)
    return "\n_eating with a **broken jaw** is agonizing — **+3 pain exhaustion**. slippery elm removes this._"


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
    if attr == "wis" and "concussion" in injuries and "swollen_eye" not in injuries:
        # Early orbital blur before full swollen_eye sets in (days 1-2).
        penalty -= 1
    if attr == "wis" and "torn_ear" in injuries:
        penalty -= 1
    if attr == "dex" and "punctured_paw" in injuries:
        penalty -= 1
    if attr == "str" and "fractured_rib" in injuries:
        penalty -= 1
    if attr == "str" and "bruised_lung" in injuries:
        penalty -= 1
    if attr == "wis" and "bruised_lung" in injuries:
        penalty -= 1
    if attr == "dex" and "snake_venom" in injuries:
        penalty -= 4
    if attr == "dex" and "insect_sting" in injuries:
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
    if "fractured_rib" in injuries and bool(attrs & {"attr_str", "attr_dex"}):
        disadvantage = True
    if "bruised_lung" in injuries and bool(attrs & {"attr_str", "attr_wis", "attr_con"}):
        disadvantage = True
    if ("spinal_injury" in injuries or "paralyzed" in injuries) and bool(
        attrs & {"attr_str", "attr_dex"}
    ):
        disadvantage = True
    if "punctured_paw" in injuries and "attr_dex" in attrs:
        disadvantage = True
    if "snake_venom" in injuries and "attr_dex" in attrs:
        penalty -= 4
    if "insect_sting" in injuries and "attr_dex" in attrs:
        penalty -= 1
    if "torn_ear" in injuries and "attr_wis" in attrs:
        penalty -= 1
    smoke = int(user["smoke_debuff"]) if user and "smoke_debuff" in user.keys() else 0
    if smoke and "attr_wis" in attrs:
        disadvantage = True
    # Exhaustion 4: body past its limit — disadvantage on all physical attribute checks.
    if user and "exhaustion" in user.keys() and int(user["exhaustion"]) >= 4:
        if bool(attrs & {"attr_str", "attr_dex", "attr_con"}):
            disadvantage = True
    # Compound injury burden: each injury beyond the first adds -1 to all checks (cap -4).
    if len(injuries) > 1:
        penalty -= min(4, len(injuries) - 1)
    # Critical mood: wolf is barely present — WIS disadvantage on field checks.
    if user and "mood" in user.keys() and int(user["mood"]) < MOOD_CRITICAL_THRESHOLD:
        if "attr_wis" in attrs:
            disadvantage = True
    # Pain exhaustion: accumulated physical pain impairs checks.
    from engine.exhaustion_effects import pain_exhaustion_check_adjustments
    pe_pen, pe_dis = pain_exhaustion_check_adjustments(user, attr_keys)
    penalty += pe_pen
    if pe_dis:
        disadvantage = True
    return penalty, disadvantage


def injury_hunt_multiplier(user) -> tuple[float, str]:
    """
    Non-blocking injuries still cost hunt yield — sprained leg, infected wound,
    etc. slow a wolf without stopping them entirely. Stacks up to −50%.
    """
    injuries = active_injury_keys(user)
    from engine.long_term_injuries import parse_long_term_injuries
    lt_injuries = parse_long_term_injuries(user["long_term_injuries"] if user and "long_term_injuries" in user.keys() else None)
    if not injuries and not lt_injuries:
        return 1.0, ""
    PENALTIES: dict[str, tuple[float, str]] = {
        "sprained_leg":   (0.25, "sprained leg; speed cut on the hunt (**−25%**)"),
        "punctured_paw":  (0.20, "punctured paw; every stride costs (**−20%**)"),
        "bruised_lung":   (0.20, "bruised lung; every stride is labored (**−20%**)"),
        "concussion":     (0.20, "concussion; disoriented tracking (**−20%**)"),
        "snake_venom":    (0.20, "snake venom; venom-slowed limbs and burning pain (**−20%**)"),
        "deep_gash":      (0.15, "deep gash; blood loss and pain (**−15%**)"),
        "infected_wound": (0.15, "infected wound; fever and fatigue (**−15%**)"),
        "torn_claw":      (0.10, "torn claw; reduced grip on prey (**−10%**)"),
        "broken_tooth":   (0.10, "broken tooth; bite strength reduced (**−10%**)"),
        "torn_ear":       (0.05, "torn ear; tracking by sound impaired (**−5%**)"),
    }
    LT_PENALTIES: dict[str, tuple[float, str]] = {
        "limp": (0.15, "old leg injury; permanent limp slows the chase (**−15%**)"),
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
    for key in lt_injuries:
        pen, label = LT_PENALTIES.get(key, (0.0, ""))
        if pen > worst_pen:
            worst_pen = pen
            worst_label = label
        total += pen
    from engine.exhaustion_effects import pain_exhaustion_hunt_multiplier
    pe_mult, pe_note = pain_exhaustion_hunt_multiplier(user)
    pe_pen_amt = 1.0 - pe_mult
    if pe_pen_amt > 0:
        total += pe_pen_amt
        if pe_pen_amt > worst_pen:
            worst_pen = pe_pen_amt
            worst_label = pe_note
    total = min(total, 0.50)
    if total <= 0:
        return 1.0, ""
    pct = int(total * 100)
    note = worst_label if pct == int(worst_pen * 100) else f"injuries; reduced effectiveness (**-{pct}%**)"
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


def in_shock(fighter_f) -> bool:
    """True when a fighter's in-combat HP falls below 25% of their max — shock sets in."""
    if not fighter_f:
        return False
    try:
        hp = int(fighter_f["hp"])
        max_hp = int(fighter_f["max_hp"])
    except (KeyError, TypeError, ValueError):
        return False
    return max_hp > 0 and hp / max_hp < 0.25


def active_bleed_per_round(user) -> int:
    """HP drained per combat round from active bleeding injuries."""
    injuries = active_injury_keys(user)
    if "deep_gash" in injuries:
        return 1
    return 0


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
