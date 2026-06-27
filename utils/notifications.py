"""Safe Discord DMs for consent requests and rollover birth alerts."""

from __future__ import annotations

import logging

import discord

import database as db
from engine.family import GESTATION_DAYS
from utils.embeds import SUCCESS_COLOR, howlbert_embed

logger = logging.getLogger("howlbert")


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


async def guild_member_ids_with_wolves_resolved(
    bot: discord.Client, guild: discord.Guild
) -> list[int]:
    """Wolf owners in this guild; chunk member list if cache is still cold."""
    ids = guild_member_ids_with_wolves(guild)
    if ids:
        return ids
    try:
        await guild.chunk()
    except (discord.HTTPException, AttributeError):
        pass
    return guild_member_ids_with_wolves(guild)


async def notify_den_news_after_rollover(
    bot: discord.Client,
    guild: discord.Guild,
    world,
    crisis: dict,
    *,
    catch_up_days: int = 1,
    briefing: bool = False,
) -> int:
    """DM the sunrise embed (den news + vitals) to registered players in the guild."""
    from engine.rollover_announce import build_rollover_embed

    day = int(world["day_number"])
    if db.den_news_dm_sent_for_day(guild.id, day):
        logger.info(
            "Den news DM already sent for guild %s on day %s; skipping.",
            guild.id,
            day,
        )
        return 0

    embed = build_rollover_embed(world, crisis)
    if briefing:
        embed.title = "morning den news"
        embed.description = (
            f"_howlbert is back online. day **{world['day_number']}** "
            f"— den news for **{guild.name}**._"
        )
    elif catch_up_days > 1:
        embed.title = f"sunrise catch-up ({catch_up_days} days)"
        embed.description = (
            f"_the den rolled while howlbert was offline. day **{world['day_number']}** "
            f"— sunrise news for **{guild.name}**._"
        )
    elif catch_up_days == 1:
        embed.description = (
            f"_sunrise catch-up for **{guild.name}** — day **{world['day_number']}**._"
        )
    recipients = await guild_member_ids_with_wolves_resolved(bot, guild)
    if not recipients:
        logger.info(
            "No DM recipients for guild %s (day %s); members may not be cached.",
            guild.id,
            world["day_number"],
        )
        return 0
    sent = 0
    for discord_id in recipients:
        if await try_dm_user(bot, discord_id, embed=embed):
            sent += 1
    if sent:
        db.mark_den_news_dm_sent(guild.id, day)
        logger.info(
            "DM'd sunrise den news to %s/%s player(s) in guild %s (day %s).",
            sent,
            len(recipients),
            guild.id,
            world["day_number"],
        )
    else:
        logger.warning(
            "Could not DM any of %s wolf owner(s) in guild %s (day %s).",
            len(recipients),
            guild.id,
            world["day_number"],
        )
    return sent
