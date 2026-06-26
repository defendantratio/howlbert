"""Sniff the wind; hunt/track bonus, wolf encounters, and border cat fights."""

from __future__ import annotations

import random

import discord

from config import (
    GREAT_PACKS,
    SNIFF_CAT_ENCOUNTER_CHANCE,
    SNIFF_HUNT_BONUS_PCT,
    SNIFF_HUNT_HINT_CHANCE,
    SNIFF_WOLF_ENCOUNTER_CHANCE,
    SNIFF_WOLF_ENCOUNTER_MOOD,
)
from engine.cat_pacts import pact_border_chance_multiplier
from engine.prey_items import SNIFF_FLAVORS, SNIFF_HUNT_HINT
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed


SNIFF_ENCOUNTER_PACKMATE = (
    "You catch **{name}** on the same ridge; they step out of the pines, ears forward, tail low.",
    "**{name}** is already here, nose in the same trail you were reading.",
    "A familiar scent; **{name}** rounds the boulder and gives a quick nose-bump.",
)

SNIFF_ENCOUNTER_FACTION = (
    "A **{pack}** wolf; **{name}**; watches from the treeline before padding closer.",
    "Scent marks say **{pack}** territory. **{name}** appears on the trail, cautious but curious.",
    "**{name}** of **{pack}** crosses your path; neither of you expected company this early.",
)

SNIFF_ENCOUNTER_STRANGER = (
    "An unfamiliar wolf; **{name}**; freezes when you both read the same trail.",
    "A stranger's mark on the wind: **{name}** slips out of the brush, wary.",
    "**{name}** is here too, nose to the ground. You lock eyes, then relax.",
)


def sniff_bonus_active(user, day: int) -> bool:
    bonus_day = int(user["sniff_bonus_day"]) if "sniff_bonus_day" in user.keys() else 0
    return bonus_day >= day


def apply_sniff_bone_bonus(user, amount: int, day: int) -> tuple[int, int, str]:
    """Return (new_amount, bonus_added, footer_note)."""
    if amount <= 0 or not sniff_bonus_active(user, day):
        return amount, 0, ""
    bonus = max(1, int(amount * SNIFF_HUNT_BONUS_PCT / 100))
    note = f"Sniff bonus; **+{SNIFF_HUNT_BONUS_PCT}%** hunt/track payout."
    return amount + bonus, bonus, note


def sniff_track_fail_reduction(user, day: int) -> int:
    """Points subtracted from tracking DC when sniff bonus is active."""
    if not sniff_bonus_active(user, day):
        return 0
    return max(5, int(SNIFF_HUNT_BONUS_PCT / 2))


def _encounter_flavor(user, other) -> str:
    name = other["wolf_name"]
    if user["pack_id"] and user["pack_id"] == other["pack_id"]:
        return random.choice(SNIFF_ENCOUNTER_PACKMATE).format(name=name)
    gp = other["great_pack"] if "great_pack" in other.keys() and other["great_pack"] else None
    if gp and gp in GREAT_PACKS:
        pack = GREAT_PACKS[gp]["name"]
        return random.choice(SNIFF_ENCOUNTER_FACTION).format(name=name, pack=pack)
    return random.choice(SNIFF_ENCOUNTER_STRANGER).format(name=name)


