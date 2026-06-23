"""Wolvden hoard extras; shred, gift, hoard view."""

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from engine.amusement_items import amusement_meta
from engine.amusement_storage import format_amusement_line, gift_amusement
from engine.crafting import format_hoard_summary, shred_amusement_stack
from engine.hunger import format_hunger_line
from engine.thirst import format_thirst_line
from engine.mood import format_mood_line
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed


async def _other_wolf_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    active = db.get_user(interaction.user.id)
    if not active:
        return []
    choices = []
    for wolf in db.list_user_wolves(interaction.user.id):
        if wolf["id"] == active["id"]:
            continue
        name = wolf["wolf_name"]
        if current and current.lower() not in name.lower():
            continue
        choices.append(app_commands.Choice(name=name[:100], value=name))
    return choices[:25]


def _resolve_own_wolf(discord_id: int, name: str):
    rows = db.list_user_wolves(discord_id)
    return next((w for w in rows if w["wolf_name"].lower() == name.strip().lower()), None)


async def _toy_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    user = db.get_user(interaction.user.id)
    if not user:
        return []
    stacks = db.get_amusement_stacks(user["id"])
    choices = []
    for stack in stacks:
        label = format_amusement_line(stack)
        if current and current not in label.lower() and current not in str(stack["id"]):
            continue
        choices.append(app_commands.Choice(name=label[:100], value=str(stack["id"])))
    return choices[:25]


class Wolvden(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="hoarding",
        description="Hoard overview, shred toys, or gift toys.",
    )
    @app_commands.describe(
        action="hoard, shred, or gift",
        toy="Toy stack (shred/gift)",
        wolf="Packmate (gift)",
        own_wolf="Your other wolf (gift)",
        message="Optional howl text (unused for most actions)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Hoard overview", value="hoard"),
            app_commands.Choice(name="Shred toy", value="shred"),
            app_commands.Choice(name="Gift toy", value="gift"),
        ]
    )
    @app_commands.autocomplete(toy=_toy_autocomplete, own_wolf=_other_wolf_autocomplete)
    async def hoarding(
        self,
        interaction: discord.Interaction,
        action: str,
        toy: str | None = None,
        wolf: discord.Member | None = None,
        own_wolf: str | None = None,
        message: str | None = None,
    ):
        if action == "hoard":
            await self._hoard(interaction)
        elif action == "shred":
            if not toy:
                await interaction.response.send_message("Pick a `toy` to shred.", ephemeral=True)
                return
            await self._shred(interaction, toy)
        elif action == "gift":
            if not toy:
                await interaction.response.send_message("Pick a `toy` to gift.", ephemeral=True)
                return
            await self._gift(interaction, toy, wolf, own_wolf)

    async def _hoard(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.get_world(interaction.guild.id)
        embed = howlbert_embed(
            f"{user['wolf_name']}; Hoard",
            format_hoard_summary(user, day=world["day_number"]),
        )
        embed.add_field(name="Mood", value=format_mood_line(user), inline=True)
        embed.add_field(name="Hunger", value=format_hunger_line(user), inline=True)
        embed.add_field(name="Thirst", value=format_thirst_line(user), inline=True)
        embed.set_footer(text="/shred · /prey · /toys · /raccoon buy")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _shred(self, interaction: discord.Interaction, toy: str):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        try:
            stack_id = int(toy)
        except ValueError:
            await interaction.response.send_message("Pick a toy from `/toys`.", ephemeral=True)
            return

        ok, msg, _ = shred_amusement_stack(user, stack_id)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Shred", msg, color=color))

    async def _gift(
        self,
        interaction: discord.Interaction,
        toy: str,
        wolf: discord.Member | None = None,
        own_wolf: str | None = None,
    ):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return

        if wolf and own_wolf:
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Pick One",
                    "Choose another **player** or `own_wolf`; not both.",
                    color=ERROR_COLOR,
                ),
                ephemeral=True,
            )
            return

        partner = None
        if own_wolf:
            partner = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not partner:
                await interaction.response.send_message(
                    embed=howlbert_embed(
                        "Unknown Wolf",
                        "No wolf with that name on your account. Check `/wolves`.",
                        color=ERROR_COLOR,
                    ),
                    ephemeral=True,
                )
                return
            if partner["id"] == user["id"]:
                await interaction.response.send_message(
                    embed=howlbert_embed(
                        "Same Wolf",
                        "Switch to another wolf with `/switchwolf`, or pick a different `own_wolf`.",
                        color=ERROR_COLOR,
                    ),
                    ephemeral=True,
                )
                return
        elif wolf:
            if wolf.bot or wolf.id == interaction.user.id:
                await interaction.response.send_message(
                    embed=howlbert_embed(
                        "Pick Another Wolf",
                        "Use another **player**, or your other wolf via `own_wolf`.",
                        color=ERROR_COLOR,
                    ),
                    ephemeral=True,
                )
                return
            partner = db.get_user(wolf.id)
            if not partner:
                await interaction.response.send_message("They haven't registered a wolf.", ephemeral=True)
                return
        else:
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "No Target",
                    "Pick another **player** or one of your wolves with `own_wolf`.",
                    color=ERROR_COLOR,
                ),
                ephemeral=True,
            )
            return

        try:
            stack_id = int(toy)
        except ValueError:
            await interaction.response.send_message("Pick a toy from `/toys`.", ephemeral=True)
            return

        ok, msg = gift_amusement(user, stack_id, partner)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Gift", msg, color=color))


async def setup(bot: commands.Bot):
    await bot.add_cog(Wolvden(bot))
