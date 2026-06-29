"""Discord button/select views for Howlbert flows."""

from __future__ import annotations

import discord

import database as db
from engine.activities import (
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
        "trading post",
        "spend bones with **buy** below.\n"
        "· **consumables**; `/bones action:use item:<key>` (e.g. `herb_bundle`, `den_charm`)\n"
        "· **food & toys**; go to `/food` and `/playpen action:toys` automatically\n"
        "· **wild herbs**; not sold here; gather with `/field action:forage`",
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
        text=f"page {page + 1} of {total_pages} · {len(items)} items · "
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
                        embed=embed, ephemeral=False
                    )

            button = discord.ui.Button(
                label=f"buy {label} ({price})"[:80],
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
                    label="◀ prev",
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
                    label="next ▶",
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"fable_shop_page:{self.page + 1}",
                )
                next_btn.callback = next_cb
                self.add_item(next_btn)


def make_shop_view(items: list, page: int = 0) -> discord.ui.View:
    return ShopPageView(items, page)




# --- Hunt follow-up ---


def make_hunt_followup_view() -> discord.ui.View:
    view = discord.ui.View(timeout=300)

    async def preypile_callback(interaction: discord.Interaction):
        err = preypile_error(interaction)
        if err:
            await interaction.response.send_message(
                embed=howlbert_embed("can't share", err, color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        from cogs.prey_pile import open_prey_pile

        await open_prey_pile(interaction, interaction.client)

    button = discord.ui.Button(
        label="lay out fresh-kill",
        emoji="🍖",
        style=discord.ButtonStyle.primary,
        custom_id="fable_hunt:preypile",
    )
    button.callback = preypile_callback
    view.add_item(button)
    return view


# --- New wolf arrival scene ---

ARRIVAL_SCENE_CHOICES = (
    {
        "key": "bold_arrival",
        "label": "stride in, head high",
        "flavor": "**{name}** doesn't slink to the border; they walk straight up the trail and into the den-mouth, daring anyone to look away first.",
        "note": "Bold Arrival; **+1** on Intimidation checks, for good.",
    },
    {
        "key": "quiet_arrival",
        "label": "slip in without a sound",
        "flavor": "**{name}** keeps to the shadows along the tree line, scenting every wolf long before any of them scent back.",
        "note": "Quiet Arrival; **+1** on Stealth checks, for good.",
    },
    {
        "key": "wary_arrival",
        "label": "limp in, half-starved",
        "flavor": "**{name}** arrives gaunt and watchful, eyes on every exit, the long way here having taught hard lessons.",
        "note": "Wary Arrival; **+1** on Survival checks, for good.",
    },
)

LONER_ARRIVAL_SCENE_CHOICES = (
    {
        "key": "bold_arrival",
        "label": "claims ground, no permission asked",
        "flavor": "**{name}** doesn't ask anyone's leave to walk this ground; they mark it like it was always theirs.",
        "note": "Bold Arrival; **+1** on Intimidation checks, for good.",
    },
    {
        "key": "quiet_arrival",
        "label": "moves like the wild taught them",
        "flavor": "**{name}** moves the way nothing with a den ever has to; quiet, unseen, gone before anyone notices the trail.",
        "note": "Quiet Arrival; **+1** on Stealth checks, for good.",
    },
    {
        "key": "wary_arrival",
        "label": "trusts nothing that isn't earned",
        "flavor": "**{name}** has survived this long alone by trusting nothing that hasn't been earned twice over.",
        "note": "Wary Arrival; **+1** on Survival checks, for good.",
    },
)

BIRTH_SCENE_CHOICES = (
    {
        "key": "bold_arrival",
        "label": "first to bare tiny teeth",
        "flavor": "**{name}** is the first of the litter to growl, the first to push the others off the warmest spot.",
        "note": "Bold Arrival; **+1** on Intimidation checks, for good.",
    },
    {
        "key": "quiet_arrival",
        "label": "first to go still and watch",
        "flavor": "**{name}** is the quiet one of the litter, eyes open early, watching the den before making a sound.",
        "note": "Quiet Arrival; **+1** on Stealth checks, for good.",
    },
    {
        "key": "wary_arrival",
        "label": "smallest, born fighting for milk",
        "flavor": "**{name}** came smallest of the litter, and fought hardest for every meal since.",
        "note": "Wary Arrival; **+1** on Survival checks, for good.",
    },
)

LONER_BIRTH_SCENE_CHOICES = (
    {
        "key": "bold_arrival",
        "label": "born snapping at the wind",
        "flavor": "**{name}** was born under a fallen log with no den wall around them, and came out snapping at the wind like it owed them something.",
        "note": "Bold Arrival; **+1** on Intimidation checks, for good.",
    },
    {
        "key": "quiet_arrival",
        "label": "born listening for danger",
        "flavor": "**{name}** was born to a lone mother with no pack at her back, and learned to listen for danger before they learned to walk.",
        "note": "Quiet Arrival; **+1** on Stealth checks, for good.",
    },
    {
        "key": "wary_arrival",
        "label": "born on the move",
        "flavor": "**{name}** was born between territories, carried from one hiding place to the next before their eyes even opened.",
        "note": "Wary Arrival; **+1** on Survival checks, for good.",
    },
)


def make_arrival_scene_view(
    wolf_id: int, wolf_name: str, owner_discord_id: int, *, pup: bool = False, loner: bool = False
) -> discord.ui.View:
    """
    One-time post-registration scene (Wolvden-style): how did this wolf
    arrive at the den (or come into the litter, for a pup)? Each pick is
    real, not flavor-only — see engine.long_term_injuries.LONG_TERM_TYPES's
    *_arrival entries.
    """
    from engine.long_term_injuries import add_long_term_injury

    view = discord.ui.View(timeout=180)
    if pup and loner:
        choices = LONER_BIRTH_SCENE_CHOICES
    elif pup:
        choices = BIRTH_SCENE_CHOICES
    elif loner:
        choices = LONER_ARRIVAL_SCENE_CHOICES
    else:
        choices = ARRIVAL_SCENE_CHOICES

    def make_callback(choice: dict):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != owner_discord_id:
                await interaction.response.send_message(
                    "this is someone else's scene.", ephemeral=False
                )
                return
            add_long_term_injury(wolf_id, choice["key"])
            for item in view.children:
                item.disabled = True
            embed = howlbert_embed(
                "born" if pup else "arrival",
                choice["flavor"].format(name=wolf_name) + f"\n\n_{choice['note']}_",
            )
            await interaction.response.edit_message(embed=embed, view=view)

        return callback

    for choice in choices:
        button = discord.ui.Button(
            label=choice["label"],
            style=discord.ButtonStyle.secondary,
            custom_id=f"fable_arrival:{choice['key']}:{wolf_id}",
        )
        button.callback = make_callback(choice)
        view.add_item(button)

    return view


# --- Combat ---

from utils.combat_views import make_combat_view  # noqa: E402, F401

