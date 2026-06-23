"""Paginated herb guide view."""

from __future__ import annotations

import discord

from engine.herb_guide import FILTER_LABELS, build_herb_guide_embed, total_pages
from utils.embeds import EMBED_COLOR, howlbert_embed


class HerbGuideView(discord.ui.View):
    def __init__(self, *, page: int = 0, filter_key: str = "all"):
        super().__init__(timeout=300)
        self.page = page
        self.filter_key = filter_key
        self.max_page = total_pages(filter_key)

        if page > 0:
            self.prev_page.disabled = False
        if page < self.max_page:
            self.next_page.disabled = False

        options = [
            discord.SelectOption(
                label=label,
                value=key,
                default=(key == filter_key),
            )
            for key, label in FILTER_LABELS.items()
        ]
        self.filter_select.options = options

    def _embed(self) -> discord.Embed:
        title, body = build_herb_guide_embed(page=self.page, filter_key=self.filter_key)
        embed = howlbert_embed(title, body, color=EMBED_COLOR)
        embed.set_footer(text="Herb guide · /vitals action:herbs")
        return embed

    @discord.ui.select(
        placeholder="Filter by habitat…",
        min_values=1,
        max_values=1,
        row=1,
    )
    async def filter_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.filter_key = select.values[0]
        self.page = 0
        self.max_page = total_pages(self.filter_key)
        self.prev_page.disabled = True
        self.next_page.disabled = self.max_page == 0
        await interaction.response.edit_message(embed=self._embed(), view=self)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, disabled=True)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self.prev_page.disabled = self.page == 0
        self.next_page.disabled = self.page >= self.max_page
        await interaction.response.edit_message(embed=self._embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, disabled=True)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(self.max_page, self.page + 1)
        self.prev_page.disabled = self.page == 0
        self.next_page.disabled = self.page >= self.max_page
        await interaction.response.edit_message(embed=self._embed(), view=self)

    @discord.ui.button(label="Overview", style=discord.ButtonStyle.primary, row=2)
    async def overview(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 0
        self.prev_page.disabled = True
        self.next_page.disabled = self.max_page > 0
        await interaction.response.edit_message(embed=self._embed(), view=self)


def make_herb_guide_view(*, page: int = 0, filter_key: str = "all") -> HerbGuideView:
    return HerbGuideView(page=page, filter_key=filter_key)
