"""Interactive crop editor for `/proxy avatar`."""

from __future__ import annotations

import io
import logging

import discord
from discord import ui

import database as db
from engine.avatar_crop import (
    MAX_ZOOM,
    MIN_ZOOM,
    PAN_STEP,
    ZOOM_STEP,
    CropState,
    render_cropped_png,
)
from engine.avatar_hosting import host_avatar_bytes
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed

logger = logging.getLogger("howlbert")


class AvatarCropView(ui.View):
    def __init__(
        self,
        bot,
        *,
        owner_id: int,
        wolf,
        source_bytes: bytes,
        guild: discord.Guild,
    ):
        super().__init__(timeout=300)
        self.bot = bot
        self.owner_id = owner_id
        self.wolf = wolf
        self.source_bytes = source_bytes
        self.guild = guild
        self.state = CropState()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This crop editor isn't yours.", ephemeral=True
            )
            return False
        return True

    def _embed(self) -> discord.Embed:
        embed = howlbert_embed(
            f"Crop — {self.wolf['wolf_name']}",
            (
                "Move and zoom until the portrait looks right, then **Save**.\n"
                "The preview circle matches how Discord shows webhook avatars."
            ),
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="◀ ▶ ▲ ▼ pan · + / − zoom · ↺ reset")
        embed.set_image(url="attachment://preview.png")
        return embed

    def _preview_file(self) -> discord.File:
        png = render_cropped_png(self.source_bytes, self.state, preview=True)
        return discord.File(io.BytesIO(png), filename="preview.png")

    async def _refresh(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(
            embed=self._embed(),
            attachments=[self._preview_file()],
            view=self,
        )

    @ui.button(label="◀", style=discord.ButtonStyle.secondary, row=0)
    async def pan_left(self, interaction: discord.Interaction, button: ui.Button):
        self.state.offset_x -= PAN_STEP
        await self._refresh(interaction)

    @ui.button(label="▶", style=discord.ButtonStyle.secondary, row=0)
    async def pan_right(self, interaction: discord.Interaction, button: ui.Button):
        self.state.offset_x += PAN_STEP
        await self._refresh(interaction)

    @ui.button(label="▲", style=discord.ButtonStyle.secondary, row=0)
    async def pan_up(self, interaction: discord.Interaction, button: ui.Button):
        self.state.offset_y -= PAN_STEP
        await self._refresh(interaction)

    @ui.button(label="▼", style=discord.ButtonStyle.secondary, row=0)
    async def pan_down(self, interaction: discord.Interaction, button: ui.Button):
        self.state.offset_y += PAN_STEP
        await self._refresh(interaction)

    @ui.button(label="−", style=discord.ButtonStyle.secondary, row=1)
    async def zoom_out(self, interaction: discord.Interaction, button: ui.Button):
        self.state.zoom = max(MIN_ZOOM, round(self.state.zoom - ZOOM_STEP, 2))
        await self._refresh(interaction)

    @ui.button(label="+", style=discord.ButtonStyle.secondary, row=1)
    async def zoom_in(self, interaction: discord.Interaction, button: ui.Button):
        self.state.zoom = min(MAX_ZOOM, round(self.state.zoom + ZOOM_STEP, 2))
        await self._refresh(interaction)

    @ui.button(label="↺ Reset", style=discord.ButtonStyle.secondary, row=1)
    async def reset_crop(self, interaction: discord.Interaction, button: ui.Button):
        self.state.reset()
        await self._refresh(interaction)

    @ui.button(label="Save", style=discord.ButtonStyle.success, row=2)
    async def save_crop(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        final_png = render_cropped_png(self.source_bytes, self.state, preview=False)
        url = await host_avatar_bytes(
            self.bot,
            self.guild,
            final_png,
            filename=f"wolf_{self.wolf['id']}_avatar.png",
        )
        if not url:
            await interaction.followup.send(
                embed=howlbert_embed(
                    "No Avatar Cache",
                    "Create a channel named **#howlbert-avatars** (bot can post there), "
                    "or set `AVATAR_CACHE_CHANNEL_ID` in `.env` so cropped avatars can be hosted.",
                    color=ERROR_COLOR,
                ),
                ephemeral=True,
            )
            return
        db.set_wolf_identity(self.wolf["id"], avatar_url=url)
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass
        await interaction.followup.send(
            embed=howlbert_embed(
                self.wolf["wolf_name"],
                "Proxy avatar saved.",
                color=SUCCESS_COLOR,
            ),
            ephemeral=True,
        )
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=2)
    async def cancel_crop(self, interaction: discord.Interaction, button: ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=howlbert_embed("Cancelled", "Avatar not changed.", color=ERROR_COLOR),
            attachments=[],
            view=self,
        )
        self.stop()

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
