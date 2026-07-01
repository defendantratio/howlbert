"""Scout-only field work; survey borders and follow cold trails."""

from __future__ import annotations

import random

import discord

import database as db
from config import SCOUT_SURVEY_BONES, SCOUT_TRAIL_BONES
from engine.character import parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from engine.injury_effects import strenuous_activity_blocked_by_injury
from engine.vitals import full_activity_block
from engine.prey_storage import grant_prey_carcass
from engine.role_privileges import is_scout
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed

SURVEY_FLAVOR = [
    "you ghost along the ridge line, reading wind and distant movement.",
    "from a high ledge you map fresh sign without showing your silhouette.",
    "You circle the den's edge twice; counting tracks, not making any.",
]

TRAIL_FLAVOR = [
    "a thread of scent peels off the main game trail; you commit to it.",
    "old scratch-marks on bark lead you deeper than most wolves wander.",
    "You find where prey watered yesterday and follow the spoor uphill.",
    "A cold rivulet cuts the trail; you wade it and pick up sign on the far bank.",
    "Raven chatter marks a kill site; you circle wide and read what's left.",
]

SURVEY_INTEL = [
    "You note **fresh elk** sign on the eastern ridge.",
    "A loner scent crosses the border and fades south; worth a howl report.",
    "Smoke on the horizon; probably a human camp, not a den fire.",
    "The river ford is muddy; prey will avoid it until the next rain.",
    "You spot raccoon activity near the stash trees; den guards should watch `/pack stash`.",
]

TRAIL_INTEL = [
    "The spoor leads to a **vole warren**; easy pickings if you're quick.",
    "You find where a hare doubled back; patience pays off.",
    "Fish scales glint in a backwater; something fed here at dawn.",
    "Grouse feathers scatter under a pine; a hawk's kill, but scraps remain.",
    "Old wolf sign overlays newer deer track; rivals passed through.",
]

TRAIL_PREY = (
    ("vole", 25),
    ("rabbit", 25),
    ("hare", 20),
    ("fish", 10),
    ("grouse", 10),
    ("bones", 10),
)


def _scout_only(user) -> discord.Embed | None:
    if not is_scout(user):
        return howlbert_embed(
            "scouts only",
            "only wolves with the **scout** role can run field commands. "
            "Apprentices earn the title through the den (`/role action:event`, age-up).",
            color=ERROR_COLOR,
        )
    return None


