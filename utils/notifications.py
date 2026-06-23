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
            f"**{row['wolf_name']}**; gestation is complete. Use **`/birth names:...`** "
            f"to name the litter (mate: **{mate_name}**).",
        )
        if mate:
            add(
                mate["discord_id"],
                f"Your mate **{row['wolf_name']}** is ready for **`/birth`**; "
                f"they name the litter when the pups arrive.",
            )
    return recipients


async def notify_births_ready_after_rollover(bot: discord.Client, day_number: int) -> int:
    sent = 0
    for discord_id, message in births_crossing_threshold(day_number):
        ok = await notify_consent_request(
            bot,
            discord_id,
            title="Birth Ready",
            body=message,
        )
        if ok:
            sent += 1
    return sent
