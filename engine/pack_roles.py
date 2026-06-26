"""Auto-managed Discord roles for Great Pack membership (onboarding)."""

from __future__ import annotations

import logging

import discord

from config import GREAT_PACKS

logger = logging.getLogger("howlbert")

ALL_PACK_ROLE_NAMES = {info["name"] for info in GREAT_PACKS.values()}


def pack_role_name(pack_key: str) -> str | None:
    """Discord role name for a pack key; loners/rogues get no dedicated role."""
    info = GREAT_PACKS.get(pack_key)
    return info["name"] if info else None


async def ensure_pack_role(guild: discord.Guild, name: str) -> discord.Role | None:
    """Find the pack role by name, creating it if the bot may manage roles."""
    role = discord.utils.get(guild.roles, name=name)
    if role:
        return role
    me = guild.me
    if not me or not me.guild_permissions.manage_roles:
        return None
    try:
        return await guild.create_role(
            name=name, mentionable=True, reason="Howlbert pack role"
        )
    except (discord.Forbidden, discord.HTTPException):
        logger.info("Could not create pack role %s in guild %s", name, guild.id)
        return None


async def sync_member_pack_role(
    guild: discord.Guild | None,
    member: discord.Member | None,
    pack_key: str,
) -> str | None:
    """Give the member their current pack role and strip other pack roles.

    Returns a short user-facing note, or None when nothing notable happened
    (no permission, no change, or loner/rogue).
    """
    if guild is None or member is None:
        return None
    me = guild.me
    if not me or not me.guild_permissions.manage_roles:
        return None

    target_name = pack_role_name(pack_key)
    stale = [
        r for r in member.roles
        if r.name in ALL_PACK_ROLE_NAMES and r.name != target_name
    ]
    if stale:
        try:
            await member.remove_roles(*stale, reason="Howlbert pack change")
        except (discord.Forbidden, discord.HTTPException):
            pass

    if not target_name:
        return None

    role = await ensure_pack_role(guild, target_name)
    if not role:
        return None
    if role in member.roles:
        return None
    if role >= me.top_role:
        return f"⚠️ Move my role above **{role.name}** so I can assign pack roles."
    try:
        await member.add_roles(role, reason="Howlbert pack join")
    except (discord.Forbidden, discord.HTTPException):
        return None
    return f"Given the **{role.name}** role."
