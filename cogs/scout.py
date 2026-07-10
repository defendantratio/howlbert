"""Scout role commands; rescout, border survey, cold trails."""
import discord
from discord import app_commands
from discord.ext import commands
from engine.explore import try_rescout
from engine.scout_field import try_scout_survey, try_scout_trail
from utils.replies import reply_ephemeral

class Scout(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    scout = app_commands.Group(name='scout', description='scout role; border survey, trails, rescout.')

    @scout.command(name='rescout', description='walk the biome again; mood & loot (unlimited per sunrise, scout only).')
    async def scout_rescout(self, interaction: discord.Interaction):
        embed = try_rescout(interaction)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @scout.command(name='survey', description='map the pack border unseen; bones, standing, intel (repeats pay less).')
    @app_commands.describe(collaborate='call a pack patrol; scouts in your den join via buttons')
    async def scout_survey(self, interaction: discord.Interaction, collaborate: bool=False):
        if collaborate:
            from cogs.collab_patrol import post_collab_patrol_call
            await post_collab_patrol_call(interaction, self.bot)
            return
        embed = try_scout_survey(interaction)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @scout.command(name='trail', description='follow a cold scent off the main paths; bones and prey chance (repeats pay less).')
    @app_commands.describe(collaborate='call a pack trail; scouts in your den join via buttons')
    async def scout_trail(self, interaction: discord.Interaction, collaborate: bool=False):
        if collaborate:
            from cogs.collab_patrol import post_collab_trail_call
            await post_collab_trail_call(interaction, self.bot)
            return
        embed = try_scout_trail(interaction)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

async def setup(bot: commands.Bot):
    await bot.add_cog(Scout(bot))