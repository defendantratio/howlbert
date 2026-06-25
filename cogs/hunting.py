import discord
from discord import app_commands
from discord.ext import commands

import database as db
from engine.activities import try_fishing, try_forage, try_scavenge, try_track
from engine.verge_foraging import try_verge_forage
from engine.prey_items import PREY_FRESH_DAYS
from engine.sniff import try_sniff
from utils.combat_views import make_combat_view
from engine.prey_storage import (
    eat_prey_carcass,
    format_prey_hoard_line,
    salvage_prey_carcass,
)
from engine.thirst import drink_at_creek
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from utils.views import make_hunt_followup_view


async def _prey_stack_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        return []
    world = db.get_world(interaction.guild.id)
    stacks = db.get_prey_stacks(user["id"])
    choices = []
    for stack in stacks:
        label = format_prey_hoard_line(stack, world["day_number"])
        if current and current not in label.lower() and current not in str(stack["id"]):
            continue
        choices.append(
            app_commands.Choice(
                name=label[:100],
                value=str(stack["id"]),
            )
        )
    return choices[:25]


class Hunting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="prey",
        description="View carcasses in your hoard (Wolvden-style; they rot over time).",
    )
    async def prey_hoard(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.get_world(interaction.guild.id)
        stacks = db.get_prey_stacks(user["id"])
        if not stacks:
            embed = howlbert_embed(
                "Empty Hoard",
                "No carcasses yet; **hunt**, **track**, **fish**, or **scavenge**.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        lines = [format_prey_hoard_line(s, world["day_number"]) for s in stacks]
        embed = howlbert_embed(
            f"{user['wolf_name']}; Prey Hoard",
            "\n".join(lines),
        )
        embed.set_footer(
            text=(
                f"Fresh ~{PREY_FRESH_DAYS} sunrises · `/eat` · `/drink` · `/preypile` · "
                f"rotting → `/salvage`"
            )
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="eat",
        description="Eat one use from a carcass in your hoard (−1 exhaustion, +HP).",
    )
    @app_commands.describe(prey="Stack ID from `/prey`")
    @app_commands.autocomplete(prey=_prey_stack_autocomplete)
    async def eat_prey(self, interaction: discord.Interaction, prey: str):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        try:
            stack_id = int(prey)
        except ValueError:
            await interaction.response.send_message(
                "Pick a carcass from `/prey` autocomplete.", ephemeral=True
            )
            return

        ok, msg = eat_prey_carcass(user, stack_id)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Meal", msg, color=color))

    @app_commands.command(
        name="drink",
        description="Drink at the creek (once per hour, no daily cap).",
    )
    async def drink_creek(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.get_world(interaction.guild.id)
        ok, msg = drink_at_creek(
            user,
            day=world["day_number"],
            season=world["season"],
            guild_id=interaction.guild.id,
        )
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = "Drink" if ok else ("Creek Cooldown" if "min" in msg else "Cannot Drink")
        embed = howlbert_embed(title, msg, color=color)
        if ok:
            embed.set_footer(text="Thirst slips faster than hunger each sunrise; drink when you can.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="salvage",
        description="Salvage a rotting carcass into bones (Wolvden-style).",
    )
    @app_commands.describe(prey="Rotting stack ID from `/prey`")
    @app_commands.autocomplete(prey=_prey_stack_autocomplete)
    async def salvage_prey(self, interaction: discord.Interaction, prey: str):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        try:
            stack_id = int(prey)
        except ValueError:
            await interaction.response.send_message(
                "Pick a rotting carcass from `/prey`.", ephemeral=True
            )
            return

        ok, msg, bones = salvage_prey_carcass(user, stack_id)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed("Salvage", msg, color=color)
        if ok and bones:
            embed.add_field(name="Bones", value=f"+{bones} 🦴", inline=True)
        await interaction.response.send_message(embed=embed)

    async def _sniff(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        await interaction.response.defer()
        embed, combat_enc = try_sniff(interaction)
        if combat_enc:
            view = make_combat_view(combat_enc, self.bot)
            await interaction.followup.send(embed=embed, view=view)
            return
        await interaction.followup.send(
            embed=embed,
            ephemeral=embed.color == ERROR_COLOR,
        )

    @app_commands.command(
        name="field",
        description="Scavenge, track, fish, forage, verge-forage, or sniff the wind.",
    )
    @app_commands.describe(
        action="scavenge, track, fishing, forage, verge, sniff, or compendium",
        rarity="Herb rarity (territory forage only)",
        verge_site="Roadside or Twoleg compound (verge forage only)",
        trail_age="Trail age (track only)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Scavenge", value="scavenge"),
            app_commands.Choice(name="Track", value="track"),
            app_commands.Choice(name="Fishing", value="fishing"),
            app_commands.Choice(name="Forage herbs (territory)", value="forage"),
            app_commands.Choice(name="Forage verge (road / Twoleg edge)", value="verge"),
            app_commands.Choice(name="Sniff wind", value="sniff"),
            app_commands.Choice(name="Herb compendium (read-only)", value="compendium"),
        ],
        trail_age=[
            app_commands.Choice(name="Fresh (<1 hour) DC 8", value="fresh"),
            app_commands.Choice(name="Recent (1-6 hours) DC 12", value="recent"),
            app_commands.Choice(name="Cold (6-24 hours) DC 15", value="cold"),
            app_commands.Choice(name="Very cold (1-3 days) DC 18", value="very_cold"),
            app_commands.Choice(name="Faint (3+ days) DC 25", value="faint"),
        ],
        rarity=[
            app_commands.Choice(name="Common (DC 8)", value="common"),
            app_commands.Choice(name="Uncommon (DC 12)", value="uncommon"),
            app_commands.Choice(name="Rare (DC 15)", value="rare"),
            app_commands.Choice(name="Very rare (DC 20)", value="very_rare"),
        ],
        verge_site=[
            app_commands.Choice(name="Thunderpath shoulder", value="roadside"),
            app_commands.Choice(name="Twoleg compound fence-line", value="compound"),
        ],
    )
    async def field(
        self,
        interaction: discord.Interaction,
        action: str,
        rarity: str = "common",
        verge_site: str = "roadside",
        trail_age: str = "recent",
    ):
        if action == "scavenge":
            await self._scavenge(interaction)
        elif action == "track":
            await self._track(interaction, trail_age)
        elif action == "fishing":
            await self._fishing(interaction)
        elif action == "forage":
            await self._forage(interaction, rarity)
        elif action == "verge":
            await self._verge_forage(interaction, verge_site)
        elif action == "sniff":
            await self._sniff(interaction)
        elif action == "compendium":
            await self._herb_compendium(interaction)

    async def _herb_compendium(self, interaction: discord.Interaction):
        from engine.herb_guide import build_herb_guide_embed
        from utils.herb_views import make_herb_guide_view

        title, body = build_herb_guide_embed(page=0, filter_key="all")
        embed = howlbert_embed(title, body)
        embed.set_footer(text="Herb compendium · /field action:compendium · read-only")
        view = make_herb_guide_view(page=0, filter_key="all")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def _scavenge(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = try_scavenge(interaction)
        if embed:
            await interaction.followup.send(embed=embed, ephemeral=embed.color == ERROR_COLOR)

    async def _track(self, interaction: discord.Interaction, trail_age: str = "recent"):
        await interaction.response.defer()
        embed, show_prey = try_track(interaction, trail_age=trail_age)
        if embed:
            if show_prey and embed.color != ERROR_COLOR:
                await interaction.followup.send(embed=embed, view=make_hunt_followup_view())
            else:
                await interaction.followup.send(embed=embed, ephemeral=embed.color == ERROR_COLOR)

    async def _fishing(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed, show_prey = try_fishing(interaction)
        if embed:
            if show_prey and embed.color != ERROR_COLOR:
                await interaction.followup.send(embed=embed, view=make_hunt_followup_view())
            else:
                await interaction.followup.send(embed=embed, ephemeral=embed.color == ERROR_COLOR)

    async def _forage(self, interaction: discord.Interaction, rarity: str = "common"):
        await interaction.response.defer(ephemeral=True)
        embed = try_forage(interaction, rarity)
        if embed:
            await interaction.followup.send(embed=embed, ephemeral=embed.color == ERROR_COLOR)

    async def _verge_forage(self, interaction: discord.Interaction, verge_site: str = "roadside"):
        await interaction.response.defer(ephemeral=True)
        embed = try_verge_forage(interaction, verge_site)
        if embed:
            await interaction.followup.send(embed=embed, ephemeral=embed.color == ERROR_COLOR)


async def setup(bot: commands.Bot):
    await bot.add_cog(Hunting(bot))
