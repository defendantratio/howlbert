"""Safe Discord DMs for consent requests and rollover birth alerts."""

from __future__ import annotations

import logging

import discord

import database as db
from engine.family import GESTATION_DAYS
from utils.embeds import EMBED_COLOR, SUCCESS_COLOR, howlbert_embed

logger = logging.getLogger("howlbert")


async def _resolve_guild_channel(
    bot: discord.Client, guild_id: int, channel_id: int
) -> discord.TextChannel | None:
    """Fetch a text channel by id and confirm it belongs to guild_id."""
    ch = bot.get_channel(channel_id)
    if not isinstance(ch, discord.TextChannel):
        try:
            ch = await bot.fetch_channel(channel_id)
        except discord.HTTPException:
            return None
    if isinstance(ch, discord.TextChannel) and ch.guild.id == guild_id:
        return ch
    return None


async def post_obituary_to_memoriam(
    bot: discord.Client, guild_id: int, obituary_line: str, *, wolf_name: str | None = None
) -> bool:
    """Post a finished obituary line to the configured #in-memoriam channel, so
    the world keeps its dead in one place. Best-effort: never raises into the
    death flow; logs and returns False on any failure or if disabled."""
    from config import IN_MEMORIAM_CHANNEL_ID

    if not IN_MEMORIAM_CHANNEL_ID:
        return False
    channel = await _resolve_guild_channel(bot, guild_id, IN_MEMORIAM_CHANNEL_ID)
    if channel is None:
        return False
    title = f"in memoriam: {wolf_name}" if wolf_name else "in memoriam"
    embed = howlbert_embed(title, obituary_line, color=EMBED_COLOR)
    try:
        await channel.send(embed=embed)
        return True
    except discord.HTTPException as exc:
        logger.info("Could not post obituary to memoriam in guild %s: %s", guild_id, exc)
        return False


async def try_dm_user(
    bot: discord.Client,
    discord_id: int,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
) -> bool:
    try:
        user = bot.get_user(discord_id) or await bot.fetch_user(discord_id)
        await user.send(content=content, embed=embed)
        return True
    except (discord.Forbidden, discord.HTTPException, AttributeError) as exc:
        logger.info("Could not DM user %s: %s", discord_id, exc)
        return False


async def notify_consent_request(
    bot: discord.Client,
    discord_id: int,
    *,
    title: str,
    body: str,
) -> bool:
    embed = howlbert_embed(title, body, color=SUCCESS_COLOR)
    return await try_dm_user(bot, discord_id, embed=embed)


def births_crossing_threshold(day_number: int) -> list[tuple[int, str]]:
    """Wolves to ping when gestation completes on this sunrise (discord_id, message)."""
    recipients: list[tuple[int, str]] = []
    seen: set[int] = set()

    def add(discord_id: int | None, message: str) -> None:
        if not discord_id or discord_id in seen:
            return
        seen.add(discord_id)
        recipients.append((discord_id, message))

    with db.get_db() as conn:
        rows = conn.execute("SELECT * FROM users WHERE is_pregnant = 1").fetchall()
    for row in rows:
        elapsed = max(0, day_number - row["pregnancy_start_day"])
        if elapsed != GESTATION_DAYS:
            continue
        mate = db.get_mate_wolf(row)
        mate_name = mate["wolf_name"] if mate else "unknown"
        add(
            row["discord_id"],
            f"**{row['wolf_name']}**; gestation is complete. use **`/birth names:...`** "
            f"to name the litter (mate: **{mate_name}**).",
        )
        if mate:
            add(
                mate["discord_id"],
                f"your mate **{row['wolf_name']}** is ready for **`/birth`**; "
                f"they name the litter when the pups arrive.",
            )
    return recipients


async def notify_births_ready_after_rollover(bot: discord.Client, day_number: int) -> int:
    sent = 0
    for discord_id, message in births_crossing_threshold(day_number):
        ok = await notify_consent_request(
            bot,
            discord_id,
            title="birth ready",
            body=message,
        )
        if ok:
            sent += 1
    return sent


def guild_member_ids_with_wolves(guild: discord.Guild) -> list[int]:
    """Discord IDs in this guild who have at least one living wolf (member cache)."""
    member_ids = {m.id for m in guild.members}
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT discord_id FROM users
            WHERE condition NOT IN ('dead', 'dying')
            """
        ).fetchall()
    return [int(r["discord_id"]) for r in rows if int(r["discord_id"]) in member_ids]