def try_sniff(interaction) -> tuple[discord.Embed, int | None]:
    """
    Sniff the wind once per sunrise.
    Returns (embed, border_combat_encounter_id or None).
    """
    import database as db

    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("Not Registered", "Use `/register` first."), None
    if not interaction.guild:
        return howlbert_embed("Server Only", "Use this in a server."), None

    world = db.get_world(interaction.guild.id)
    day = world["day_number"]
    if int(user["last_sniff_day"]) >= day:
        embed = howlbert_embed("Already Sniffed", "You've read the wind this sunrise.", color=ERROR_COLOR)
        embed.set_footer(text="Resets at next `/rollover` · `/world action:cooldowns`")
        return embed, None

    db.update_user(interaction.user.id, last_sniff_day=day)
    flavor = random.choice(SNIFF_FLAVORS)
    body = flavor
    footer_bits: list[str] = [f"Season: {world['season']} · {world['weather']}"]
    combat_enc_id: int | None = None

    gp = user["great_pack"] if "great_pack" in user.keys() and user["great_pack"] else None
    if gp and gp in GREAT_PACKS:
        from engine.territory_marking import read_marks_for_sniff

        marks = read_marks_for_sniff(gp, guild_id=interaction.guild.id, day=day)
        if marks:
            body += "\n\n**Scent marks on the wind:**\n" + "\n".join(f"· {m}" for m in marks[:4])
            footer_bits.append("Border marks")

    encounter = None
    if random.random() < SNIFF_WOLF_ENCOUNTER_CHANCE:
        encounter = db.pick_sniff_encounter_wolf(
            exclude_wolf_id=user["id"],
            exclude_discord_id=interaction.user.id,
            pack_id=user["pack_id"],
            great_pack=gp,
        )

    if encounter:
        from engine.pack_relations import sniff_encounter_lines

        relation_body, skirmish_id = sniff_encounter_lines(
            user,
            encounter,
            guild_id=interaction.guild.id,
            channel_id=interaction.channel_id,
        )
        if relation_body:
            body += relation_body
            if skirmish_id:
                combat_enc_id = skirmish_id
                footer_bits.append("Hostile rival; combat panel below")
        else:
            body += f"\n\n{_encounter_flavor(user, encounter)}"
            new_mood = db.adjust_mood(user["id"], SNIFF_WOLF_ENCOUNTER_MOOD)
            body += f"\n\n**+{SNIFF_WOLF_ENCOUNTER_MOOD} mood** (now **{new_mood}**)."
            if user["pack_id"] and user["pack_id"] == encounter["pack_id"]:
                body += (
                    "\nPackmate on the trail; try **`/playpen action:socialize`** "
                    "if you haven't mingled today."
                )
        footer_bits.append("Wolf encounter")
    else:
        border_odds = SNIFF_CAT_ENCOUNTER_CHANCE * pact_border_chance_multiplier(
            interaction.guild.id, user["pack_id"]
        )
        from engine.plot_blinking import plot_sniff_border_mult

        border_odds *= plot_sniff_border_mult(interaction.guild.id)
        if (
            border_odds > 0
            and random.random() < border_odds
        ):
            from engine.border_combat import start_border_cat_fight
            from engine.cat_clans import sniff_cat_scent_line
            from engine.cat_pacts import pick_border_cat_for_pack

            border_pick = pick_border_cat_for_pack(interaction.guild.id, user["pack_id"])
            _template, border_clan, violation = border_pick
            if violation:
                scent = sniff_cat_scent_line(allied_clan=border_clan, allied_patrol=True)
            else:
                scent = sniff_cat_scent_line(rival_clan=border_clan)
            body += f"\n\n_{scent}_"
            enc_id, _template, fight_flavor = start_border_cat_fight(
                user,
                guild_id=interaction.guild.id,
                channel_id=interaction.channel_id,
                pick=border_pick,
            )
            body += f"\n\n{fight_flavor}"
            combat_enc_id = enc_id
            footer_bits.append("Border fight; use the combat panel")

    if random.random() < SNIFF_HUNT_HINT_CHANCE:
        db.update_user(interaction.user.id, sniff_bonus_day=day)
        body += (
            f"\n\n_{random.choice(SNIFF_HUNT_HINT)}_\n"
            f"**+{SNIFF_HUNT_BONUS_PCT}%** on **hunt** and **track** payouts this sunrise."
        )
        footer_bits.append(f"Sniff bonus active (+{SNIFF_HUNT_BONUS_PCT}%)")

    from engine.role_features import try_scout_hide_in_weather

    hide_note = try_scout_hide_in_weather(user, weather_key=world["weather"], day=day)
    if hide_note:
        body += f"\n\n_{hide_note}_"
        footer_bits.append("Unseen Paw active")

    from engine.restricted_herbs import try_catch_hoarder_on_sniff

    hoard_caught = try_catch_hoarder_on_sniff(user)
    if hoard_caught:
        body += f"\n\n{hoard_caught}"
        footer_bits.append("Poison herbs seized")

    from engine.plot_blinking import try_plot_sniff_extras

    body += try_plot_sniff_extras(user, interaction.guild.id, day=day)

    from engine.whispering_wild import spirit_whisper_on_sniff

    whisper = spirit_whisper_on_sniff(user, weather=world["weather"])
    if whisper:
        body += f"\n\n{whisper}"
        footer_bits.append("Spirit whisper")

    embed = howlbert_embed("On the Wind", body, color=SUCCESS_COLOR)
    embed.set_footer(text=" · ".join(footer_bits))
    return embed, combat_enc_id
