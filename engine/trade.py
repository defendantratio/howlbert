"""Trade offer display and button handlers."""

from __future__ import annotations

import discord

import database as db
from utils.currency import format_bones
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed

TRADE_ERROR_MESSAGES = {
    "not_found": "This trade no longer exists.",
    "not_pending": "This trade was already completed or cancelled.",
    "expired": "This trade offer expired; start a new one with `/trade offer`.",
    "not_registered": "One of the wolves is no longer registered.",
    "insufficient_from": "The offerer no longer has everything they promised.",
    "insufficient_to": "You don't have everything required to accept this trade.",
}


def _side_line(
    item_id: int | None,
    item_qty: int,
    bones: int,
) -> str:
    parts: list[str] = []
    if item_id and item_qty > 0:
        item = db.get_item_by_id(item_id)
        name = item["name"] if item else "Unknown item"
        parts.append(f"**{name}** x{item_qty}")
    if bones > 0:
        parts.append(format_bones(bones))
    return " · ".join(parts) if parts else "-"


def build_trade_embed(trade, *, status: str = "pending") -> discord.Embed:
    from_user = db.get_user(trade["from_discord_id"])
    to_user = db.get_user(trade["to_discord_id"])
    from_name = from_user["wolf_name"] if from_user else "Unknown"
    to_name = to_user["wolf_name"] if to_user else "Unknown"

    offer_line = _side_line(
        trade["from_item_id"],
        int(trade["from_item_qty"]),
        int(trade["from_bones"]),
    )
    want_line = _side_line(
        trade["to_item_id"],
        int(trade["to_item_qty"]),
        int(trade["to_bones"]),
    )
    has_want = bool(
        (trade["to_item_id"] and int(trade["to_item_qty"]) > 0)
        or int(trade["to_bones"]) > 0
    )

    if status == "completed":
        embed = howlbert_embed("Trade Complete", color=SUCCESS_COLOR)
    elif status == "declined":
        embed = howlbert_embed("Trade Declined", color=ERROR_COLOR)
    elif status == "cancelled":
        embed = howlbert_embed("Trade Cancelled", color=ERROR_COLOR)
    else:
        embed = howlbert_embed("Trade Offer", color=SUCCESS_COLOR)

    embed.add_field(name=f"{from_name} offers", value=offer_line, inline=False)
    if has_want:
        embed.add_field(name=f"In return from {to_name}", value=want_line, inline=False)
    else:
        embed.set_footer(text=f"{to_name}; press Accept to receive the offer.")
    return embed


async def handle_trade_accept(interaction: discord.Interaction, trade_id: int) -> None:
    trade = db.get_pending_trade(trade_id)
    if not trade or trade["status"] != "pending":
        embed = howlbert_embed(
            "Trade Unavailable",
            TRADE_ERROR_MESSAGES.get("not_pending", "Unavailable."),
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if interaction.user.id != trade["to_discord_id"]:
        await interaction.response.send_message(
            "Only the recipient can accept this trade.", ephemeral=True
        )
        return

    result = db.complete_pending_trade(trade_id)
    if result != "ok":
        msg = TRADE_ERROR_MESSAGES.get(result, "Trade failed.")
        await interaction.response.send_message(msg, ephemeral=True)
        return

    trade = db.get_pending_trade(trade_id)
    embed = build_trade_embed(trade, status="completed")
    await interaction.response.edit_message(embed=embed, view=None)


async def handle_trade_decline(interaction: discord.Interaction, trade_id: int) -> None:
    trade = db.get_pending_trade(trade_id)
    if not trade or trade["status"] != "pending":
        await interaction.response.send_message(
            "This trade is no longer active.", ephemeral=True
        )
        return

    if interaction.user.id not in (trade["from_discord_id"], trade["to_discord_id"]):
        await interaction.response.send_message(
            "This trade isn't yours.", ephemeral=True
        )
        return

    db.decline_pending_trade(trade_id)
    trade = db.get_pending_trade(trade_id)
    embed = build_trade_embed(trade, status="declined")
    await interaction.response.edit_message(embed=embed, view=None)
