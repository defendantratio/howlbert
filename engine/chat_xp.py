"""Server chat activity: +1 XP once per game day."""

from __future__ import annotations

import discord

import database as db

CHAT_XP_PER_SUNRISE = 1


def chat_xp_claimed_today(discord_id: int, guild_id: int, day: int) -> bool:
    """True when the daily chat XP cap for this den is already claimed."""
    if day <= 0:
        return True
    with db.get_db() as conn:
        row = conn.execute(
            """
            SELECT last_claim_day FROM chat_xp_claims
            WHERE discord_id = ? AND guild_id = ?
            """,
            (discord_id, guild_id),
        ).fetchone()
        return bool(row and row["last_claim_day"] >= day)


def format_chat_xp_status(discord_id: int, guild_id: int, day: int) -> str:
    """Player-facing line for profile or cooldown hints."""
    if chat_xp_claimed_today(discord_id, guild_id, day):
        return f"chat xp claimed (+{CHAT_XP_PER_SUNRISE} account xp this sunrise)"
    return f"chat xp unclaimed (+{CHAT_XP_PER_SUNRISE} on your next message)"


def try_chat_message_xp(message: discord.Message) -> bool:
    """Award +1 XP on the first qualifying message each sunrise. Returns True if granted."""
    if message.author.bot or not message.guild:
        return False
    if message.type not in (discord.MessageType.default, discord.MessageType.reply):
        return False
    if len(message.content.strip()) < 2:
        return False

    day = db.get_world(message.guild.id)["day_number"]
    return db.try_grant_chat_xp(message.author.id, message.guild.id, day)
