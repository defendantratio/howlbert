"""Optional explore encounters; Wolvden-style dig, follow, investigate."""

from __future__ import annotations

import random

import discord

from engine.amusement_items import amusement_meta
from engine.amusement_storage import grant_amusement
from engine.dice import format_roll_result, resolve_check
from engine.prey_storage import grant_prey_carcass
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed

EXPLORE_ACTIONS = {
    "dig": {
        "label": "Dig",
        "emoji": "🕳️",
        "skill": "Survival",
        "attrs": ("attr_str", "attr_con"),
        "dc": 10,
        "flavor": "You dig through leaf-mold and old den scrapes.",
    },
    "follow": {
        "label": "Follow scent",
        "emoji": "👃",
        "skill": "Survival",
        "attrs": ("attr_wis", "attr_dex"),
        "dc": 12,
        "flavor": "A bitter thread of scent leads you off the main trail.",
    },
    "investigate": {
        "label": "Investigate",
        "emoji": "🔍",
        "skill": "Survival",
        "attrs": ("attr_wis", "attr_int"),
        "dc": 11,
        "flavor": "Something moved in the brush; you circle wide and look closer.",
    },
}

BIOME_FLAVOR = {
    "greyspire": "pine ridges and grey stone",
    "mistmoor": "mist-choked fen and willow",
    "thistlehide": "thorn scrub and dry gulch",
    "silverrush": "river shale and cottonwood",
    "loner": "unclaimed borderlands",
    "rogue": "stolen edges and trespassed borders",
}

DIG_LOOT = (
    ("bone", 30),
    ("acorn", 18),
    ("shell", 12),
    ("feather", 12),
    ("bones", 12),
    ("vole", 8),
    ("frog", 5),
    ("shiny_pebble", 8),
)

FOLLOW_LOOT = (
    ("stick", 22),
    ("feather", 18),
    ("talon", 10),
    ("herb", 22),
    ("hare", 14),
    ("bones", 10),
    ("moth_wing", 4),
)

INVESTIGATE_LOOT = (
    ("feather", 22),
    ("bone", 18),
    ("fish", 14),
    ("frog", 8),
    ("grouse", 14),
    ("bones", 14),
    ("shell", 10),
    ("crow_feather", 8),
)

EXPLORE_SIDE_FINDS = [
    "An old raven nest spills **shiny bits**; you tuck one away.",
    "You find a sun-warmed hollow where prey slept last night; **+2 mood**.",
    "Coyote sign warns you off a cache; you leave it and mark the spot for the den.",
    "A fallen log hides **grubs**; not a meal, but useful bait scent.",
    "You cross a brook on stepping stones no other wolf uses; quiet pride.",
    "Wind shifts; you catch **elk** sign a day old. Worth reporting to scouts.",
    "A fox den, long abandoned; you pull a **clean bone** from the midden.",
    "Thunderhead on the horizon; you turn back before the sky opens.",
]

EXPLORE_FAIL_FLAVOR = [
    "the trail doubles back on itself until you give up.",
    "something large moved uphill; you decide not to follow alone.",
    "Rain-soft ground swallows your scent; the venture yields nothing.",
    "A rival's mark on a stump tells you to range elsewhere today.",
]


def _explore_field_hazard(user, action: str, *, scale: float = 1.0) -> str:
    from engine.disease_contract import (
        try_insect_sting_exposure,
        try_poison_ivy_exposure,
        try_snake_venom_exposure,
    )

    if action == "dig":
        return try_insect_sting_exposure(user, chance=0.10 * scale) or ""
    if action == "follow":
        return try_snake_venom_exposure(user, chance=0.07 * scale) or ""
    if action == "investigate":
        return try_poison_ivy_exposure(user, chance=0.08 * scale) or ""
    return ""


def _maybe_explore_side_event(user, discord_id: int) -> str:
    import database as db

    if random.random() > 0.28:
        return ""
    line = random.choice(EXPLORE_SIDE_FINDS)
    if "+2 mood" in line:
        db.adjust_mood(user["id"], 2)
    elif "clean bone" in line.lower():
        extra = random.randint(2, 6)
        db.add_bones(discord_id, extra, wolf_id=user["id"])
        line += f" (+{extra} 🦴)"
    return f"\n\n_{line}_"


def _pick_loot(table: tuple) -> str:
    keys, weights = zip(*table)
    return random.choices(keys, weights=weights, k=1)[0]


def _biome_loot_extra(user) -> tuple[tuple[str, int], ...]:
    gp = user["great_pack"] if user and "great_pack" in user.keys() else None
    if gp in ("mistmoor", "silverrush"):
        return (("frog", 10), ("snake", 4))
    if gp == "thistlehide":
        return (("lizard", 8),)
    return ()


