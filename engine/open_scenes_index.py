"""Live index of currently-open /scene threads, posted to a dedicated
channel (see docs/GROWTH_IDEAS.md section 45, "#open-scenes"). One message
per guild, edited in place as scenes open, gain/lose members, or close."""

from __future__ import annotations

import logging

import discord

import database as db
from config import OPEN_SCENES_CHANNEL_ID
from utils.embeds import SUCCESS_COLOR, howlbert_embed

logger = logging.getLogger("howlbert")


def build_open_scenes_embed(guild_id: int) -> discord.Embed:
    scenes = db.list_open_scenes(guild_id)
    if not scenes:
        body = "_No open scenes right now; `/scene start` to open one._"
    else:
        lines = []
        for scene in scenes:
            members = db.get_scene_members(scene["id"])
            cast = ", ".join(m["wolf_name"] for m in members) or "_empty_"
            lines.append(f"• <#{scene['thread_id']}> — {cast}")
        body = "\n".join(lines)
    embed = howlbert_embed("🎬 Open Scenes", body, color=SUCCESS_COLOR)
    embed.set_footer(text="updates automatically · /scene start to open one")
    return embed


async def refresh_open_scenes_index(bot, guild_id: int) -> None:
    if not OPEN_SCENES_CHANNEL_ID:
        logger.info("OPEN_SCENES_CHANNEL_ID is not set; skipping open-scenes index refresh.")
        return
    channel = bot.get_channel(OPEN_SCENES_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(OPEN_SCENES_CHANNEL_ID)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            logger.warning(
                "OPEN_SCENES_CHANNEL_ID=%s could not be fetched; check the id and that the bot can see it.",
                OPEN_SCENES_CHANNEL_ID,
            )
            return
    if not isinstance(channel, discord.TextChannel):
        logger.warning(
            "OPEN_SCENES_CHANNEL_ID=%s is not a text channel (got %s); open-scenes index needs a plain text channel.",
            OPEN_SCENES_CHANNEL_ID,
            type(channel).__name__,
        )
        return
    embed = build_open_scenes_embed(guild_id)
    msg_id = db.get_open_scenes_index_message_id(guild_id)
    if msg_id:
        try:
            msg = await channel.fetch_message(msg_id)
            await msg.edit(embed=embed)
            return
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass
    try:
        msg = await channel.send(embed=embed)
        db.set_open_scenes_index_message_id(guild_id, msg.id)
    except (discord.Forbidden, discord.HTTPException) as exc:
        logger.warning("Could not post open-scenes index in guild %s: %s", guild_id, exc)
