"""Sunrise ambience posts for designated RP channels."""

from __future__ import annotations

import logging
import random

import discord

from config import ROLLOVER_TIMEZONE
from engine.lunar import active_lunar_phase, rollover_now
from engine.world import season_label, time_label, weather_label
from utils.embeds import EMBED_COLOR, howlbert_embed

logger = logging.getLogger("howlbert")

_AMBIENCE_LINES = {
    "newgrowth": [
        "Mud-soft paths and new leaf-smell; the den wakes hungry for spring.",
        "Meltwater threads the stones; prey stirs in the thaw.",
    ],
    "highsun": [
        "Heat-haze over the ridges; shade is worth more than gossip today.",
        "Cicada-dry air; even the wind sounds tired.",
    ],
    "leaf_drop": [
        "Copper leaves skitter across the trail; the wind tastes of rain.",
        "First frost whispers at dawn; fur thickens overnight.",
    ],
    "leaf_bare": [
        "Bare branches click like teeth; breath ghosts in the cold.",
        "Ice crusts the creek edges; hunger walks closer than kin.",
    ],
}


def build_ambience_embed(world) -> discord.Embed:
    season = world["season"]
    weather = world["weather"]
    tod = world["time_of_day"]
    day = world["day_number"]
    moon = active_lunar_phase(rollover_now(ROLLOVER_TIMEZONE))
    flavor = random.choice(_AMBIENCE_LINES.get(season, _AMBIENCE_LINES["newgrowth"]))
    body = (
        f"**day {day}** · {season_label(season)} · {weather_label(weather)} · "
        f"{time_label(tod)} · {moon}\n\n{flavor}"
    )
    return howlbert_embed("🌅 sunrise over the territory", body, color=EMBED_COLOR)


async def post_rp_ambience(bot, guild_id: int, world) -> None:
    from config import RP_AMBIENCE_CHANNEL_IDS

    if not RP_AMBIENCE_CHANNEL_IDS:
        return
    guild = bot.get_guild(guild_id)
    if not guild:
        return
    embed = build_ambience_embed(world)
    for ch_id in RP_AMBIENCE_CHANNEL_IDS:
        channel = guild.get_channel(ch_id)
        if not isinstance(channel, discord.TextChannel):
            continue
        perms = channel.permissions_for(guild.me)
        if not perms.send_messages:
            continue
        try:
            await channel.send(embed=embed)
        except discord.HTTPException as exc:
            logger.warning("RP ambience post failed in %s: %s", ch_id, exc)
