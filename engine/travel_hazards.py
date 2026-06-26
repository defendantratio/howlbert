"""Travel hazard DCs by territory type."""

from __future__ import annotations

import random

import database as db
from engine.dice import format_roll_result, resolve_check
from engine.herb_buffs import grant_frostbite
from engine.vitals import apply_hp_damage


def _apply_travel_hp_loss(user, dmg: int, lines: list[str], *, label: str | None = None) -> None:
    _, extras = apply_hp_damage(user, dmg)
    lines.append(label if label else f"**−{dmg} HP**")
    lines.extend(extras)

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
        _apply_travel_hp_loss(user, dmg, lines)
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
    weather: str | None = None,
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
    blizzard = season == "winter" and weather in ("snow", "blizzard", "hail")
    if blizzard and result["success"]:
        result2 = resolve_check(
            user,
            attr_keys=("attr_wis", "attr_con"),
            skill="Survival",
            dc=dc,
            proficient=False,
            skill_key="survival",
            game_day=day,
            fear_context=fear_context,
        )
        lines.append("_Blizzard; second hazard check._")
        lines.append(format_roll_result(result2))
        if not result2["success"]:
            result = result2
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
    elif territory == "forest":
        hours_lost = random.randint(1, 4)
        ex_gain = 1 if hours_lost >= 3 else 0
        if ex_gain:
            ex = min(6, int(user["exhaustion"]) + ex_gain)
            db.set_user_conditions(user["discord_id"], exhaustion=ex)
            lines.append(f"Wandered **{hours_lost} hours** off-trail; **+{ex_gain} exhaustion**.")
        else:
            lines.append(f"Wandered **{hours_lost} hours** off-trail; legs heavy but you push on.")
    elif territory == "swamp":
        if spec.get("damage"):
            dmg = random.randint(*spec["damage"])
            _apply_travel_hp_loss(
                user,
                dmg,
                lines,
                label=f"**Swamp poison**: **−{dmg} HP** until antidote or rest.",
            )
        from engine.disease_contract import try_contract_disease

        poison_note = try_contract_disease(user, "mild_poison", "stung", chance=0.55)
        if poison_note:
            lines.append(poison_note)
        rot_note = try_contract_disease(user, "rot_lung", "fever", chance=0.18)
        if rot_note:
            lines.append(f"Marsh gas: {rot_note}")
    elif spec.get("damage"):
        dmg = random.randint(*spec["damage"])
        _apply_travel_hp_loss(user, dmg, lines)
    return False, "\n".join(lines)


WC_ENCOUNTER_EFFECTS: dict[str, str] = {
    "Clan patrol": "patrol",
    "rogue": "rogue",
    "dog": "dog",
    "monster": "monster",
    "badger": "badger",
}

WC_ENCOUNTER_FIND_EFFECTS: dict[str, str] = {
    "medicine herbs": "herbs",
    "Twoleg rubbish": "bones",
    "carrion": "carrion",
    "shelter": "shelter",
    "water": "water",
}


