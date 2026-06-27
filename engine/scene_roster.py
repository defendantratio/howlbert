"""Pinned living roster for RP scene threads."""

from __future__ import annotations

import logging

import discord

import database as db
from utils.embeds import SUCCESS_COLOR, howlbert_embed

logger = logging.getLogger("howlbert")


def build_roster_embed(scene, members) -> discord.Embed:
    if members:
        roster = "\n".join(
            f"• **{m['wolf_name']}** (<@{m['discord_id']}>)" for m in members
        )
    else:
        roster = "_No wolves present yet — post or `/scene join` to enter._"
    embed = howlbert_embed(f"🎬 {scene['name']}", roster, color=SUCCESS_COLOR)
    if scene["topic"]:
        embed.add_field(name="topic", value=scene["topic"], inline=False)
    embed.set_footer(text=f"{len(members)} present · auto-join on post · /scene poke")
    return embed


async def refresh_scene_roster(bot, scene) -> None:
    """edit the pinned roster message, or create one if missing."""
    if scene["status"] != "open":
        return
    thread = bot.get_channel(int(scene["thread_id"]))
    if not isinstance(thread, discord.Thread):
        return
    members = db.get_scene_members(scene["id"])
    embed = build_roster_embed(scene, members)
    msg_id = scene["roster_message_id"] if "roster_message_id" in scene.keys() else None
    if msg_id:
        try:
            msg = await thread.fetch_message(int(msg_id))
            await msg.edit(embed=embed)
            return
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass
    try:
        msg = await thread.send(embed=embed)
        await msg.pin()
        db.set_scene_roster_message_id(scene["id"], msg.id)
    except (discord.Forbidden, discord.HTTPException):
        logger.info("Could not pin scene roster in thread %s", thread.id)
