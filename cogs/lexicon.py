import discord
from discord import app_commands
from discord.ext import commands

from engine.lexicon import build_terms_embed
from utils.embeds import EMBED_COLOR, embed_footer, howlbert_embed


class Lexicon(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="terms",
        description="Wolf RP glossary; fresh-kill, Newgrowth, insults, and more.",
    )
    @app_commands.describe(topic="Which terms to read")
    @app_commands.choices(
        topic=[
            app_commands.Choice(name="Overview", value="overview"),
            app_commands.Choice(name="Basic terms", value="basic"),
            app_commands.Choice(name="Seasons & time", value="seasons"),
            app_commands.Choice(name="Measurements", value="measurements"),
            app_commands.Choice(name="Insults", value="insults"),
        ]
    )
    async def terms(self, interaction: discord.Interaction, topic: str = "overview"):
        title, body = build_terms_embed(topic)
        embed = howlbert_embed(title, body, color=EMBED_COLOR)
        embed.set_footer(text=embed_footer("Wolf tongue"))
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Lexicon(bot))
