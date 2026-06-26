"""Pack ceremonies: naming, blooding, mourning."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from engine.blooding import is_unblooded_juvenile
from engine.mirewort_burial import is_mirewort, mirewort_grave_rite
from engine.wolf_journal import log_blooded, log_rite
from utils.embeds import EMBED_COLOR, ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from utils.permissions import is_howlbert_admin
from utils.replies import reply_ephemeral

logger = logging.getLogger("howlbert")


def _active_wolf(interaction: discord.Interaction):
    return db.get_user(interaction.user.id)


def _world_day(guild_id: int) -> int | None:
    world = db.get_world(guild_id)
    return int(world["day_number"]) if world else None


class Rite(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    rite = app_commands.Group(name="rite", description="Den ceremonies and rites.")

    @rite.command(name="naming", description="Name a pup or youth in a den ceremony.")
    @app_commands.describe(
        wolf="The pup being named (your wolf or another member's)",
        words="Optional words spoken at the rite",
    )
    async def naming(
        self,
        interaction: discord.Interaction,
        wolf: str,
        words: str | None = None,
    ):
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=reply_ephemeral())
            return
        actor = _active_wolf(interaction)
        if not actor:
            await interaction.response.send_message("Use `/register` first.", ephemeral=reply_ephemeral())
            return

        target_row = db.get_wolf_by_name(wolf)
        if not target_row:
            await interaction.response.send_message(
                embed=howlbert_embed("Not Found", "No wolf by that name.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        from config import PUP_MAX_MOONS

        age = int(target_row["age_months"]) if "age_months" in target_row.keys() else 24
        if age >= PUP_MAX_MOONS and not (
            "is_born_pup" in target_row.keys() and target_row["is_born_pup"]
        ):
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Too Old",
                    "Naming rites are for pups and very young wolves.",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return
        if target_row["discord_id"] != interaction.user.id and not is_howlbert_admin(interaction):
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Not Yours",
                    "You can only hold a naming rite for your own pup unless you're admin.",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

        day = _world_day(interaction.guild.id)
        speech = words.strip() if words else "_The den speaks the name aloud._"
        embed = howlbert_embed(
            f"🌿 Naming Rite — {target_row['wolf_name']}",
            (
                f"**{actor['wolf_name']}** leads the den in naming **{target_row['wolf_name']}**.\n\n"
                f"{speech}"
            ),
            color=SUCCESS_COLOR,
        )
        log_rite(
            target_row["id"],
            "rite_naming",
            f"Naming rite led by **{actor['wolf_name']}**.",
            guild_id=interaction.guild.id,
            day=day,
        )
        await interaction.response.send_message(embed=embed)

    @rite.command(name="blooding", description="Hold a blooding ceremony for a juvenile.")
    @app_commands.describe(
        wolf="The juvenile (defaults to your active wolf)",
        words="Optional words at the rite",
    )
    async def blooding(
        self,
        interaction: discord.Interaction,
        wolf: str | None = None,
        words: str | None = None,
    ):
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=reply_ephemeral())
            return
        actor = _active_wolf(interaction)
        if not actor:
            await interaction.response.send_message("Use `/register` first.", ephemeral=reply_ephemeral())
            return

        if wolf:
            target = db.get_wolf_by_name(wolf)
        else:
            target = actor
        if not target:
            await interaction.response.send_message(
                embed=howlbert_embed("Not Found", "No wolf by that name.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        if target["discord_id"] != interaction.user.id and not is_howlbert_admin(interaction):
            await interaction.response.send_message(
                embed=howlbert_embed("Not Yours", "You can only rite your own wolf.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        if is_unblooded_juvenile(target) or not (
            "has_blooding" in target.keys() and target["has_blooding"]
        ):
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Not Yet",
                    "They must earn blooding on a hunt first (`/bones action:hunt`), then hold the rite.",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

        day = _world_day(interaction.guild.id)
        speech = words.strip() if words else "_Blood on muzzle, name on the wind — the den witnesses._"
        embed = howlbert_embed(
            f"🩸 Blooding Rite — {target['wolf_name']}",
            (
                f"**{actor['wolf_name']}** calls the pack to witness **{target['wolf_name']}**'s blooding.\n\n"
                f"{speech}"
            ),
            color=EMBED_COLOR,
        )
        log_blooded(target["id"], target["wolf_name"], ceremonial=True)
        await interaction.response.send_message(embed=embed)

    @rite.command(name="mourning", description="Hold a mourning rite for a fallen wolf.")
    @app_commands.describe(
        wolf="Name of the wolf being mourned",
        words="Optional words at the rite",
    )
    async def mourning(
        self,
        interaction: discord.Interaction,
        wolf: str,
        words: str | None = None,
    ):
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=reply_ephemeral())
            return
        actor = _active_wolf(interaction)
        if not actor:
            await interaction.response.send_message("Use `/register` first.", ephemeral=reply_ephemeral())
            return

        target = db.get_wolf_by_name(wolf)
        if not target:
            await interaction.response.send_message(
                embed=howlbert_embed("Not Found", "No wolf by that name.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        if target["condition"] != "dead":
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Still Living",
                    "Mourning rites are for wolves who have passed.",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

        day = _world_day(interaction.guild.id)
        cause = target["cause_of_death"] if "cause_of_death" in target.keys() else "unknown"
        journal_note = f"Mourning rite led by **{actor['wolf_name']}**."
        if is_mirewort(actor):
            speech, grave_journal = mirewort_grave_rite(
                target["wolf_name"],
                custom_words=words,
            )
            journal_note = f"{journal_note} {grave_journal}"
        else:
            speech = words.strip() if words else "_The den sits in silence._"
        embed = howlbert_embed(
            f"🕯 Mourning — {target['wolf_name']}",
            (
                f"**{actor['wolf_name']}** leads mourning for **{target['wolf_name']}** "
                f"_(died of {cause})_.\n\n{speech}"
            ),
            color=EMBED_COLOR,
        )
        log_rite(
            target["id"],
            "rite_mourning",
            journal_note,
            guild_id=interaction.guild.id,
            day=day,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Rite(bot))
