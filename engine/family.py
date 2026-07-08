import json
import random

from engine.character import attr_modifier, default_stats_for_role
from engine.dice import roll_d20
from rpg_rules import ROLE_PROFICIENCIES, SKILLS, MAX_SKILL_RANK, XP_PER_TRAIT

GESTATION_DAYS = 63
XP_PER_ATTRIBUTE = 5
XP_PER_SKILL = 5
XP_PER_ROLE_FEATURE = 10

COURTSHIP_DCS = {
    "friendly": 12,
    "neutral": 15,
    "hostile": 18,
}


def courtship_check(user, difficulty: str = "friendly", *, fearful: bool = False) -> dict:
    from engine.character_traits import trait_check_adjustments

    dc = COURTSHIP_DCS.get(difficulty, 15)
    die = min(roll_d20(), roll_d20()) if fearful else roll_d20()
    cha_mod = attr_modifier(user["attr_cha"])
    trait_mod, _ = trait_check_adjustments(
        user, ("attr_cha",), skill_key="persuasion", skill_label="Persuasion"
    )
    total = die + cha_mod + trait_mod
    if die == 1:
        outcome = "critical_failure"
        success = False
    elif die == 20:
        outcome = "critical_success"
        success = True
    elif total >= dc:
        outcome = "success"
        success = True
    else:
        outcome = "failure"
        success = False
    return {"die": die, "total": total, "dc": dc, "success": success, "outcome": outcome}


def _mother_condition_penalty(female) -> tuple[int, str]:
    """
    Care during courtship and early pregnancy should matter mechanically,
    not just for show: a mother who's starving, exhausted, or miserable at
    conception carries real extra risk, not a flat roll regardless of her
    condition.
    """
    hunger = int(female["hunger"]) if "hunger" in female.keys() and female["hunger"] is not None else 100
    exhaustion = int(female["exhaustion"]) if "exhaustion" in female.keys() and female["exhaustion"] is not None else 0
    mood = int(female["mood"]) if "mood" in female.keys() and female["mood"] is not None else 50
    penalty = 0
    notes = []
    if hunger < 30:
        penalty += 2
        notes.append("hungry")
    if exhaustion >= 3:
        penalty += 2
        notes.append("exhausted")
    if mood < 25:
        penalty += 1
        notes.append("low mood")
    note = f"mother's condition ({', '.join(notes)}): −{penalty}" if notes else ""
    return penalty, note


def conception_check(female, male) -> dict:
    die = roll_d20()
    f_mod = attr_modifier(female["attr_con"])
    m_mod = attr_modifier(male["attr_con"])
    condition_penalty, condition_note = _mother_condition_penalty(female)
    total = die + f_mod + m_mod - condition_penalty
    dc = 15
    if die == 1:
        outcome = "complication"
        success = False
    elif die == 20:
        outcome = "critical_success"
        success = True
    elif total >= dc:
        outcome = "success"
        success = True
    elif condition_penalty >= 3 and total < dc - 5:
        outcome = "complication"
        success = False
    else:
        outcome = "failure"
        success = False
    return {
        "die": die,
        "total": total,
        "dc": dc,
        "success": success,
        "outcome": outcome,
        "f_mod": f_mod,
        "m_mod": m_mod,
        "condition_penalty": condition_penalty,
        "condition_note": condition_note,
    }


def birth_check(mother) -> dict:
    from engine.herb_buffs import birth_save_has_advantage

    die = roll_d20()
    used_birth_advantage = birth_save_has_advantage(mother)
    if used_birth_advantage:
        die = max(roll_d20(), roll_d20())
    mod = attr_modifier(mother["attr_con"])
    total = die + mod
    dc = 12
    if die == 1:
        outcome = "critical_failure"
        success = False
    elif die == 20:
        outcome = "critical_success"
        success = True
    elif total >= dc:
        outcome = "success"
        success = True
    else:
        outcome = "failure"
        success = False
    litter = random.randint(1, 4) + 1
    if not success:
        litter = max(1, litter - 1)
    # a well-fed dam carries a fuller litter; an underfed one reabsorbs or loses
    # pups. real litter size tracks the mother's body condition and prey supply.
    mother_hunger = int(mother["hunger"]) if "hunger" in mother.keys() and mother["hunger"] is not None else 100
    if mother_hunger < 15:
        litter = max(1, litter - 2)
    elif mother_hunger < 35:
        litter = max(1, litter - 1)
    elif mother_hunger >= 85 and success and random.random() < 0.30:
        litter += 1  # thriving dam, generous litter
    from engine.herb_buffs import extra_pup_milk

    if success and extra_pup_milk(mother):
        litter += 1
    return {
        "die": die,
        "total": total,
        "dc": dc,
        "success": success,
        "outcome": outcome,
        "litter_size": litter,
        "used_birth_advantage": used_birth_advantage,
        "extra_pup_from_borage": success and extra_pup_milk(mother),
        "mother_hunger": mother_hunger,
    }


