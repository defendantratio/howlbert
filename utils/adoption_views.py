"""Accept / decline buttons for pending youth adoptions."""

from __future__ import annotations

import discord

import database as db
from engine.adoption_consent import accept_pending_adoption, decline_pending_adoption
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed


class AdoptionConsentView(discord.ui.View):
    def __init__(self, pending_id: int):
        super().__init__(timeout=1800)
        self.pending_id = pending_id

    async def _finish(self, interaction: discord.Interaction, *, accepted: bool) -> None:
        pending = db.get_pending_adoption(self.pending_id)
        if not pending or pending["status"] != "pending":
            await interaction.response.send_message(
                embed=howlbert_embed("Expired", "This adoption request is no longer active.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return

        if interaction.user.id != pending["youth_owner_discord_id"]:
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Not Your Wolf",
                    "Only the youth's player can accept or decline.",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

        adopter1 = db.get_user_by_id(pending["adopter_1_wolf_id"])
        adopter2 = db.get_user_by_id(pending["adopter_2_wolf_id"])
        youth = db.get_user_by_id(pending["youth_wolf_id"])
        if not adopter1 or not adopter2 or not youth:
            db.set_pending_adoption_status(self.pending_id, "expired")
            await interaction.response.send_message(
                embed=howlbert_embed("Invalid", "One of the wolves no longer exists.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return

        if not accepted:
            ok, msg = decline_pending_adoption(self.pending_id)
            if not ok:
                await interaction.response.send_message(
                    embed=howlbert_embed("Expired", msg, color=ERROR_COLOR), ephemeral=reply_ephemeral()
                )
                return
            self.stop()
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(
                embed=howlbert_embed("Adoption Declined", msg, color=ERROR_COLOR),
                view=self,
            )
            return

        ok, msg = accept_pending_adoption(self.pending_id)
        if not ok:
            await interaction.response.send_message(
                embed=howlbert_embed("Cannot Adopt", msg, color=ERROR_COLOR), ephemeral=reply_ephemeral()
            )
            return
        self.stop()
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            embed=howlbert_embed("Adopted", msg, color=SUCCESS_COLOR),
            view=self,
        )

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, accepted=True)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, accepted=False)

    async def on_timeout(self) -> None:
        db.set_pending_adoption_status(self.pending_id, "expired")
