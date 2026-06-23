"""Travel hazard DCs by territory type."""

from __future__ import annotations

import random

import database as db
from engine.dice import format_roll_result, resolve_check
from engine.herb_buffs import grant_frostbite

TERRITORY_HAZARDS = {
    "river": {
        "label": "River",
        "dc": 12,
        "failure": "Strong current; gain **1 exhaustion** or lose a herb bundle.",
        "damage": None,
    },
    "swamp": {
        "label": "Swamp",
        "dc": 15,
        "failure": "Poisonous gas or sinkhole; **poisoned** (1d4 damage/hour until treated).",
        "damage": (1, 4),
    },
    "mountain": {
        "label": "Mountain",
        "dc": 18,
        "failure": "Avalanche chill; **frostbite** (−1 Dexterity until treated).",
        "damage": None,
    },
    "forest": {
        "label": "Forest",
        "dc": 10,
        "failure": "Lost in the trees; lose **1d4 hours** of travel.",
        "damage": None,
    },
}


def travel_hazard_dc(territory: str, *, season: str | None = None) -> int:
    """Base DC; spring river crossings are +2 (melt floods)."""
    spec = TERRITORY_HAZARDS.get(territory)
    if not spec:
        return 12
    dc = int(spec["dc"])
    if territory == "river" and season == "spring":
        dc += 2
    return dc


def _lose_random_herb_stack(user) -> str:
    stacks = db.get_herb_stacks(user["id"])
    if not stacks:
        return "Nothing left in the herb bag to wash away."
    stack = random.choice(stacks)
    db.remove_herb_stack(stack["id"])
    from herbs import HERBS

    name = HERBS.get(stack["herb_key"], {}).get("name", stack["herb_key"])
    return f"A **{name}** stack washes from your bag."


def roll_travel_hazard(
    user,
    territory: str,
    *,
    day: int,
    season: str | None = None,
) -> tuple[bool, str]:
    spec = TERRITORY_HAZARDS.get(territory)
    if not spec:
        return False, f"Unknown territory **{territory}**."
    dc = travel_hazard_dc(territory, season=season)
    fear_context = territory
    if territory == "river" and season == "spring":
        fear_context = "spring_river"
    result = resolve_check(
        user,
        attr_keys=("attr_wis", "attr_con"),
        skill="Survival",
        dc=dc,
        proficient=False,
        skill_key="survival",
        game_day=day,
        fear_context=fear_context,
    )
    season_note = ""
    if territory == "river" and season == "spring":
        season_note = " _(spring melt; DC +2)_"
    lines = [f"**{spec['label']}** travel · {format_roll_result(result)}{season_note}"]
    if result["success"]:
        lines.append("Path holds; you cross safely.")
        return True, "\n".join(lines)
    lines.append(spec["failure"])
    if territory == "mountain":
        fields = grant_frostbite(user, day=day)
        db.update_user(user["discord_id"], wolf_id=user["id"], **fields)
        lines.append("**Frostbite**: **−1 Dex** until treated or after a week of warmth.")
    elif territory == "river":
        lines.append(_lose_random_herb_stack(user))
        ex = min(6, int(user["exhaustion"]) + 1)
        db.set_user_conditions(user["discord_id"], exhaustion=ex)
        lines.append("+1 exhaustion fighting the current.")
    elif territory == "swamp":
        if spec.get("damage"):
            dmg = random.randint(*spec["damage"])
            new_hp = max(0, int(user["hp"]) - dmg)
            db.set_user_conditions(user["discord_id"], hp=new_hp)
            lines.append(f"**Swamp poison**: **−{dmg} HP** until antidote or rest.")
    elif spec.get("damage"):
        dmg = random.randint(*spec["damage"])
        new_hp = max(0, int(user["hp"]) - dmg)
        db.set_user_conditions(user["discord_id"], hp=new_hp)
        lines.append(f"**−{dmg} HP**")
    return False, "\n".join(lines)


def roll_wilderness_encounter() -> tuple[str, str]:
    roll = random.randint(1, 20)
    if roll <= 5:
        kind = random.choice(["predator", "rival wolf", "hazard", "Twoleg trap"])
        return "encounter", f"Roll **{roll}**; **{kind}** crosses your path."
    if roll <= 15:
        return "quiet", f"Roll **{roll}**; nothing stirs."
    find = random.choice(["herb patch", "carcass", "water source", "shelter ledge"])
    return "find", f"Roll **{roll}**; you find a **{find}**."


def roll_rest_omen() -> tuple[str, str]:
    roll = random.randint(1, 20)
    if roll == 1:
        return "bad", "Roll **1**; bad omen (**disadvantage** on tomorrow's first roll)."
    if roll == 20:
        return "good", "Roll **20**; good omen (**advantage** on tomorrow's first roll)."
    return "neutral", f"Roll **{roll}**; the Maw is silent tonight."
