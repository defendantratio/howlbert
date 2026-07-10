import discord
from discord import app_commands
from discord.ext import commands
from engine.lexicon import build_terms_embed
from utils.embeds import EMBED_COLOR, embed_footer, howlbert_embed

class Lexicon(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='terms', description='wolf rp glossary; fresh-kill, newgrowth, insults, and more.')
    @app_commands.describe(topic='which terms to read')
    @app_commands.choices(topic=[app_commands.Choice(name='overview', value='overview'), app_commands.Choice(name='basic terms', value='basic'), app_commands.Choice(name='seasons & time', value='seasons'), app_commands.Choice(name='measurements', value='measurements'), app_commands.Choice(name='insults', value='insults')])
    async def terms(self, interaction: discord.Interaction, topic: str='overview'):
        title, body = build_terms_embed(topic)
        embed = howlbert_embed(title, body, color=EMBED_COLOR)
        embed.set_footer(text=embed_footer('wolf tongue'))
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Lexicon(bot))