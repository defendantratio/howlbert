"""Re-register pending consent views after bot restart."""

from __future__ import annotations

import logging

import database as db
from utils.adoption_views import AdoptionConsentView
from utils.mate_views import MateConsentView

logger = logging.getLogger("howlbert")


async def restore_pending_views(bot) -> None:
    adoptions = db.list_pending_adoptions()
    mates = db.list_pending_mates()
    for row in adoptions:
        if not row["message_id"] or not row["channel_id"]:
            continue
        try:
            channel = bot.get_channel(row["channel_id"]) or await bot.fetch_channel(row["channel_id"])
            message = await channel.fetch_message(row["message_id"])
            await message.edit(view=AdoptionConsentView(row["id"]))
        except Exception as exc:
            logger.warning("Could not restore adoption view %s: %s", row["id"], exc)
    for row in mates:
        if not row["message_id"] or not row["channel_id"]:
            continue
        try:
            channel = bot.get_channel(row["channel_id"]) or await bot.fetch_channel(row["channel_id"])
            message = await channel.fetch_message(row["message_id"])
            await message.edit(view=MateConsentView(row["id"]))
        except Exception as exc:
            logger.warning("Could not restore mate view %s: %s", row["id"], exc)
    if adoptions or mates:
        logger.info(
            "Restored %s adoption and %s mate consent view(s).",
            len(adoptions),
            len(mates),
        )
