"""Discord button/select views for Howlbert flows."""

from __future__ import annotations

import discord

import database as db
from engine.activities import (
    accept_quest,
    complete_quest,
    preypile_error,
    purchase_item,
)
from utils.currency import format_bones
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, howlbert_embed


def _is_error(embed: discord.Embed) -> bool:
    return embed.color == ERROR_COLOR


# --- Shop ---

SHOP_ITEMS_PER_PAGE = 4


def build_shop_embed(items: list, page: int = 0) -> discord.Embed:
    total_pages = max(1, (len(items) + SHOP_ITEMS_PER_PAGE - 1) // SHOP_ITEMS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * SHOP_ITEMS_PER_PAGE
    chunk = items[start : start + SHOP_ITEMS_PER_PAGE]

    embed = howlbert_embed(
        "Trading Post",
        "Spend bones with **Buy** below.\n"
        "· **Consumables**; `/bones action:use item:<key>` (e.g. `herb_bundle`, `den_charm`)\n"
        "· **Food & toys**; go to `/prey` and `/playpen action:toys` automatically\n"
        "· **Wild herbs**; not sold here; gather with `/field action:forage`",
    )
    for item in chunk:
        desc = item["description"] or "-"
        if len(desc) > 200:
            desc = desc[:197] + "..."
        embed.add_field(
            name=f"{item['name']} - {format_bones(item['price'])}",
            value=f"`{item['key']}`; {desc}",
            inline=False,
        )
    embed.set_footer(
        text=f"Page {page + 1} of {total_pages} · {len(items)} items · "
        "/bones action:buy item:<key> · action:inventory"
    )
    return embed


class ShopPageView(discord.ui.View):
    def __init__(self, items: list, page: int = 0):
        super().__init__(timeout=300)
        self.items = items
        self.page = page
        self.total_pages = max(1, (len(items) + SHOP_ITEMS_PER_PAGE - 1) // SHOP_ITEMS_PER_PAGE)
        self._build()

    def _page_items(self) -> list:
        start = self.page * SHOP_ITEMS_PER_PAGE
        return self.items[start : start + SHOP_ITEMS_PER_PAGE]

    def _build(self):
        self.clear_items()
        for item in self._page_items():
            if item["price"] <= 0:
                continue
            key = item["key"]
            label = item["name"][:80]
            price = format_bones(item["price"])

            async def callback(interaction: discord.Interaction, *, item_key=key):
                embed = purchase_item(interaction, item_key)
                if embed:
                    await interaction.response.send_message(
                        embed=embed, ephemeral=_is_error(embed)
                    )

            button = discord.ui.Button(
                label=f"Buy {label} ({price})"[:80],
                style=discord.ButtonStyle.success,
                custom_id=f"fable_shop:{key}:{self.page}",
            )
            button.callback = callback
            self.add_item(button)

        if self.total_pages > 1:
            if self.page > 0:

                async def prev_cb(interaction: discord.Interaction):
                    view = ShopPageView(self.items, self.page - 1)
                    await interaction.response.edit_message(
                        embed=build_shop_embed(self.items, view.page),
                        view=view,
                    )

                prev_btn = discord.ui.Button(
                    label="◀ Prev",
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"fable_shop_page:{self.page - 1}",
                )
                prev_btn.callback = prev_cb
                self.add_item(prev_btn)

            if self.page < self.total_pages - 1:

                async def next_cb(interaction: discord.Interaction):
                    view = ShopPageView(self.items, self.page + 1)
                    await interaction.response.edit_message(
                        embed=build_shop_embed(self.items, view.page),
                        view=view,
                    )

                next_btn = discord.ui.Button(
                    label="Next ▶",
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"fable_shop_page:{self.page + 1}",
                )
                next_btn.callback = next_cb
                self.add_item(next_btn)


def make_shop_view(items: list, page: int = 0) -> discord.ui.View:
    return ShopPageView(items, page)


# --- Quests ---


def make_quest_accept_view(quests: list) -> discord.ui.View | None:
    if not quests:
        return None
    view = discord.ui.View(timeout=300)
    if len(quests) <= 4:
        for q in quests[:4]:
            key = q["key"]

            async def callback(interaction: discord.Interaction, *, quest_key=key):
                embed = accept_quest(interaction, quest_key)
                if embed:
                    await interaction.response.send_message(
                        embed=embed, ephemeral=_is_error(embed)
                    )

            button = discord.ui.Button(
                label=q["title"][:80],
                style=discord.ButtonStyle.primary,
                custom_id=f"fable_accept:{key}",
            )
            button.callback = callback
            view.add_item(button)
        return view

    options = [
        discord.SelectOption(
            label=q["title"][:100], value=q["key"], description=q["difficulty"][:100]
        )
        for q in quests[:25]
    ]

    async def select_callback(interaction: discord.Interaction):
        quest_key = interaction.data["values"][0]
        embed = accept_quest(interaction, quest_key)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=_is_error(embed))

    select = discord.ui.Select(
        placeholder="Accept a quest…",
        options=options,
        custom_id="fable_accept_select",
    )
    select.callback = select_callback
    view.add_item(select)
    return view


def make_quest_complete_view(ready_quests: list) -> discord.ui.View | None:
    ready = [q for q in ready_quests if q["progress"] >= q["objective_count"]]
    if not ready:
        return None
    view = discord.ui.View(timeout=300)

    if len(ready) == 1:
        key = ready[0]["quest_key"]

        async def callback(interaction: discord.Interaction, *, quest_key=key):
            embed = complete_quest(interaction, quest_key)
            if embed:
                await interaction.response.send_message(
                    embed=embed, ephemeral=_is_error(embed)
                )

        button = discord.ui.Button(
            label=f"Turn in: {ready[0]['title'][:60]}",
            style=discord.ButtonStyle.success,
            custom_id=f"fable_complete:{key}",
        )
        button.callback = callback
        view.add_item(button)
        return view

    options = [
        discord.SelectOption(label=q["title"][:100], value=q["quest_key"])
        for q in ready[:25]
    ]

    async def select_callback(interaction: discord.Interaction):
        quest_key = interaction.data["values"][0]
        embed = complete_quest(interaction, quest_key)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=_is_error(embed))

    select = discord.ui.Select(
        placeholder="Turn in a finished quest…",
        options=options,
        custom_id="fable_complete_select",
    )
    select.callback = select_callback
    view.add_item(select)
    return view


# --- Hunt follow-up ---


def make_hunt_followup_view() -> discord.ui.View:
    view = discord.ui.View(timeout=300)

    async def preypile_callback(interaction: discord.Interaction):
        err = preypile_error(interaction)
        if err:
            await interaction.response.send_message(
                embed=howlbert_embed("Can't Share", err, color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        from cogs.prey_pile import open_prey_pile

        await open_prey_pile(interaction, interaction.client)

    button = discord.ui.Button(
        label="Lay out fresh-kill",
        emoji="🍖",
        style=discord.ButtonStyle.primary,
        custom_id="fable_hunt:preypile",
    )
    button.callback = preypile_callback
    view.add_item(button)
    return view


# --- Combat ---

from utils.combat_views import make_combat_view  # noqa: E402, F401

