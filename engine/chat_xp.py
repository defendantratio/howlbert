"""Server chat activity: +1 XP once per game day."""

from __future__ import annotations

import discord

import database as db


def try_chat_message_xp(message: discord.Message) -> bool:
    """Award +1 XP on the first qualifying message each sunrise. Returns True if granted."""
    if message.author.bot or not message.guild:
        return False
    if message.type not in (discord.MessageType.default, discord.MessageType.reply):
        return False

    day = db.get_world(message.guild.id)["day_number"]
    return db.try_grant_chat_xp(message.author.id, message.guild.id, day)
