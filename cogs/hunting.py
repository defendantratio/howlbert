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
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label
from utils.views import make_hunt_followup_view

async def _safe_defer(interaction: discord.Interaction) -> bool:
    """Defer, tolerating an already expired or duplicated interaction.

    Discord invalidates an interaction token after 3 seconds; if the gateway or
    event loop lagged, defer raises 404 (10062). Swallow it so the command fails
    quietly instead of crashing with a traceback; returns False when we can no
    longer respond.
    """
    try:
        await interaction.response.defer()
        return True
    except discord.HTTPException:
        return False


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


async def _drink_source_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Autocomplete for /drink source: owned territories, allied pack territories, active cat pacts."""
    if not interaction.guild:
        return []
    user = db.get_user(interaction.user.id)
    if not user or "pack_id" not in user.keys() or not user["pack_id"]:
        return []
    guild_id = interaction.guild.id
    pack_id = user["pack_id"]
    all_territories = db.get_territories(guild_id)
    choices: list[app_commands.Choice[str]] = []
    for t in all_territories:
        if t["owner_pack_id"] == pack_id:
            label = f"own territory: {t['name']}"
            if not current or current.lower() in label.lower():
                choices.append(app_commands.Choice(name=choice_label(label), value=t["key"]))
    ally_pack_ids = {row["other_pack_id"] for row in db.list_active_wolf_treaties(guild_id, pack_id)}
    for t in all_territories:
        if t["owner_pack_id"] in ally_pack_ids:
            label = f"ally territory: {t['name']} ({t['owner_name'] or '?'})"
            if not current or current.lower() in label.lower():
                choices.append(app_commands.Choice(name=choice_label(label), value=t["key"]))
    for pact in db.list_active_cat_pacts(guild_id, pack_id):
        clan = pact["clan_name"]
        label = f"cat clan: {clan}"
        if not current or current.lower() in label.lower():
            choices.append(app_commands.Choice(name=choice_label(label), value=f"clan:{clan}"))
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
            embed = howlbert_embed('Empty Hoard', 'No carcasses yet.\n· `/bones action:hunt` or `collaborate:true` pack hunt\n· `/explore` · `/field action:track` · `action:fishing` · `action:scavenge`\n· `/world action:encounter`')
            embed.set_footer(text=format_prey_hoard_footer(empty=True))
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        lines = [format_prey_hoard_line(s, world['day_number']) for s in stacks]
        embed = howlbert_embed(f"{user['wolf_name']}; Food Hoard", '\n'.join(lines))
        embed.set_footer(text=format_prey_hoard_footer())
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @app_commands.command(name='eat', description='eat one use from your hoard (−1 exhaustion, +hp).')
    @app_commands.describe(food='stack id from `/food`')
    @app_commands.autocomplete(food=_prey_stack_autocomplete)
    async def eat_prey(self, interaction: discord.Interaction, food: str):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        from engine.vitals_decay import apply_time_decay
        if apply_time_decay(user)[0]:
            user = db.get_user(interaction.user.id) or user
        try:
            stack_id = int(food)
        except ValueError:
            await interaction.response.send_message(player_message('Pick something from `/food` autocomplete.'), ephemeral=reply_ephemeral())
            return
        stack = db.get_prey_stack(stack_id)
        _eat_day = db.get_world(interaction.guild.id)['day_number'] if interaction.guild else 0
        ok, msg = eat_prey_carcass(user, stack_id, day=_eat_day)
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

    @app_commands.command(name='drink', description='drink water at the creek, or sip broth or milk (−exhaustion; feeds the injured).')
    @app_commands.describe(
        type='water (creek), broth, or milk',
        source='water only; Mistmoor: owned/allied territory or cat clan for clean water (skips swamp disease).',
    )
    @app_commands.choices(type=[
        app_commands.Choice(name='water (creek)', value='water'),
        app_commands.Choice(name='broth', value='broth'),
        app_commands.Choice(name='milk', value='milk'),
    ])
    @app_commands.autocomplete(source=_drink_source_autocomplete)
    async def drink_creek(self, interaction: discord.Interaction, type: str = 'water', source: str | None = None):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        from engine.vitals_decay import apply_time_decay
        if apply_time_decay(user)[0]:
            user = db.get_user(interaction.user.id) or user
        # broth / milk: sip a stored liquid instead of creek water
        if type in ('broth', 'milk'):
            from engine.liquid_diet import drink_liquid, LIQUID_HUNGER_CAP
            ok, msg = drink_liquid(user, type)
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            embed = howlbert_embed('Liquid Diet', msg, color=color)
            if ok:
                embed.set_footer(text=f'liquids feed to {LIQUID_HUNGER_CAP} hunger at most; only meat fully satisfies')
            await interaction.response.send_message(embed=embed)
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        guild_id = interaction.guild.id
        clean_water = False
        if source and user.get('pack_id'):
            pack_id = user['pack_id']
            if source.startswith('clan:'):
                clan_name = source[5:]
                pacts = db.list_active_cat_pacts(guild_id, pack_id)
                if any(p['clan_name'].lower() == clan_name.lower() for p in pacts):
                    clean_water = True
                else:
                    await interaction.response.send_message(
                        player_message(f'No active cat pact with **{clan_name}**; pick a territory or clan from the list.'),
                        ephemeral=reply_ephemeral(),
                    )
                    return
            else:
                territory = db.get_territory_by_key(guild_id, source)
                if not territory or not territory['owner_pack_id']:
                    await interaction.response.send_message(
                        player_message('That territory has no owner; pick from the autocomplete list.'),
                        ephemeral=reply_ephemeral(),
                    )
                    return
                owner_id = territory['owner_pack_id']
                if owner_id == pack_id:
                    clean_water = True
                else:
                    treaties = db.list_active_wolf_treaties(guild_id, pack_id)
                    if any(t['other_pack_id'] == owner_id for t in treaties):
                        clean_water = True
                    else:
                        await interaction.response.send_message(
                            player_message(f'**{territory["name"]}** is not owned by your pack or an active ally.'),
                            ephemeral=reply_ephemeral(),
                        )
                        return
        world = db.get_world(guild_id)
        ok, msg = drink_at_creek(user, day=world['day_number'], season=world['season'], guild_id=guild_id, clean_water=clean_water)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = 'Drink' if ok else 'Creek Cooldown' if 'min' in msg else 'Cannot Drink'
        embed = howlbert_embed(title, msg, color=color)
        if ok:
            embed.set_footer(text='hydration slips faster than hunger each sunrise; drink when you can.')
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
            embed.set_footer(text='only rotting stacks salvage (`/food` shows status)')
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
        embed.set_footer(text='burial is final; no bones or salvage from buried carcasses.')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='cache', description='personal food cache for packless wolves: bury a carcass to keep it, dig it up later, or list it.')
    @app_commands.describe(action='bury a hoard carcass, dig up a cache, or list your caches', stack='stack id (a `/food` carcass to bury, or a cache id from `action:list` to dig up)')
    @app_commands.choices(action=[app_commands.Choice(name='bury a carcass', value='bury'), app_commands.Choice(name='dig up a cache', value='dig'), app_commands.Choice(name='list caches', value='list')])
    @app_commands.autocomplete(stack=_prey_stack_autocomplete)
    async def cache(self, interaction: discord.Interaction, action: str, stack: str | None = None):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        from engine.role_features import is_unaffiliated_wolf
        if not is_unaffiliated_wolf(user):
            await interaction.response.send_message(embed=howlbert_embed('No Personal Cache', 'pack wolves share the den `/pack stash`; the buried personal cache is for **loners and rogues** with no den.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.prey_items import prey_meta
        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day = world['day_number'] if world else 0
        if action == 'list':
            cached = db.get_cached_prey_stacks(user['id'])
            if not cached:
                await interaction.response.send_message(embed=howlbert_embed('Empty Cache', 'nothing buried. bury a `/food` carcass with `/cache action:bury`.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
                return
            from config import LONER_CACHE_SLOTS
            lines = [f"**#{s['id']}** {prey_meta(s['prey_key'])['name']} · buried sunrise {s['cache_day']}" + (' · **rotting**' if s['is_rotting'] else '') for s in cached]
            embed = howlbert_embed(f"Buried Cache ({len(cached)}/{LONER_CACHE_SLOTS})", '\n'.join(lines))
            embed.set_footer(text='`/cache action:dig stack:<id>` to unearth · caches keep longer but can be pilfered')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not stack:
            await interaction.response.send_message(player_message('Pick a `stack` id.'), ephemeral=reply_ephemeral())
            return
        try:
            stack_id = int(stack)
        except ValueError:
            await interaction.response.send_message(player_message('Pick a carcass by stack id.'), ephemeral=reply_ephemeral())
            return
        row = db.get_prey_stack(stack_id)
        if not row or int(row['wolf_id']) != int(user['id']):
            await interaction.response.send_message(embed=howlbert_embed('Not Yours', 'that carcass is not in your hoard or cache.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if action == 'bury':
            if int(row['cached']):
                await interaction.response.send_message(embed=howlbert_embed('Already Buried', 'that carcass is already in your cache.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            from config import LONER_CACHE_SLOTS
            if db.count_cached_prey_stacks(user['id']) >= LONER_CACHE_SLOTS:
                await interaction.response.send_message(embed=howlbert_embed('Cache Full', f'you can bury at most **{LONER_CACHE_SLOTS}** carcasses. dig one up first.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            db.bury_prey_stack_in_cache(stack_id, day)
            from config import LONER_CACHE_ROT_MULT
            embed = howlbert_embed('Cached', f"you bury the **{prey_meta(row['prey_key'])['name']}** in a scrape and scent-mark it. it keeps roughly **{LONER_CACHE_ROT_MULT}x** longer than the open hoard.", color=SUCCESS_COLOR)
            embed.set_footer(text='dig it up with `/cache action:dig` before another scavenger finds it.')
            await interaction.response.send_message(embed=embed)
            return
        # dig
        if not int(row['cached']):
            await interaction.response.send_message(embed=howlbert_embed('Not Buried', 'that carcass is already in your open hoard.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.dig_prey_stack_from_cache(stack_id)
        embed = howlbert_embed('Unearthed', f"you dig up the **{prey_meta(row['prey_key'])['name']}**; back in your `/food` hoard.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    async def _sniff(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        if not await _safe_defer(interaction):
            return
        embed, combat_enc = try_sniff(interaction)
        if combat_enc:
            view = make_combat_view(combat_enc, self.bot)
            await interaction.followup.send(embed=embed, view=view)
            return
        await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

    @app_commands.command(name='field', description='scavenge, track, fish, forage, verge-forage, mark territory, or sniff.')
    @app_commands.describe(action='scavenge, track, fishing, forage, verge, mark, or sniff', rarity='herb rarity (territory forage only)', verge_site='roadside or twoleg compound (verge forage only)', trail_age='trail age (track only)', territory='territory key (mark only; see /pack territory)')
    @app_commands.choices(action=[app_commands.Choice(name='scavenge', value='scavenge'), app_commands.Choice(name='track', value='track'), app_commands.Choice(name='fishing', value='fishing'), app_commands.Choice(name='forage herbs (territory)', value='forage'), app_commands.Choice(name='forage verge (road / twoleg edge)', value='verge'), app_commands.Choice(name='mark territory scent', value='mark'), app_commands.Choice(name='sniff wind', value='sniff')], trail_age=[app_commands.Choice(name='fresh (<1 hour) dc 8', value='fresh'), app_commands.Choice(name='recent (1 to 6 hours) dc 12', value='recent'), app_commands.Choice(name='cold (6 to 24 hours) dc 15', value='cold'), app_commands.Choice(name='very cold (1 to 3 days) dc 18', value='very_cold'), app_commands.Choice(name='faint (3+ days) dc 25', value='faint')], rarity=[app_commands.Choice(name='common (dc 8)', value='common'), app_commands.Choice(name='uncommon (dc 12)', value='uncommon'), app_commands.Choice(name='rare (dc 15)', value='rare'), app_commands.Choice(name='very rare (dc 20)', value='very_rare')], verge_site=[app_commands.Choice(name='thunderpath shoulder', value='roadside'), app_commands.Choice(name='twoleg compound fence-line', value='compound')])
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

    async def _scavenge(self, interaction: discord.Interaction):
        if not await _safe_defer(interaction):
            return
        embed = try_scavenge(interaction)
        if not embed:
            embed = howlbert_embed('Scavenge Failed', 'Something went wrong.', color=ERROR_COLOR)
        await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

    async def _track(self, interaction: discord.Interaction, trail_age: str='recent'):
        if not await _safe_defer(interaction):
            return
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
        if not await _safe_defer(interaction):
            return
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
        if not await _safe_defer(interaction):
            return
        embed = try_forage(interaction, rarity)
        if not embed:
            embed = howlbert_embed('Forage Failed', 'Something went wrong.', color=ERROR_COLOR)
        await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

    async def _verge_forage(self, interaction: discord.Interaction, verge_site: str='roadside'):
        if not await _safe_defer(interaction):
            return
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