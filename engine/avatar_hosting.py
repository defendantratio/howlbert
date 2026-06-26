"""Upload cropped avatars to Discord's CDN for webhook use."""

from __future__ import annotations

import io
import logging

import discord
from discord.ext import commands

from config import AVATAR_CACHE_CHANNEL_ID

logger = logging.getLogger("howlbert")


async def resolve_avatar_cache_channel(
    bot: commands.Bot, guild: discord.Guild
) -> discord.TextChannel | None:
    if AVATAR_CACHE_CHANNEL_ID:
        ch = bot.get_channel(AVATAR_CACHE_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            return ch
        try:
            fetched = await bot.fetch_channel(AVATAR_CACHE_CHANNEL_ID)
            if isinstance(fetched, discord.TextChannel):
                return fetched
        except discord.HTTPException:
            pass

    for channel in guild.text_channels:
        if channel.name == "howlbert-avatars" and channel.permissions_for(guild.me).send_messages:
            return channel
    return None


async def host_avatar_bytes(
    bot: commands.Bot,
    guild: discord.Guild,
    image_bytes: bytes,
    *,
    filename: str = "avatar.png",
) -> str | None:
    """Post image to the avatar cache channel; return the attachment CDN URL."""
    channel = await resolve_avatar_cache_channel(bot, guild)
    if not channel:
        return None
    try:
        msg = await channel.send(
            content="_avatar cache_",
            file=discord.File(io.BytesIO(image_bytes), filename=filename),
        )
    except discord.HTTPException as exc:
        logger.info("Avatar cache upload failed in guild %s: %s", guild.id, exc)
        return None
    if not msg.attachments:
        return None
    return msg.attachments[0].url