def try_scout_survey(interaction) -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    block = _scout_only(user)
    if block:
        return block
    inj = strenuous_activity_blocked_by_injury(user)
    if inj:
        return howlbert_embed("too injured", inj, color=ERROR_COLOR)
    if not interaction.guild:
        return howlbert_embed("server only", "use this in a server channel.", color=ERROR_COLOR)

    world = db.get_world(interaction.guild.id)
    day = world["day_number"]
    vitals_block = full_activity_block(user, day, action="survey")
    if vitals_block:
        return howlbert_embed("cannot survey", vitals_block, color=ERROR_COLOR)
    profs = parse_proficiencies(user["skill_proficiencies"])
    from engine.pack_raid_ecology import survey_dc_modifiers, survey_victim_bone_bonus

    dc_mod, dc_note = survey_dc_modifiers(user, interaction.guild.id, day)
    from engine.moon_phase import new_moon_stealth_dc_mod

    moon_dc_mod = new_moon_stealth_dc_mod()
    if moon_dc_mod:
        dc_mod += moon_dc_mod
        dc_note = f"{dc_note} new moon; no light to give you away." if dc_note else "new moon; no light to give you away."
    result = resolve_check(
        user,
        attr_keys=("attr_wis", "attr_dex"),
        skill="Stealth",
        dc=11 + dc_mod,
        proficient="stealth" in profs or "tracking" in profs,
        skill_key="stealth",
        game_day=day,
    )
    db.update_user(interaction.user.id, last_survey_day=day)
    from engine.activity_exhaustion import apply_activity_fatigue, append_fatigue_to_footer

    survey_fatigue = apply_activity_fatigue(db.get_user(interaction.user.id), "survey", "stealth", day)

    from engine.role_features import scout_hide_after_check

    hide_note = scout_hide_after_check(
        user,
        weather_key=world["weather"],
        day=day,
        skill_key="stealth",
        success=result["success"],
    )

    if result["outcome"] == "critical_failure":
        db.adjust_wolf_standing(interaction.user.id, -1)
        embed = howlbert_embed(
            "🗺️ survey",
            format_roll_result(result)
            + "\n\n"
            + random.choice(SURVEY_FLAVOR)
            + "\n\nYou were **spotted** on the ridge; standing **−1**.",
            color=ERROR_COLOR,
        )
        embed.set_footer(text="survey spent · `/scout trail` · /checklist")
        append_fatigue_to_footer(embed, survey_fatigue)
        return embed

    if not result["success"]:
        plague_note = ""
        from engine.disease_contract import try_sick_traveler_exposure

        plague = try_sick_traveler_exposure(user)
        if plague:
            plague_note = f"\n\n{plague}"
        embed = howlbert_embed(
            "🗺️ survey",
            format_roll_result(result)
            + "\n\n"
            + random.choice(SURVEY_FLAVOR)
            + "\n\nThe border stays quiet; nothing worth reporting."
            + plague_note,
            color=ERROR_COLOR,
        )
        embed.set_footer(text="survey spent · `/scout rescout` · /checklist")
        append_fatigue_to_footer(embed, survey_fatigue)
        return embed

    bones = random.randint(*SCOUT_SURVEY_BONES)
    if result["outcome"] == "critical_success":
        bones += 8
    bones += survey_victim_bone_bonus(user, interaction.guild.id, day)
    db.add_bones(interaction.user.id, bones, wolf_id=user["id"])
    standing = 2 if result["outcome"] == "critical_success" else 1
    from engine.plot_blinking import plot_thistlehide_patrol_standing_bonus

    gp = user["great_pack"] if "great_pack" in user.keys() else None
    standing += plot_thistlehide_patrol_standing_bonus(interaction.guild.id, gp, user=user)
    db.adjust_wolf_standing(interaction.user.id, standing)
    db.increment_quest_progress(interaction.user.id, "survey", guild_id=interaction.guild.id)
    db.increment_quest_progress(interaction.user.id, "patrol", guild_id=interaction.guild.id)

    crit = " **Critical report!**" if result["outcome"] == "critical_success" else ""
    intel = ""
    if random.random() < (0.5 if result["outcome"] == "critical_success" else 0.3):
        intel = f"\n_{random.choice(SURVEY_INTEL)}_"
    from engine.plot_blinking import try_plot_witness
    from engine.role_shift_bonus import apply_first_survey_bonus

    witness = try_plot_witness(user, interaction.guild.id, day, action="survey")
    shift_note = apply_first_survey_bonus(user) or ""
    extra = ""
    if dc_note:
        extra += f"\n_{dc_note}_"
    if shift_note:
        extra += f"\n_{shift_note}_"
    if witness:
        extra += witness
    embed = howlbert_embed(
        "🗺️ survey",
        format_roll_result(result)
        + "\n\n"
        + random.choice(SURVEY_FLAVOR)
        + f"\n\n{crit} intel for the alpha; **+{bones}** bones, standing **+{standing}**.{intel}{hide_note}{extra}",
        color=SUCCESS_COLOR,
    )
    embed.set_footer(text="scouts · unlimited · counts toward survey & patrol quests")
    append_fatigue_to_footer(embed, survey_fatigue)
    return embed