def _pick_loot_for_user(user, table: tuple) -> str:
    extra = _biome_loot_extra(user)
    if not extra:
        return _pick_loot(table)
    merged = list(table) + list(extra)
    return _pick_loot(tuple(merged))


def _grant_loot(
    wolf_id: int,
    *,
    guild_id: int,
    day: int,
    loot_key: str,
    discord_id: int,
) -> str:
    import database as db

    if loot_key == "bones":
        amount = random.randint(3, 12)
        db.add_bones(discord_id, amount, wolf_id=wolf_id)
        return f"+{amount} 🦴 bones"
    if loot_key == "herb":
        from herbs import HERBS

        pool = [
            k
            for k, m in HERBS.items()
            if m["rarity"] == "common"
            and not m.get("poison")
            and "wild" in m.get("habitat", ("wild",))
        ]
        herb_key = random.choice(pool) if pool else random.choice(list(HERBS.keys()))
        from herbs import herb_inventory_key

        item = db.get_item_by_key(herb_inventory_key(herb_key))
        if item:
            db.grant_item(discord_id, item["id"])
            return f"**{HERBS[herb_key]['name']}** (herb)"
    if loot_key in ("vole", "hare", "fish", "grouse", "frog", "snake", "lizard"):
        grant_prey_carcass(
            wolf_id,
            loot_key,
            guild_id=guild_id,
            acquired_day=day,
        )
        from engine.prey_items import prey_meta

        return f"**{prey_meta(loot_key)['name']}**"
    toy_key = loot_key
    if loot_key in ("shiny_pebble", "moth_wing", "crow_feather"):
        toy_key = random.choice(("bone", "feather", "stick"))
    grant_amusement(wolf_id, toy_key)
    return f"**{amusement_meta(toy_key)['name']}** ({amusement_meta(toy_key)['uses']} uses)"