def _apply_encounter_effect(user, label: str, *, day: int, guild_id: int, channel_id: int | None) -> tuple[list[str], int | None]:
    effect = WC_ENCOUNTER_EFFECTS.get(label, "patrol")
    lines: list[str] = []
    enc_id: int | None = None
    if effect == "patrol":
        db.adjust_mood(user["id"], -4)
        lines.append("**−4 mood**; you back away before claws meet.")
    elif effect == "rogue":
        db.adjust_mood(user["id"], -3)
        lines.append("**−3 mood**; the rogue melts into bracken.")
    elif effect == "dog":
        from engine.wild_encounters import start_verge_dog_ambush, verge_dog_bite_fallback

        ambush = start_verge_dog_ambush(
            user,
            guild_id=guild_id,
            channel_id=channel_id or 0,
            activity="wilderness",
        )
        if ambush:
            enc_id, _key, _flavor = ambush
            lines.append(f"A **guard hearth-hound** charges; combat **#{enc_id}** opened in-channel.")
            db.adjust_mood(user["id"], -3)
            lines.append("**−3 mood**; you flatten in the ditch until it passes or you fight.")
        else:
            lines.append(verge_dog_bite_fallback(user, day=day))
            db.adjust_mood(user["id"], -5)
            dmg = random.randint(1, 4)
            _apply_travel_hp_loss(
                user,
                dmg,
                lines,
                label=f"**−5 mood**, **−{dmg} HP**.",
            )
    elif effect == "badger":
        result = resolve_check(
            user,
            attr_keys=("attr_dex",),
            skill=None,
            dc=12,
            proficient=False,
            skill_key=None,
            game_day=day,
        )
        lines.append(format_roll_result(result))
        if not result["success"]:
            dmg = random.randint(2, 8)
            _apply_travel_hp_loss(
                user,
                dmg,
                lines,
                label=f"The **badger** rakes your muzzle; **−{dmg} HP**.",
            )
        else:
            lines.append("You give the sett a wide berth.")
    return lines, enc_id


def _apply_find_effect(user, label: str, *, day: int, guild_id: int) -> list[str]:
    effect = WC_ENCOUNTER_FIND_EFFECTS.get(label, "bones")
    lines: list[str] = []
    if effect == "herbs":
        from engine.cat_clan_goods import medicine_herb_display
        from engine.herb_habitat import herbs_for_verge

        pool = herbs_for_verge("roadside") or ["yarrow"]
        herb_key = random.choice(pool)
        stack_id = db.add_herb_stack(user["id"], herb_key, guild_id=guild_id, acquired_day=day)
        lines.append(f"Gathered **{medicine_herb_display(herb_key)}**; stack `#{stack_id}`.")
    elif effect == "bones":
        bones = random.randint(5, 12)
        db.add_bones(user["discord_id"], bones, wolf_id=user["id"])
        lines.append(f"**+{bones} bones** from useful scrap.")
    elif effect == "carrion":
        from engine.disease_contract import try_scavenge_filth_exposure
        from engine.prey_storage import grant_prey_carcass

        stack_id = grant_prey_carcass(
            user["id"], "rabbit", guild_id=guild_id, acquired_day=day, bone_value=6
        )
        lines.append(f"Risky **carrion**; carcass `#{stack_id}` in hoard.")
        filth = try_scavenge_filth_exposure(user, day=day)
        if filth:
            lines.append(filth)
    elif effect == "shelter":
        mood = db.adjust_mood(user["id"], 3)
        lines.append(f"Dry rest under the shed; mood **{mood}** (**+3**).")
    elif effect == "water":
        thirst = db.adjust_thirst(user["id"], -4)
        lines.append(f"Clean lap from the stream; thirst **{thirst}** (**−4**).")
    return lines


def roll_wilderness_encounter(
    user,
    *,
    day: int,
    guild_id: int,
    channel_id: int | None = None,
) -> tuple[str, str, int | None]:
    roll = random.randint(1, 20)
    if roll <= 5:
        label, text = random.choice(WC_ENCOUNTER_BAD)
        extra, enc_id = _apply_encounter_effect(
            user, label, day=day, guild_id=guild_id, channel_id=channel_id
        )
        body = f"Roll **{roll}**; **{label}** — {text}"
        if extra:
            body += "\n\n" + "\n".join(extra)
        return "encounter", body, enc_id
    if roll <= 15:
        return "quiet", f"Roll **{roll}**; the border is quiet; only wind and distant Twoleg birds.", None
    label, text = random.choice(WC_ENCOUNTER_FIND)
    extra = _apply_find_effect(user, label, day=day, guild_id=guild_id)
    body = f"Roll **{roll}**; you find **{label}** — {text}"
    if extra:
        body += "\n\n" + "\n".join(extra)
    return "find", body, None


def roll_rest_omen() -> tuple[str, str]:
    from engine.starclan_omens import roll_rest_omen as _starclan_roll

    return _starclan_roll()
