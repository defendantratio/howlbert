import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.activities import try_fishing, try_forage, try_scavenge, try_track
from engine.verge_foraging import try_verge_forage
from engine.sniff import try_sniff
from utils.combat_views import make_combat_view
from engine.prey_storage import eat_prey_carcass, format_prey_hoard_footer, format_prey_hoard_line, salvage_prey_carcass
from engine.thirst import drink_at_creek
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message
from utils.views import make_hunt_followup_view

async def _prey_stack_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        return []
    world = db.get_world(interaction.guild.id)
    stacks = db.get_prey_stacks(user['id'])
    choices = []
    for stack in stacks:
        label = format_prey_hoard_line(stack, world['day_number'])
        if current and current not in label.lower() and (current not in str(stack['id'])):
            continue
        choices.append(app_commands.Choice(name=choice_label(label), value=str(stack['id'])))
    return choices[:25]

async def _territory_field_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if not interaction.guild:
        return []
    territories = db.get_territories(interaction.guild.id)
    choices = []
    for t in territories:
        label = f"{t['name']} ({t['key']})"
        if current and current.lower() not in label.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(label), value=t['key']))
    return choices[:25]

class Hunting(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='food', description='view carcasses in your food hoard (they rot over time).')
    async def food_hoard(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        stacks = db.get_prey_stacks(user['id'])
        if not stacks:
            embed = howlbert_embed('Empty Hoard', 'No carcasses yet.\n· `/bones action:hunt` or `collaborate:true` pack hunt\n· `/explore venture` · `/field action:track` · `action:fishing` · `action:scavenge`\n· `/world action:encounter`')
            embed.set_footer(text=format_prey_hoard_footer(empty=True))
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        lines = [format_prey_hoard_line(s, world['day_number']) for s in stacks]
        embed = howlbert_embed(f"{user['wolf_name']}; Food Hoard", '\n'.join(lines))
        embed.set_footer(text=format_prey_hoard_footer())
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @app_commands.command(name='eat', description='eat one use from a carcass in your hoard (−1 exhaustion, +hp).')
    @app_commands.describe(prey='stack id from `/food`')
    @app_commands.autocomplete(prey=_prey_stack_autocomplete)
    async def eat_prey(self, interaction: discord.Interaction, prey: str):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        try:
            stack_id = int(prey)
        except ValueError:
            await interaction.response.send_message(player_message('Pick a carcass from `/food` autocomplete.'), ephemeral=reply_ephemeral())
            return
        stack = db.get_prey_stack(stack_id)
        ok, msg = eat_prey_carcass(user, stack_id)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Meal', msg, color=color)
        if ok and stack and interaction.guild:
            from engine.prey_items import is_cannibal_prey, freshness_label
            day = db.get_world(interaction.guild.id)['day_number']
            fresh = freshness_label(stack['acquired_day'], day, stack['prey_key'], rotting=bool(stack['is_rotting']))
            footer = f'Was: {fresh}'
            if is_cannibal_prey(stack['prey_key']):
                footer += " · wolf meat risks mood if you're caught sharing"
            embed.set_footer(text=footer)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='drink', description='drink at the creek (once per hour, no daily cap).')
    async def drink_creek(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        ok, msg = drink_at_creek(user, day=world['day_number'], season=world['season'], guild_id=interaction.guild.id)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = 'Drink' if ok else 'Creek Cooldown' if 'min' in msg else 'Cannot Drink'
        embed = howlbert_embed(title, msg, color=color)
        if ok:
            embed.set_footer(text='thirst slips faster than hunger each sunrise; drink when you can.')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='salvage', description='salvage a rotting carcass into bones.')
    @app_commands.describe(prey='rotting stack id from `/food`')
    @app_commands.autocomplete(prey=_prey_stack_autocomplete)
    async def salvage_prey(self, interaction: discord.Interaction, prey: str):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        try:
            stack_id = int(prey)
        except ValueError:
            await interaction.response.send_message(player_message('Pick a rotting carcass from `/food`.'), ephemeral=reply_ephemeral())
            return
        ok, msg, bones = salvage_prey_carcass(user, stack_id)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Salvage', msg, color=color)
        if ok and bones:
            embed.add_field(name='Bones', value=f'+{bones} 🦴', inline=True)
            embed.set_footer(text='rotting carcass → bone toy (`/playpen action:toys`)')
        elif not ok:
            embed.set_footer(text='only **rotting** stacks salvage (`/food` shows status)')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='bury', description='bury a carcass from your hoard (optional ritual herbs mask death-scent).')
    @app_commands.describe(prey='stack id from `/food`', ritual_herb='lavender, rosemary, meadowsweet, or mint over the grave (optional)')
    @app_commands.choices(ritual_herb=[app_commands.Choice(name='no ritual herb', value='none'), app_commands.Choice(name='lavender', value='lavender'), app_commands.Choice(name='rosemary', value='rosemary'), app_commands.Choice(name='meadowsweet', value='meadowsweet'), app_commands.Choice(name='garden mint', value='garden_mint'), app_commands.Choice(name='water mint', value='watermint')])
    @app_commands.autocomplete(prey=_prey_stack_autocomplete)
    async def bury_prey(self, interaction: discord.Interaction, prey: str, ritual_herb: str='none'):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        try:
            stack_id = int(prey)
        except ValueError:
            await interaction.response.send_message(player_message('Pick a carcass from `/food` autocomplete.'), ephemeral=reply_ephemeral())
            return
        from engine.bury_ritual import bury_carcass
        world = db.get_world(interaction.guild.id)
        ok, body = bury_carcass(user, stack_id, day=world['day_number'], ritual_herb=None if ritual_herb == 'none' else ritual_herb)
        if not ok:
            await interaction.response.send_message(embed=howlbert_embed('Cannot Bury', body, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Buried', body, color=SUCCESS_COLOR)
        embed.set_footer(text='burial is final — no bones or salvage from buried carcasses.')
        await interaction.response.send_message(embed=embed)

    async def _sniff(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        await interaction.response.defer()
        embed, combat_enc = try_sniff(interaction)
        if combat_enc:
            view = make_combat_view(combat_enc, self.bot)
            await interaction.followup.send(embed=embed, view=view)
            return
        await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

    @app_commands.command(name='field', description='scavenge, track, fish, forage, verge-forage, mark territory, or sniff the wind.')
    @app_commands.describe(action='scavenge, track, fishing, forage, verge, mark, sniff, or compendium', rarity='herb rarity (territory forage only)', verge_site='roadside or twoleg compound (verge forage only)', trail_age='trail age (track only)', territory='territory key (mark only; see /pack territory)')
    @app_commands.choices(action=[app_commands.Choice(name='scavenge', value='scavenge'), app_commands.Choice(name='track', value='track'), app_commands.Choice(name='fishing', value='fishing'), app_commands.Choice(name='forage herbs (territory)', value='forage'), app_commands.Choice(name='forage verge (road / twoleg edge)', value='verge'), app_commands.Choice(name='mark territory scent', value='mark'), app_commands.Choice(name='sniff wind', value='sniff'), app_commands.Choice(name='herb compendium (read-only)', value='compendium')], trail_age=[app_commands.Choice(name='fresh (<1 hour) dc 8', value='fresh'), app_commands.Choice(name='recent (1-6 hours) dc 12', value='recent'), app_commands.Choice(name='cold (6-24 hours) dc 15', value='cold'), app_commands.Choice(name='very cold (1-3 days) dc 18', value='very_cold'), app_commands.Choice(name='faint (3+ days) dc 25', value='faint')], rarity=[app_commands.Choice(name='common (dc 8)', value='common'), app_commands.Choice(name='uncommon (dc 12)', value='uncommon'), app_commands.Choice(name='rare (dc 15)', value='rare'), app_commands.Choice(name='very rare (dc 20)', value='very_rare')], verge_site=[app_commands.Choice(name='thunderpath shoulder', value='roadside'), app_commands.Choice(name='twoleg compound fence-line', value='compound')])
    @app_commands.autocomplete(territory=_territory_field_autocomplete)
    async def field(self, interaction: discord.Interaction, action: str, rarity: str='common', verge_site: str='roadside', trail_age: str='recent', territory: str | None=None):
        if action == 'scavenge':
            await self._scavenge(interaction)
        elif action == 'track':
            await self._track(interaction, trail_age)
        elif action == 'fishing':
            await self._fishing(interaction)
        elif action == 'forage':
            await self._forage(interaction, rarity)
        elif action == 'verge':
            await self._verge_forage(interaction, verge_site)
        elif action == 'mark':
            await self._mark_territory(interaction, territory)
        elif action == 'sniff':
            await self._sniff(interaction)
        elif action == 'compendium':
            await self._herb_compendium(interaction)

    async def _mark_territory(self, interaction: discord.Interaction, territory: str | None):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(embed=howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        if not territory:
            await interaction.response.send_message(embed=howlbert_embed('Territory Required', 'Pick a territory key from `/pack territory` (e.g. `pine_ridge`).', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.territory_marking import mark_territory
        world = db.get_world(interaction.guild.id)
        embed = mark_territory(user, interaction.guild.id, world['day_number'], territory)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _herb_compendium(self, interaction: discord.Interaction):
        from engine.herb_guide import build_herb_guide_embed
        from utils.herb_views import make_herb_guide_view
        title, body = build_herb_guide_embed(page=0, filter_key='all')
        embed = howlbert_embed(title, body)
        embed.set_footer(text='herb compendium · /field action:compendium · read-only')
        view = make_herb_guide_view(page=0, filter_key='all')
        await interaction.response.send_message(embed=embed, view=view, ephemeral=reply_ephemeral())

    async def _scavenge(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = try_scavenge(interaction)
        if not embed:
            embed = howlbert_embed('Scavenge Failed', 'Something went wrong.', color=ERROR_COLOR)
        await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

    async def _track(self, interaction: discord.Interaction, trail_age: str='recent'):
        await interaction.response.defer()
        embed, show_prey = try_track(interaction, trail_age=trail_age)
        if not embed:
            embed = howlbert_embed('Track Failed', 'Something went wrong.', color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())
            return
        if show_prey and embed.color != ERROR_COLOR:
            await interaction.followup.send(embed=embed, view=make_hunt_followup_view())
        else:
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

    async def _fishing(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed, show_prey = try_fishing(interaction)
        if not embed:
            embed = howlbert_embed('Fishing Failed', 'Something went wrong.', color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())
            return
        if show_prey and embed.color != ERROR_COLOR:
            await interaction.followup.send(embed=embed, view=make_hunt_followup_view())
        else:
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

    async def _forage(self, interaction: discord.Interaction, rarity: str='common'):
        await interaction.response.defer()
        embed = try_forage(interaction, rarity)
        if not embed:
            embed = howlbert_embed('Forage Failed', 'Something went wrong.', color=ERROR_COLOR)
        await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

    async def _verge_forage(self, interaction: discord.Interaction, verge_site: str='roadside'):
        await interaction.response.defer()
        embed, combat_enc = try_verge_forage(interaction, verge_site)
        if not embed:
            embed = howlbert_embed('Forage Failed', 'Something went wrong.', color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())
            return
        if combat_enc:
            await interaction.followup.send(embed=embed, view=make_combat_view(combat_enc, self.bot))
        else:
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

async def setup(bot: commands.Bot):
    await bot.add_cog(Hunting(bot))