def try_explore(
    interaction,
    action: str,
) -> tuple[discord.Embed | None, int | None]:
    import database as db
    from engine.character import parse_proficiencies

    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR), None
    if not interaction.guild:
        return howlbert_embed("server only", "explore in a server channel.", color=ERROR_COLOR), None

    from engine.injury_effects import strenuous_activity_blocked_by_injury
    from engine.vitals import full_activity_block

    inj = strenuous_activity_blocked_by_injury(user)
    if inj:
        return howlbert_embed("too injured", inj, color=ERROR_COLOR), None

    world = db.get_world(interaction.guild.id)
    day = world["day_number"]
    block = full_activity_block(user, day, action="explore")
    if block:
        return howlbert_embed("cannot explore", block, color=ERROR_COLOR), None

    spec = EXPLORE_ACTIONS.get(action)
    if not spec:
        return howlbert_embed("unknown action", "pick dig, follow, or investigate.", color=ERROR_COLOR), None
    from engine.role_privileges import is_scout

    from engine.diminishing import use_count_today
    # scouts range unlimited; everyone else faces a climbing dc on repeat
    # explores in one sunrise, instead of a hard once-per-sunrise block.
    explore_repeat = 0 if is_scout(user) else use_count_today(user, "explore", day)

    from engine.wild_encounters import ambush_embed, maybe_start_activity_ambush

    ambush = maybe_start_activity_ambush(
        user,
        guild_id=interaction.guild.id,
        channel_id=interaction.channel_id,
        activity="explore",
    )
    if ambush:
        enc_id, template_key, flavor = ambush
        embed = ambush_embed(template_key, flavor, user, activity="explore")
        from config import EXPLORE_WILD_ENCOUNTER_CHANCE

        embed.set_footer(
            text=f"~{EXPLORE_WILD_ENCOUNTER_CHANCE}% ambush · win to finish explore · flee and you keep today's venture"
        )
        return embed, enc_id

    from engine.diminishing import record_use

    record_use(user, "explore", day)

    profs = parse_proficiencies(user["skill_proficiencies"])
    skill_key = spec["skill"].lower()
    from config import SCOUT_EXPLORE_DC_BONUS

    explore_dc = max(5, spec["dc"] - (SCOUT_EXPLORE_DC_BONUS if is_scout(user) else 0) + 3 * explore_repeat)
    result = resolve_check(
        user,
        attr_keys=spec["attrs"],
        skill=spec["skill"],
        dc=explore_dc,
        proficient=skill_key in profs,
        skill_key=skill_key,
        game_day=day,
    )

    db.update_user(interaction.user.id, last_explore_day=day)
    from engine.activity_exhaustion import apply_activity_fatigue, append_fatigue_to_footer

    explore_fatigue = apply_activity_fatigue(
        db.get_user(interaction.user.id), "explore", skill_key, day
    )

    pack_key = user["great_pack"] if "great_pack" in user.keys() and user["great_pack"] else "loner"
    biome = BIOME_FLAVOR.get(pack_key, BIOME_FLAVOR["loner"])

    if result["outcome"] == "critical_failure":
        db.adjust_mood(user["id"], -5)
        from engine.disease_contract import try_den_filth_exposure

        filth_note = ""
        filth = try_den_filth_exposure(user)
        if filth:
            filth_note = f"\n\n{filth}"
        hazard_note = _explore_field_hazard(user, action, scale=0.65)
        embed = howlbert_embed(
            f"{spec['emoji']} explore: {spec['label']}",
            format_roll_result(result)
            + f"\n\n{spec['flavor']}\n_biome: {biome}_\n\n"
            "**Critical failure**; you startle prey, twist a paw, or lose the trail. **−5 mood.**"
            + filth_note
            + (f"\n\n{hazard_note}" if hazard_note else ""),
            color=ERROR_COLOR,
        )
        embed.set_footer(text="repeats today cost a higher dc · `/playpen` · `/food`")
        append_fatigue_to_footer(embed, explore_fatigue)
        return embed, None

    if not result["success"]:
        fail_extra = ""
        if random.random() < 0.35:
            fail_extra = f"\n\n_{random.choice(EXPLORE_FAIL_FLAVOR)}_"
        hazard_note = _explore_field_hazard(user, action, scale=0.45)
        embed = howlbert_embed(
            f"{spec['emoji']} explore: {spec['label']}",
            format_roll_result(result)
            + f"\n\n{spec['flavor']}\n_biome: {biome}_\n\nnothing useful today.{fail_extra}"
            + (f"\n\n{hazard_note}" if hazard_note else ""),
            color=ERROR_COLOR,
        )
        embed.set_footer(text="repeats today cost a higher dc · hazards still find you in the brush")
        append_fatigue_to_footer(embed, explore_fatigue)
        return embed, None

    table = {"dig": DIG_LOOT, "follow": FOLLOW_LOOT, "investigate": INVESTIGATE_LOOT}[action]
    loot_key = _pick_loot_for_user(user, table)
    if result["outcome"] == "critical_success":
        loot_key2 = _pick_loot_for_user(user, table)
        reward = _grant_loot(
            user["id"],
            guild_id=interaction.guild.id,
            day=day,
            loot_key=loot_key,
            discord_id=interaction.user.id,
        )
        reward2 = _grant_loot(
            user["id"],
            guild_id=interaction.guild.id,
            day=day,
            loot_key=loot_key2,
            discord_id=interaction.user.id,
        )
        loot_line = f"**double find!** {reward} and {reward2}"
    else:
        loot_line = _grant_loot(
            user["id"],
            guild_id=interaction.guild.id,
            day=day,
            loot_key=loot_key,
            discord_id=interaction.user.id,
        )
        loot_line = f"found: {loot_line}"

    side = _maybe_explore_side_event(user, interaction.user.id)
    mill_line = ""
    if action == "investigate":
        from engine.plot_blinking import try_plot_mill_investigate

        mill_line = try_plot_mill_investigate(
            user,
            guild_id=interaction.guild.id,
            day=day,
            success=True,
        )
    from engine.plot_blinking import try_plot_witness

    witness = try_plot_witness(user, interaction.guild.id, day, action="explore")
    db.increment_quest_progress(interaction.user.id, "explore", guild_id=interaction.guild.id)
    hazard_note = _explore_field_hazard(user, action)
    embed = howlbert_embed(
        f"{spec['emoji']} explore: {spec['label']}",
        format_roll_result(result)
        + f"\n\n{spec['flavor']}\n_biome: {biome}_\n\n{loot_line}{side}{mill_line}{witness}"
        + (f"\n\n{hazard_note}" if hazard_note else ""),
        color=SUCCESS_COLOR,
    )
    embed.set_footer(text="amusement: `/playpen` · carcasses: `/food` · salvage scraps: `/salvage`")
    if is_scout(user):
        from config import SCOUT_EXPLORE_DC_BONUS

        embed.set_footer(
            text=(
                f"scout; unlimited ventures · explore dc −{SCOUT_EXPLORE_DC_BONUS} · "
                f"/scout rescout · `/playpen` · /food"
            )
        )
    append_fatigue_to_footer(embed, explore_fatigue)
    return embed, None


RESCOUT_LOOT = (
    ("feather", 25),
    ("bone", 20),
    ("shell", 15),
    ("stick", 12),
    ("talon", 10),
    ("acorn", 10),
    ("hare", 5),
    ("bones", 8),
)

RESCOUT_CRIT_LOOT = (
    ("feather", 20),
    ("talon", 15),
    ("grouse", 15),
    ("fish", 15),
    ("hare", 15),
    ("shell", 10),
    ("bones", 10),
)


