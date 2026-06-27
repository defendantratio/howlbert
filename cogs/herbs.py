"""Herb preparation, den store, and compendium guide."""
from __future__ import annotations
import discord
from utils.replies import reply_ephemeral
from discord import app_commands
from discord.ext import commands
from cogs.care_handlers import denstore, dryall, herb_guide, prepare_herb_inventory, turnin_restricted
from utils.herb_autocomplete import herb_inventory_autocomplete
from utils.embeds import player_message, choice_label

class Herbs(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='herbs', description='herb drying, den store, guide, or poison turn-in.')
    @app_commands.describe(action='guide, prepare, dryall, store, or turnin', herb='inventory herb key (`herb_arnica`)', herb_filter='habitat filter for guide', prep_method='dry, poultice, tonic, or decoction (prepare)', mode='store: list, deposit, depositall, or withdraw', store_stack='store stack id to withdraw or turn in')
    @app_commands.choices(action=[app_commands.Choice(name='herb guide', value='guide'), app_commands.Choice(name='prepare herb', value='prepare'), app_commands.Choice(name='dry all (inventory + den store)', value='dryall'), app_commands.Choice(name='den herb store', value='store'), app_commands.Choice(name='turn in poison herbs', value='turnin')], herb_filter=[app_commands.Choice(name='all herbs', value='all'), app_commands.Choice(name='territory (wild)', value='wild'), app_commands.Choice(name='thunderpath verge', value='roadside'), app_commands.Choice(name='twoleg compound edge', value='compound')], prep_method=[app_commands.Choice(name='dry for storage', value='dry'), app_commands.Choice(name='poultice (chewed leaves)', value='poultice'), app_commands.Choice(name='tonic (crushed + water)', value='tonic'), app_commands.Choice(name='decoction (boiled / hot spring)', value='decoction')], mode=[app_commands.Choice(name='list store', value='list'), app_commands.Choice(name='deposit herb', value='deposit'), app_commands.Choice(name='deposit all herbs', value='depositall'), app_commands.Choice(name='withdraw herb', value='withdraw')])
    @app_commands.autocomplete(herb=herb_inventory_autocomplete)
    async def herbs(self, interaction: discord.Interaction, action: str, herb: str | None=None, herb_filter: str='all', prep_method: str='dry', mode: str='list', store_stack: str | None=None):
        if action == 'guide':
            await herb_guide(interaction, herb_filter)
        elif action == 'dryall':
            await dryall(interaction)
        elif action == 'store':
            await denstore(interaction, mode, store_stack, herb)
        elif action == 'turnin':
            await turnin_restricted(interaction, store_stack or herb)
        elif action == 'prepare':
            if not herb or not herb.strip().lower().startswith('herb_'):
                await interaction.response.send_message(player_message('Pick an inventory herb from autocomplete (e.g. **`herb_arnica`**).'), ephemeral=reply_ephemeral())
                return
            await prepare_herb_inventory(interaction, herb.strip().lower(), prep_method)
        else:
            await interaction.response.send_message(player_message('Pick a valid **action**.'), ephemeral=reply_ephemeral())

async def setup(bot: commands.Bot):
    await bot.add_cog(Herbs(bot))