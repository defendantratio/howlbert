"""Accept / decline buttons for pending mate requests."""

from __future__ import annotations

import discord

import database as db
from engine.mating import execute_mating, mating_embed_title
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed


class MateConsentView(discord.ui.View):
    def __init__(self, pending_id: int):
        super().__init__(timeout=1800)
        self.pending_id = pending_id

    async def _finish(self, interaction: discord.Interaction, *, accepted: bool) -> None:
        pending = db.get_pending_mate(self.pending_id)
        if not pending or pending["status"] != "pending":
            await interaction.response.send_message(
                embed=howlbert_embed("Expired", "This mating request is no longer active.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return

        if interaction.user.id != pending["partner_discord_id"]:
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Not Your Call",
                    "Only the invited partner can accept or decline.",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

        initiator = db.get_user_by_id(pending["initiator_wolf_id"])
        partner = db.get_user_by_id(pending["partner_wolf_id"])
        if not initiator or not partner:
            db.set_pending_mate_status(self.pending_id, "expired")
            await interaction.response.send_message(
                embed=howlbert_embed("Invalid", "One of the wolves no longer exists.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return

        if not accepted:
            db.set_pending_mate_status(self.pending_id, "declined")
            self.stop()
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(
                embed=howlbert_embed(
                    "Mating Declined",
                    f"**{partner['wolf_name']}** declines **{initiator['wolf_name']}**.",
                    color=ERROR_COLOR,
                ),
                view=self,
            )
            return

        world = db.get_world(pending["guild_id"])
        if world["season"] != "spring":
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Wrong Season",
                    "Mating season ended before you could respond.",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

        if partner["receptive_day"] < world["day_number"]:
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Not Receptive",
                    "You are no longer receptive; they must `/courtship action:court` you again.",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

        ok, body, color, hard_fail = execute_mating(initiator, partner, day_number=world["day_number"])
        db.set_pending_mate_status(self.pending_id, "accepted" if ok and not hard_fail else "expired")
        self.stop()
        for item in self.children:
            item.disabled = True
        title = mating_embed_title(body, hard_fail=hard_fail or not ok)
        await interaction.response.edit_message(
            embed=howlbert_embed(title, body, color=color),
            view=self,
        )

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, accepted=True)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, accepted=False)

    async def on_timeout(self) -> None:
        db.set_pending_mate_status(self.pending_id, "expired")