def _record_rescout_use(discord_id: int, day: int) -> int:
    import database as db

    user = db.get_user(discord_id)
    if not user:
        return 0
    if int(user["last_rescout_day"]) < day:
        uses = 1
    else:
        uses = int(user["rescout_uses_today"]) if "rescout_uses_today" in user.keys() else 0
        uses += 1
    db.update_user(discord_id, last_rescout_day=day, rescout_uses_today=uses)
    return uses


def try_rescout(interaction) -> discord.Embed | None:
    """repeat explore in the same biome; scout role only, mood and loot."""
    import database as db
    from config import RESCOUT_MOOD_GAIN, SCOUT_EXPLORE_DC_BONUS
    from engine.character import parse_proficiencies
    from engine.role_privileges import is_scout

    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    if not is_scout(user):
        return howlbert_embed(
            "scouts only",
            "only wolves with the **scout** role can rescout the biome. "
            "Hunters and others use **`/explore`** once per sunrise.",
            color=ERROR_COLOR,
        )
    if not interaction.guild:
        return howlbert_embed("server only", "explore in a server channel.", color=ERROR_COLOR)

    world = db.get_world(interaction.guild.id)
    day = world["day_number"]

    profs = parse_proficiencies(user["skill_proficiencies"])
    result = resolve_check(
        user,
        attr_keys=("attr_wis", "attr_dex"),
        skill="Survival",
        dc=8,
        proficient="survival" in profs or "tracking" in profs,
        skill_key="survival",
        game_day=day,
    )
    _record_rescout_use(interaction.user.id, day)
    from engine.activity_exhaustion import apply_activity_fatigue, append_fatigue_to_footer
    from engine.role_privileges import rescout_uses_today

    rescout_fatigue = apply_activity_fatigue(
        db.get_user(interaction.user.id),
        "rescout",
        "survival",
        day,
        activity_count=rescout_uses_today(db.get_user(interaction.user.id), day),
    )

    pack_key = user["great_pack"] if "great_pack" in user.keys() and user["great_pack"] else "loner"
    biome = BIOME_FLAVOR.get(pack_key, BIOME_FLAVOR["loner"])
    scout_footer = (
        f"scout; unlimited rescouts · explore dc −{SCOUT_EXPLORE_DC_BONUS} · `/playpen` · /food"
    )

    if result["outcome"] == "critical_failure":
        db.adjust_mood(user["id"], -3)
        embed = howlbert_embed(
            "🔁 rescout",
            format_roll_result(result)
            + f"\n\nyou double back through {biome}; a false trail and a stubbed paw. **−3 mood.**",
            color=ERROR_COLOR,
        )
        embed.set_footer(text=scout_footer)
        append_fatigue_to_footer(embed, rescout_fatigue)
        return embed

    if not result["success"]:
        embed = howlbert_embed(
            "🔁 rescout",
            format_roll_result(result)
            + f"\n\nyou pad the old trails through {biome} but find nothing new.",
            color=ERROR_COLOR,
        )
        embed.set_footer(text=scout_footer)
        append_fatigue_to_footer(embed, rescout_fatigue)
        return embed

    if result["outcome"] == "critical_success":
        loot_key = _pick_loot(RESCOUT_CRIT_LOOT)
        reward = _grant_loot(
            user["id"],
            guild_id=interaction.guild.id,
            day=day,
            loot_key=loot_key,
            discord_id=interaction.user.id,
        )
        loot_key2 = _pick_loot(RESCOUT_LOOT)
        reward2 = _grant_loot(
            user["id"],
            guild_id=interaction.guild.id,
            day=day,
            loot_key=loot_key2,
            discord_id=interaction.user.id,
        )
        new_mood = db.adjust_mood(user["id"], RESCOUT_MOOD_GAIN + 2)
        loot_line = f"**sharp eyes!** {reward} and {reward2} · mood **{new_mood}**"
    else:
        loot_key = _pick_loot(RESCOUT_LOOT)
        if random.random() < 0.4:
            reward = _grant_loot(
                user["id"],
                guild_id=interaction.guild.id,
                day=day,
                loot_key=loot_key,
                discord_id=interaction.user.id,
            )
            new_mood = db.adjust_mood(user["id"], RESCOUT_MOOD_GAIN)
            loot_line = f"found: {reward} · **+{RESCOUT_MOOD_GAIN} mood** (now **{new_mood}**)"
        else:
            new_mood = db.adjust_mood(user["id"], RESCOUT_MOOD_GAIN)
            loot_line = f"the land reads clear; **+{RESCOUT_MOOD_GAIN} mood** (now **{new_mood}**)"

    db.increment_quest_progress(interaction.user.id, "explore", guild_id=interaction.guild.id)
    embed = howlbert_embed(
        "🔁 rescout",
        format_roll_result(result) + f"\n\n_{biome}_\n\n{loot_line}",
        color=SUCCESS_COLOR,
    )
    embed.set_footer(text=scout_footer)
    append_fatigue_to_footer(embed, rescout_fatigue)
    return embed