def try_scout_trail(interaction) -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    block = _scout_only(user)
    if block:
        return block
    inj = strenuous_activity_blocked_by_injury(user)
    if inj:
        return howlbert_embed("too injured", inj, color=ERROR_COLOR)
    if not interaction.guild:
        return howlbert_embed("server only", "use this in a server channel.", color=ERROR_COLOR)

    world = db.get_world(interaction.guild.id)
    day = world["day_number"]
    vitals_block = full_activity_block(user, day, action="trail")
    if vitals_block:
        return howlbert_embed("cannot trail", vitals_block, color=ERROR_COLOR)
    profs = parse_proficiencies(user["skill_proficiencies"])
    result = resolve_check(
        user,
        attr_keys=("attr_wis", "attr_int"),
        skill="Tracking",
        dc=12,
        proficient="tracking" in profs,
        skill_key="tracking",
        game_day=day,
    )
    db.update_user(interaction.user.id, last_trail_day=day)
    from engine.activity_exhaustion import apply_activity_fatigue, append_fatigue_to_footer

    trail_fatigue = apply_activity_fatigue(db.get_user(interaction.user.id), "trail", "tracking", day)

    if result["outcome"] == "critical_failure":
        db.adjust_mood(user["id"], -2)
        embed = howlbert_embed(
            "👣 trail",
            format_roll_result(result)
            + "\n\n"
            + random.choice(TRAIL_FLAVOR)
            + "\n\nThe spoor vanishes in bog-water; **−2 mood**.",
            color=ERROR_COLOR,
        )
        embed.set_footer(text="trail spent · `/scout survey` · /checklist")
        append_fatigue_to_footer(embed, trail_fatigue)
        return embed

    if not result["success"]:
        hazard_note = ""
        from engine.disease_contract import try_snake_venom_exposure

        hazard = try_snake_venom_exposure(user, chance=0.06)
        if hazard:
            hazard_note = f"\n\n{hazard}"
        embed = howlbert_embed(
            "👣 trail",
            format_roll_result(result)
            + "\n\n"
            + random.choice(TRAIL_FLAVOR)
            + "\n\nThe trail goes cold."
            + hazard_note,
            color=ERROR_COLOR,
        )
        embed.set_footer(text="try again · `/scout rescout` · /checklist")
        append_fatigue_to_footer(embed, trail_fatigue)
        return embed

    bones = random.randint(*SCOUT_TRAIL_BONES)
    if result["outcome"] == "critical_success":
        bones += 10
    db.add_bones(interaction.user.id, bones, wolf_id=user["id"])
    db.increment_quest_progress(interaction.user.id, "trail")

    prey_line = ""
    if result["success"] and random.random() < (0.55 if result["outcome"] == "critical_success" else 0.35):
        keys, weights = zip(*TRAIL_PREY)
        loot = random.choices(keys, weights=weights, k=1)[0]
        if loot == "bones":
            extra = random.randint(4, 10)
            db.add_bones(interaction.user.id, extra, wolf_id=user["id"])
            prey_line = f"\n**sign cache**; +{extra} bones tucked under stone."
        else:
            grant_prey_carcass(
                user["id"],
                loot,
                guild_id=interaction.guild.id,
                acquired_day=day,
            )
            from engine.prey_items import prey_meta

            prey_line = f"\n**caught up**; **{prey_meta(loot)['name']}** in hoard (`/food`)."

    crit = " **Perfect read!**" if result["outcome"] == "critical_success" else ""
    intel = ""
    if random.random() < (0.45 if result["outcome"] == "critical_success" else 0.25):
        intel = f"\n_{random.choice(TRAIL_INTEL)}_"
    embed = howlbert_embed(
        "👣 trail",
        format_roll_result(result)
        + "\n\n"
        + random.choice(TRAIL_FLAVOR)
        + f"\n\n{crit} **+{bones}** bones.{prey_line}{intel}",
        color=SUCCESS_COLOR,
    )
    embed.set_footer(text="scouts · unlimited · counts toward trail quests")
    append_fatigue_to_footer(embed, trail_fatigue)
    return embed
