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
    "twolegplace": {
        "label": "Twolegplace",
        "dc": 14,
        "failure": "Twoleg dangers on the edge of cat territory.",
        "damage": None,
    },
}

TWOLEG_FAILURES: tuple[tuple[str, str, tuple[int, int] | None], ...] = (
    (
        "thunderpath",
        "A **monster** roars along the **Thunderpath**; iron paws and blinding eyes. "
        "You throw yourself into the ditch.",
        (3, 8),
    ),
    (
        "nest",
        "Smoke and sharp scent pour from a **Twoleg nest**; you choke and flee the fence-line.",
        (1, 4),
    ),
    (
        "dog",
        "A **pet dog** on a trailing vine lunges from a garden; teeth snap at your haunches.",
        (2, 6),
    ),
    (
        "trap",
        "A **Twoleg trap** snaps shut on brush where your paw almost landed.",
        None,
    ),
)

WC_ENCOUNTER_BAD = (
    ("Clan patrol", "A **Clan patrol** challenges you near the scent-line; you back away before claws meet."),
    ("rogue", "A **rogue cat** stalks the rubbish heap behind a Twoleg fence."),
    ("dog", "A **Twoleg dog** bays from a chained post; you circle wide through the weeds."),
    ("monster", "Distant **monster**-roar on the Thunderpath; every cat and wolf freezes."),
    ("badger", "A **badger** guards a sett near the border; best not to press."),
)

WC_ENCOUNTER_FIND = (
    ("medicine herbs", "Windfall **herbs** dropped where a medicine cat gathered at the border."),
    ("Twoleg rubbish", "Useful **scrap** in a Twoleg rubbish heap (feathers, bone, string)."),
    ("carrion", "Fresh **carrion** near the Thunderpath; risky but filling."),
    ("shelter", "A dry **shelter** under an abandoned Twoleg shed."),
    ("water", "A **stream** untainted by monster-scent."),
)


def travel_hazard_dc(territory: str, *, season: str | None = None, guild_id: int | None = None) -> int:
    """Base DC; spring river crossings are +2 (melt floods)."""
    spec = TERRITORY_HAZARDS.get(territory)
    if not spec:
        return 12
    dc = int(spec["dc"])
    if territory == "river" and season == "spring":
        dc += 2
    if territory == "twolegplace" and season == "winter":
        dc += 1
    if guild_id is not None:
        from engine.plot_blinking import plot_travel_dc_bonus

        dc += plot_travel_dc_bonus(guild_id, territory)
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


def _apply_twoleg_failure(user, day: int) -> list[str]:
    _key, text, damage = random.choice(TWOLEG_FAILURES)
    lines = [text]
    if damage:
        dmg = random.randint(*damage)
        new_hp = max(0, int(user["hp"]) - dmg)
        db.set_user_conditions(user["discord_id"], hp=new_hp)
        lines.append(f"**−{dmg} HP**")
    elif _key == "trap":
        lines.append(_lose_random_herb_stack(user))
    if _key == "nest":
        ex = min(6, int(user["exhaustion"]) + 1)
        db.set_user_conditions(user["discord_id"], exhaustion=ex)
        lines.append("+1 exhaustion from smoke.")
    return lines


def roll_travel_hazard(
    user,
    territory: str,
    *,
    day: int,
    season: str | None = None,
    guild_id: int | None = None,
) -> tuple[bool, str]:
    spec = TERRITORY_HAZARDS.get(territory)
    if not spec:
        return False, f"Unknown territory **{territory}**."
    dc = travel_hazard_dc(territory, season=season, guild_id=guild_id)
    fear_context = territory
    if territory == "river" and season == "spring":
        fear_context = "spring_river"
    if territory == "twolegplace":
        fear_context = "twolegplace"
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
    if territory == "twolegplace":
        season_note = " _(Twoleg fences, Thunderpath, monster-nests)_"
    lines = [f"**{spec['label']}** travel · {format_roll_result(result)}{season_note}"]
    if result["success"]:
        if territory == "twolegplace":
            lines.append("You slip past nests and fences; the Thunderpath fades behind you.")
        else:
            lines.append("Path holds; you cross safely.")
        return True, "\n".join(lines)
    if territory == "twolegplace":
        lines.extend(_apply_twoleg_failure(user, day))
        return False, "\n".join(lines)
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
        label, text = random.choice(WC_ENCOUNTER_BAD)
        return "encounter", f"Roll **{roll}**; **{label}** — {text}"
    if roll <= 15:
        return "quiet", f"Roll **{roll}**; the border is quiet; only wind and distant Twoleg birds."
    label, text = random.choice(WC_ENCOUNTER_FIND)
    return "find", f"Roll **{roll}**; you find **{label}** — {text}"


def roll_rest_omen() -> tuple[str, str]:
    from engine.starclan_omens import roll_rest_omen as _starclan_roll

    return _starclan_roll()
