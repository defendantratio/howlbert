"""Persistent trade offer buttons."""

from __future__ import annotations

import discord
from discord import ui

from engine.trade import handle_trade_accept, handle_trade_decline


class TradeAcceptButton(ui.DynamicItem, template=r"^fable_trade:(?P<trade_id>\d+):accept$"):
    def __init__(self, trade_id: int):
        super().__init__(
            ui.Button(
                label="Accept",
                style=discord.ButtonStyle.success,
                custom_id=f"fable_trade:{trade_id}:accept",
            )
        )
        self.trade_id = trade_id

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: ui.Item, match, /
    ):
        return cls(int(match["trade_id"]))

    async def callback(self, interaction: discord.Interaction):
        await handle_trade_accept(interaction, self.trade_id)


class TradeDeclineButton(ui.DynamicItem, template=r"^fable_trade:(?P<trade_id>\d+):decline$"):
    def __init__(self, trade_id: int):
        super().__init__(
            ui.Button(
                label="Decline",
                style=discord.ButtonStyle.secondary,
                custom_id=f"fable_trade:{trade_id}:decline",
            )
        )
        self.trade_id = trade_id

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: ui.Item, match, /
    ):
        return cls(int(match["trade_id"]))

    async def callback(self, interaction: discord.Interaction):
        await handle_trade_decline(interaction, self.trade_id)


TRADE_DYNAMIC_ITEMS = (TradeAcceptButton, TradeDeclineButton)


def make_trade_view(trade_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(TradeAcceptButton(trade_id))
    view.add_item(TradeDeclineButton(trade_id))
    return view
