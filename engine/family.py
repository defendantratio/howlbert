import json
import random

from engine.character import attr_modifier, default_stats_for_role
from engine.dice import roll_d20
from rpg_rules import PROFICIENCY_BONUS, ROLE_PROFICIENCIES, SKILLS, MAX_SKILL_RANK, XP_PER_SKILL_RANK

GESTATION_DAYS = 63
XP_PER_ATTRIBUTE = 5
XP_PER_SKILL = 5
XP_PER_ROLE_FEATURE = 10

COURTSHIP_DCS = {
    "friendly": 12,
    "neutral": 15,
    "hostile": 18,
}


def courtship_check(user, difficulty: str = "friendly") -> dict:
    from engine.character import is_skill_proficient, skill_proficiency_bonus

    dc = COURTSHIP_DCS.get(difficulty, 15)
    die = roll_d20()
    cha_mod = attr_modifier(user["attr_cha"])
    prof = skill_proficiency_bonus(
        user, "persuasion", proficient=is_skill_proficient(user, "persuasion")
    )
    total = die + cha_mod + prof
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


def conception_check(female, male) -> dict:
    die = roll_d20()
    f_mod = attr_modifier(female["attr_con"])
    m_mod = attr_modifier(male["attr_con"])
    total = die + f_mod + m_mod
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


def spend_xp_attribute(user, attr_key: str) -> str | None:
    key = f"attr_{attr_key}"
    if key not in user.keys():
        return "Invalid attribute."
    if user[key] >= 10:
        return "Attribute already at maximum (10)."
    return None


def spend_xp_skill(user, skill: str) -> str | None:
    from engine.character import is_skill_proficient

    if skill not in SKILLS:
        return "Unknown skill."
    if is_skill_proficient(user, skill):
        return "Already proficient in that skill (including role training)."
    return None


def spend_xp_skill_rank(user, skill: str) -> str | None:
    from engine.character import get_skill_rank, is_skill_proficient

    if skill not in SKILLS:
        return "Unknown skill."
    if not is_skill_proficient(user, skill):
        return f"Learn **{SKILLS[skill][1]}** proficiency first (`/advance action:spend purchase:skill`)."
    if get_skill_rank(user, skill) >= MAX_SKILL_RANK:
        return f"**{SKILLS[skill][1]}** is already at max rank (**{MAX_SKILL_RANK}**)."
    return None