def inherit_pup_attribute(parent_a: int, parent_b: int) -> int:
    """Method 2: average + 1d4: 2."""
    avg = (parent_a + parent_b) // 2
    roll = random.randint(1, 4)
    return max(1, min(10, avg + roll - 2))


def generate_pup_stats(mother, father) -> dict:
    keys = ("str", "dex", "con", "int", "cha", "wis")
    stats = {}
    for k in keys:
        ma = mother[f"attr_{k}"]
        fa = father[f"attr_{k}"]
        stats[f"attr_{k}"] = inherit_pup_attribute(ma, fa)
    total = sum(stats.values())
    while total < 6:
        k = random.choice(keys)
        if stats[f"attr_{k}"] < 10:
            stats[f"attr_{k}"] += 1
            total += 1
    while total > 10:
        k = random.choice(keys)
        if stats[f"attr_{k}"] > 1:
            stats[f"attr_{k}"] -= 1
            total -= 1
    return stats


def inherit_parent_skill_trait(pup_id: int, mother, father) -> str | None:
    """
    A small chance for a pup to start with a one-rank head start in
    whichever skill a parent has actually earned the most experience in ; 
    "comes from someone" instead of every litter starting blank regardless
    of what their parents spent seasons getting good at.
    """
    from config import PUP_TRAIT_INHERIT_CHANCE
    from engine.character_traits import get_earned_trait_bonus_for_wolf

    if random.random() >= PUP_TRAIT_INHERIT_CHANCE:
        return None

    candidates = [p for p in (mother, father) if p]
    if not candidates:
        return None
    parent = random.choice(candidates)

    best_skill = None
    best_bonus = 0
    for skill_key in SKILLS:
        bonus = get_earned_trait_bonus_for_wolf(parent["id"], skill_key)
        if bonus > best_bonus:
            best_bonus = bonus
            best_skill = skill_key
    if not best_skill:
        return None

    import database as db

    db.add_skill_rank(pup_id, best_skill, 1, grant_proficiency=True)
    label = SKILLS[best_skill][1]
    return f"inherits a touch of **{parent['wolf_name']}**'s **{label}**."


def mark_runt_pup(pup_id: int, stats: dict) -> str | None:
    """
    The smallest pup in a litter of RUNT_LITTER_MIN_SIZE+ starts at a real,
    permanent disadvantage instead of just an RP label nothing reacts to:
    -1 to its lowest attribute (floor 1), tagged with the runt long-term
    trait. Returns a player-facing note naming the weakened attribute.
    """
    from config import RUNT_ATTR_PENALTY
    from engine.long_term_injuries import add_long_term_injury

    keys = ("str", "dex", "con", "int", "cha", "wis")
    weakest = min(keys, key=lambda k: stats[f"attr_{k}"])
    new_val = max(1, stats[f"attr_{weakest}"] - RUNT_ATTR_PENALTY)
    import database as db

    db.update_user_by_id(pup_id, **{f"attr_{weakest}": new_val})
    add_long_term_injury(pup_id, "runt")
    return weakest


def grant_runt_first_feed_bond(feeder_id: int, pup_id: int, *, day: int) -> None:
    """
    Whoever feeds a runt first, while it's struggling, tends to grow close
    to it; a real kin-bond bump instead of just a feeding log entry.
    """
    from config import RUNT_FIRST_FEED_BOND_BONUS
    import database as db

    if feeder_id == pup_id:
        return
    existing = db.get_bond(feeder_id, pup_id, "kin")
    if existing:
        db.adjust_bond_strength(feeder_id, pup_id, "kin", RUNT_FIRST_FEED_BOND_BONUS, day=day)
    else:
        db.set_bond(
            feeder_id,
            pup_id,
            "kin",
            strength=40 + RUNT_FIRST_FEED_BOND_BONUS,
            note="first to feed the runt",
            day=day,
        )


def spend_xp_attribute(user, attr_key: str) -> str | None:
    key = f"attr_{attr_key}"
    if key not in user.keys():
        return "invalid attribute."
    if user[key] >= 10:
        return "attribute already at maximum (10)."
    return None


def spend_xp_trait_bonus(user, skill: str) -> str | None:
    from engine.character_traits import spend_xp_trait_bonus as _validate

    return _validate(user, skill)
