"""Herb bag, preparation, den store, and compendium guide."""

from __future__ import annotations

import discord
from utils.replies import reply_ephemeral
from discord import app_commands
from discord.ext import commands

from cogs.care_handlers import (
    denstore,
    dryall,
    herb_guide,
    herbbag,
    prepare_herb,
    prepare_herb_inventory,
    turnin_restricted,
)
from utils.herb_autocomplete import herb_inventory_autocomplete


class Herbs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="herbs",
        description="Herb bag, drying, den store, guide, or poison turn-in.",
    )
    @app_commands.describe(
        action="bag, guide, prepare, dryall, store, or turnin",
        herb="Forage stack (`stack:ID`) or inventory key (`herb_arnica`)",
        herb_filter="Habitat filter for guide",
        prep_method="dry, poultice, tonic, or decoction (prepare)",
        mode="store: list, deposit, depositall, or withdraw",
        store_stack="Stack ID to deposit, withdraw, or turn in",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Forage herb bag", value="bag"),
            app_commands.Choice(name="Herb guide", value="guide"),
            app_commands.Choice(name="Prepare herb", value="prepare"),
            app_commands.Choice(name="Dry all (bag + inventory + den store)", value="dryall"),
            app_commands.Choice(name="Den herb store", value="store"),
            app_commands.Choice(name="Turn in poison herbs", value="turnin"),
        ],
        herb_filter=[
            app_commands.Choice(name="All herbs", value="all"),
            app_commands.Choice(name="Territory (wild)", value="wild"),
            app_commands.Choice(name="Thunderpath verge", value="roadside"),
            app_commands.Choice(name="Twoleg compound edge", value="compound"),
        ],
        prep_method=[
            app_commands.Choice(name="Dry for storage", value="dry"),
            app_commands.Choice(name="Poultice (chewed leaves)", value="poultice"),
            app_commands.Choice(name="Tonic (crushed + water)", value="tonic"),
            app_commands.Choice(name="Decoction (boiled / hot spring)", value="decoction"),
        ],
        mode=[
            app_commands.Choice(name="List store", value="list"),
            app_commands.Choice(name="Deposit herb", value="deposit"),
            app_commands.Choice(name="Deposit all herbs", value="depositall"),
            app_commands.Choice(name="Withdraw herb", value="withdraw"),
        ],
    )
    @app_commands.autocomplete(herb=herb_inventory_autocomplete)
    async def herbs(
        self,
        interaction: discord.Interaction,
        action: str,
        herb: str | None = None,
        herb_filter: str = "all",
        prep_method: str = "dry",
        mode: str = "list",
        store_stack: str | None = None,
    ):
        if action == "bag":
            await herbbag(interaction)
        elif action == "guide":
            await herb_guide(interaction, herb_filter)
        elif action == "dryall":
            await dryall(interaction)
        elif action == "store":
            await denstore(interaction, mode, store_stack, herb)
        elif action == "turnin":
            await turnin_restricted(interaction, store_stack)
        elif action == "prepare":
            from engine.herb_storage import parse_herb_stack_id

            if not herb:
                await interaction.response.send_message(
                    "Pick a **forage bag** stack or a **`/bones action:inventory`** herb from autocomplete.",
                    ephemeral=reply_ephemeral(),
                )
                return
            if herb.strip().lower().startswith("herb_"):
                await prepare_herb_inventory(interaction, herb.strip().lower(), prep_method)
                return
            stack_id = parse_herb_stack_id(herb)
            if stack_id is None:
                await interaction.response.send_message(
                    "Pick from autocomplete, or enter **`stack:ID`** or **`herb_arnica`**.",
                    ephemeral=reply_ephemeral(),
                )
                return
            await prepare_herb(interaction, stack_id, prep_method)
        else:
            await interaction.response.send_message("Pick a valid **action**.", ephemeral=reply_ephemeral())


async def setup(bot: commands.Bot):
    await bot.add_cog(Herbs(bot))
