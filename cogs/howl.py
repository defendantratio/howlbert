"""Standalone `/howl` command; pack unity and Commanding Howl."""
import discord
from discord import app_commands
from discord.ext import commands
from engine.howl import execute_howl

class Howl(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='howl', description='raise a pack howl for unity, or a lone howl if you have no pack.')
    @app_commands.describe(message='optional line carried on the wind')
    async def howl(self, interaction: discord.Interaction, message: str | None=None):
        await execute_howl(interaction, message)

async def setup(bot: commands.Bot):
    await bot.add_cog(Howl(bot))