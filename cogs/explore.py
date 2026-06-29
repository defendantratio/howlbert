"""Wolvden-style explore, amusement, socialize, and raccoon trading."""
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from config import MOOD_LOW_THRESHOLD, RACCOON_BUNDLES, RACCOON_DAILY_BUYS, RACCOON_DAILY_SELLS, RACCOON_PREY_KEYS
from engine.amusement_items import amusement_meta
from engine.amusement_storage import format_amusement_line, grant_amusement, play_amusement
from engine.explore import try_explore
from engine.pack_play import run_playall
from utils.permissions import is_howlbert_admin
from engine.socialize import run_socialize
from engine.prey_items import prey_meta
from engine.prey_storage import format_prey_hoard_line
from utils.currency import format_bones
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label

async def _amusement_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    user = db.get_user(interaction.user.id)
    if not user:
        return []
    stacks = db.get_amusement_stacks(user['id'])
    choices = []
    for stack in stacks:
        label = format_amusement_line(stack)
        if current and current not in label.lower() and (current not in str(stack['id'])):
            continue
        choices.append(app_commands.Choice(name=choice_label(label), value=str(stack['id'])))
    return choices[:25]

async def _other_wolf_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    active = db.get_user(interaction.user.id)
    if not active:
        return []
    choices = []
    for wolf in db.list_user_wolves(interaction.user.id):
        if wolf['id'] == active['id']:
            continue
        name = wolf['wolf_name']
        if current and current.lower() not in name.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(name), value=name))
    return choices[:25]

def _resolve_own_wolf(discord_id: int, name: str):
    rows = db.list_user_wolves(discord_id)
    return next((w for w in rows if w['wolf_name'].lower() == name.strip().lower()), None)

async def _prey_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
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

class Explore(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    explore = app_commands.Group(name='explore', description='range the biome for loot.')

    @explore.command(name='venture', description='dig, follow scent, or investigate (scouts: unlimited · others once per sunrise).')
    @app_commands.describe(action='what you try in the wild')
    @app_commands.choices(action=[app_commands.Choice(name='🕳️ dig', value='dig'), app_commands.Choice(name='👃 follow scent', value='follow'), app_commands.Choice(name='🔍 investigate', value='investigate')])
    async def explore_venture(self, interaction: discord.Interaction, action: str):
        embed, combat_enc = try_explore(interaction, action)
        if not embed:
            await interaction.response.send_message(embed=howlbert_embed('Explore Failed', 'Something went wrong.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if combat_enc:
            from utils.combat_views import make_combat_view
            view = make_combat_view(combat_enc, self.bot)
            await interaction.response.send_message(embed=embed, view=view)
            return
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @app_commands.command(name='playpen', description='toys, play, socialize, groom, den romp, or toy store.')
    @app_commands.describe(action='toys, play, socialize, groom, playall, or toystore', mode='toystore: list, deposit, depositall, withdraw, or withdrawall', toy='toy stack (play / toystore deposit or withdraw)', wolf='packmate (socialize/groom)', own_wolf='your other wolf (socialize/groom)')
    @app_commands.choices(action=[app_commands.Choice(name='view toys', value='toys'), app_commands.Choice(name='play with toy', value='play'), app_commands.Choice(name='socialize', value='socialize'), app_commands.Choice(name='groom packmate', value='groom'), app_commands.Choice(name='play with whole den (alpha)', value='playall'), app_commands.Choice(name='den toy store', value='toystore')], mode=[app_commands.Choice(name='list store', value='list'), app_commands.Choice(name='deposit toy', value='deposit'), app_commands.Choice(name='deposit all toys', value='depositall'), app_commands.Choice(name='withdraw toy', value='withdraw'), app_commands.Choice(name='withdraw all toys', value='withdrawall')])
    @app_commands.autocomplete(toy=_amusement_autocomplete, own_wolf=_other_wolf_autocomplete)
    async def playpen(self, interaction: discord.Interaction, action: str, mode: str='list', toy: str | None=None, wolf: discord.Member | None=None, own_wolf: str | None=None):
        if action == 'toys':
            await self._toys(interaction)
        elif action == 'play':
            if not toy:
                await interaction.response.send_message(player_message('Pick a `toy` to play with.'), ephemeral=reply_ephemeral())
                return
            await self._play(interaction, toy)
        elif action == 'socialize':
            await self._socialize(interaction, wolf, own_wolf)
        elif action == 'groom':
            await self._groom(interaction, wolf, own_wolf)
        elif action == 'playall':
            await self._playall(interaction)
        elif action == 'toystore':
            await self._toystore(interaction, mode, toy)

    async def _toys(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        stacks = db.get_amusement_stacks(user['id'])
        mood = int(user['mood']) if 'mood' in user.keys() else 75
        if not stacks:
            embed = howlbert_embed('No Toys', f'Mood: **{mood}/100**\n\nNothing yet; try `/explore venture`.')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        lines = [format_amusement_line(s) for s in stacks]
        embed = howlbert_embed(f"{user['wolf_name']}; Amusement", '\n'.join(lines))
        embed.add_field(name='Mood', value=f'**{mood}**/100', inline=True)
        embed.set_footer(text='`/playpen action:play` · `action:toystore` · alpha: `action:playall` (uses your toys or den store)')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _toystore(self, interaction: discord.Interaction, mode: str, toy: str | None):
        user = db.get_user(interaction.user.id)
        if not user or not interaction.guild:
            await interaction.response.send_message(player_message('Use `/register` in a server.'), ephemeral=reply_ephemeral())
            return
        if not user['pack_id']:
            await interaction.response.send_message(embed=howlbert_embed('No Pack', 'Join a pack to use the den toy store.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.pack_amusement_store import deposit_all_amusement_to_store, deposit_amusement_to_store, list_pack_amusement_store, withdraw_all_amusement_from_store, withdraw_amusement_from_store
        if mode == 'list':
            body = list_pack_amusement_store(user['pack_id'])
            embed = howlbert_embed('Den Toy Store', body)
            embed.set_footer(text='anyone: `mode:deposit` / `depositall` / `withdraw` / `withdrawall`')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if mode == 'depositall':
            ok, msg = deposit_all_amusement_to_store(user, pack_id=user['pack_id'], guild_id=interaction.guild.id)
        elif mode == 'deposit':
            if not toy:
                await interaction.response.send_message(player_message('Pick a `toy` stack from `/playpen action:toys` to deposit.'), ephemeral=reply_ephemeral())
                return
            try:
                stack_id = int(toy)
            except ValueError:
                await interaction.response.send_message(player_message('Pick a toy from autocomplete.'), ephemeral=reply_ephemeral())
                return
            ok, msg = deposit_amusement_to_store(user, stack_id, pack_id=user['pack_id'], guild_id=interaction.guild.id)
        elif mode == 'withdraw':
            if not toy:
                await interaction.response.send_message(player_message('Enter store toy **`#ID`** from `mode:list` as the `toy` parameter.'), ephemeral=reply_ephemeral())
                return
            try:
                store_id = int(toy.strip().lstrip('#'))
            except ValueError:
                await interaction.response.send_message(player_message('Enter store stack **`#ID`** from `mode:list`.'), ephemeral=reply_ephemeral())
                return
            ok, msg = withdraw_amusement_from_store(user, store_id, pack_id=user['pack_id'])
        elif mode == 'withdrawall':
            ok, msg = withdraw_all_amusement_from_store(user, pack_id=user['pack_id'])
        else:
            await interaction.response.send_message(player_message('Pick **list**, **deposit**, **depositall**, **withdraw**, or **withdrawall**.'), ephemeral=reply_ephemeral())
            return
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Den Toy Store', msg, color=color))

    async def _play(self, interaction: discord.Interaction, toy: str):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        try:
            stack_id = int(toy)
        except ValueError:
            await interaction.response.send_message(player_message('Pick a toy from `/playpen action:toys`.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        ok, msg, _ = play_amusement(user, stack_id, day=day)
        if ok:
            db.update_user(interaction.user.id, last_play_day=world['day_number'], wolf_id=user['id'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Play', msg, color=color)
        if ok:
            embed.set_footer(text='/playpen action:toys · once per sunrise · /checklist')
        elif day is not None and 'already played' in msg.lower():
            embed.set_footer(text='/playpen action:socialize · /checklist')
        await interaction.response.send_message(embed=embed)

    async def _socialize(self, interaction: discord.Interaction, wolf: discord.Member | None=None, own_wolf: str | None=None):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        if wolf and own_wolf:
            await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Choose another **player** or `own_wolf`; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        partner = None
        if own_wolf:
            partner = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not partner:
                await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', 'No wolf with that name on your account. Check `/wolves`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if partner['id'] == user['id']:
                await interaction.response.send_message(embed=howlbert_embed('Same Wolf', 'Switch to another wolf with `/switchwolf`, or pick a different `own_wolf`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
        elif wolf:
            if wolf.bot or wolf.id == interaction.user.id:
                await interaction.response.send_message(embed=howlbert_embed('Pick Another Wolf', 'Use another **player**, or your other wolf via `own_wolf`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            partner = db.get_user(wolf.id)
            if not partner:
                await interaction.response.send_message(player_message("They haven't registered a wolf."), ephemeral=reply_ephemeral())
                return
        else:
            await interaction.response.send_message(embed=howlbert_embed('No Target', 'Pick another **player** or one of your wolves with `own_wolf`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not user['pack_id']:
            await interaction.response.send_message(embed=howlbert_embed('No Den', 'Join a great pack first; `/playpen` is a den activity.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.quarantine import is_quarantined, quarantine_activity_block
        block = quarantine_activity_block(user)
        if block:
            await interaction.response.send_message(embed=howlbert_embed('Quarantined', block, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.mental_effects import social_activity_block
        mind_block = social_activity_block(user)
        if mind_block:
            await interaction.response.send_message(embed=howlbert_embed('Mind Lost', mind_block, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if is_quarantined(partner):
            await interaction.response.send_message(embed=howlbert_embed('Sick Den', f"**{partner['wolf_name']}** is quarantined; no close contact.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        if int(user['last_socialize_day']) >= day:
            embed = howlbert_embed('Already Socialized', "You've mingled this sunrise.\n\n_Resets next sunrise · `/checklist`_", color=ERROR_COLOR)
            embed.set_footer(text='/bonds · /playpen action:groom · once per sunrise')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        db.update_user(interaction.user.id, last_socialize_day=day)
        cross_pack = user['pack_id'] != partner['pack_id']
        if cross_pack:
            from engine.pack_relations import cross_pack_social_risk

            fought, combat_enc = cross_pack_social_risk(user, partner, guild_id=interaction.guild.id, channel_id=interaction.channel_id)
            if fought and combat_enc:
                embed = howlbert_embed('Border Turns Ugly', f"You cross into **{partner['wolf_name']}**'s territory and the meeting turns to teeth; hostile ground doesn't forgive an open approach.", color=ERROR_COLOR)
                embed.set_footer(text='Hostile rival; combat panel below')
                from utils.combat_views import make_combat_view

                view = make_combat_view(combat_enc, self.bot)
                await interaction.response.send_message(embed=embed, view=view)
                return
        result = run_socialize(user, partner, pack_id=int(user['pack_id']), day=day, cross_pack=cross_pack)
        color = SUCCESS_COLOR if result['success'] else ERROR_COLOR
        embed = howlbert_embed('Socialize', result['body'], color=color)
        footer = '/bonds · once per sunrise · /checklist'
        if cross_pack:
            footer = '/bonds · cross-pack; no den unity change · once per sunrise'
        embed.set_footer(text=footer)
        await interaction.response.send_message(embed=embed)

    async def _groom(self, interaction: discord.Interaction, wolf: discord.Member | None=None, own_wolf: str | None=None):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        if wolf and own_wolf:
            await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Choose another **player** or `own_wolf`; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        partner = None
        if own_wolf:
            partner = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not partner:
                await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', 'No wolf with that name on your account. Check `/wolves`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if partner['id'] == user['id']:
                await interaction.response.send_message(embed=howlbert_embed('Same Wolf', 'Switch to another wolf with `/switchwolf`, or pick a different `own_wolf`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
        elif wolf:
            if wolf.bot or wolf.id == interaction.user.id:
                await interaction.response.send_message(embed=howlbert_embed('Pick Another Wolf', 'Use another **player**, or your other wolf via `own_wolf`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            partner = db.get_user(wolf.id)
            if not partner:
                await interaction.response.send_message(player_message("They haven't registered a wolf."), ephemeral=reply_ephemeral())
                return
        else:
            await interaction.response.send_message(embed=howlbert_embed('No Target', 'Pick another **player** or one of your wolves with `own_wolf`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not user['pack_id']:
            await interaction.response.send_message(embed=howlbert_embed('No Den', 'Join a great pack first; `/playpen` is a den activity.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.quarantine import is_quarantined, quarantine_activity_block
        block = quarantine_activity_block(user)
        if block:
            await interaction.response.send_message(embed=howlbert_embed('Quarantined', block, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.mental_effects import social_activity_block
        mind_block = social_activity_block(user)
        if mind_block:
            await interaction.response.send_message(embed=howlbert_embed('Mind Lost', mind_block, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if is_quarantined(partner):
            await interaction.response.send_message(embed=howlbert_embed('Sick Den', f"**{partner['wolf_name']}** is quarantined; no close contact.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        if int(user['last_groom_day']) >= day:
            embed = howlbert_embed('Already Groomed', "You've shared tongues this sunrise.\n\n_Resets next sunrise · `/checklist`_", color=ERROR_COLOR)
            embed.set_footer(text='/bonds · caretaker bonus on low mood · once per sunrise')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        db.update_user(interaction.user.id, last_groom_day=day)
        cross_pack = user['pack_id'] != partner['pack_id']
        if cross_pack:
            from engine.pack_relations import cross_pack_social_risk

            fought, combat_enc = cross_pack_social_risk(user, partner, guild_id=interaction.guild.id, channel_id=interaction.channel_id)
            if fought and combat_enc:
                embed = howlbert_embed('Border Turns Ugly', f"You cross into **{partner['wolf_name']}**'s territory and the meeting turns to teeth; hostile ground doesn't forgive an open approach.", color=ERROR_COLOR)
                embed.set_footer(text='Hostile rival; combat panel below')
                from utils.combat_views import make_combat_view

                view = make_combat_view(combat_enc, self.bot)
                await interaction.response.send_message(embed=embed, view=view)
                return
        from engine.role_features import caretaker_groom_mood_bonus, is_caretaker
        partner_mood = int(partner['mood']) if 'mood' in partner.keys() else 50
        partner_distressed = int(partner['distressed']) if 'distressed' in partner.keys() else 0
        if is_caretaker(user):
            mood_gain, soothe_line = caretaker_groom_mood_bonus(partner_mood, partner_distressed=bool(partner_distressed))
            if partner_distressed or partner_mood < 30:
                db.update_user(partner['discord_id'], wolf_id=partner['id'], distressed=0)
        else:
            mood_gain, soothe_line = (5, '')
        your_mood = db.adjust_mood(user['id'], mood_gain)
        their_mood = db.adjust_mood(partner['id'], mood_gain)
        heal = min(partner['max_hp'] - partner['hp'], 2)
        if heal > 0:
            db.set_user_conditions(partner['discord_id'], wolf_id=partner['id'], hp=partner['hp'] + heal)
        unity_line = ''
        if user['pack_id'] and not cross_pack:
            db.adjust_pack_unity(int(user['pack_id']), 1)
            unity_line = '\nDen unity **+1**.'
        from engine.disease_contract import try_spread_from_close_contact
        spread_notes = []
        for note in (try_spread_from_close_contact(user, partner), try_spread_from_close_contact(partner, user)):
            if note:
                spread_notes.append(note)
        spread_line = '\n' + '\n'.join(spread_notes) if spread_notes else ''
        from engine.bonds import apply_groom_bonds
        bond_note = apply_groom_bonds(user, partner, day=day)
        bond_line = f'\n{bond_note}' if bond_note else ''
        from engine.restricted_herbs import try_catch_hoarder_on_groom
        hoard_caught = try_catch_hoarder_on_groom(user, partner)
        hoard_line = f'\n\n{hoard_caught}' if hoard_caught else ''
        embed = howlbert_embed('Groom', f"You work burrs from **{partner['wolf_name']}**'s coat; **+{mood_gain} mood** each.\nYour mood: **{your_mood}** · Theirs: **{their_mood}**" + (f'\nThey gain **+{heal} HP** from the care.' if heal else '') + unity_line + spread_line + soothe_line + bond_line + hoard_line, color=SUCCESS_COLOR)
        footer = '/bonds · once per sunrise · /checklist'
        if cross_pack:
            footer = '/bonds · cross-pack; no den unity change · once per sunrise'
        embed.set_footer(text=footer)
        await interaction.response.send_message(embed=embed)

    async def _playall(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not user['pack_id']:
            await interaction.response.send_message(embed=howlbert_embed('No Pack', 'Join a Great Pack to rally a den romp.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        ok, msg = run_playall(user, user['pack_id'], world['day_number'], discord_admin=is_howlbert_admin(interaction))
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Play All', msg, color=color)
        if ok:
            embed.set_footer(text='alpha · once per sunrise · /checklist')
        elif not ok:
            embed.set_footer(text='/playpen action:play · /checklist')
        await interaction.response.send_message(embed=embed)
    raccoon = app_commands.Group(name='raccoon', description='sell small carcass scraps to the raccoon trader.')

    @raccoon.command(name='sell', description='sell a small carcass for bones (5 sales per sunrise).')
    @app_commands.describe(prey='vole, rabbit, hare, or fish from `/food`')
    @app_commands.autocomplete(prey=_prey_autocomplete)
    async def raccoon_sell(self, interaction: discord.Interaction, prey: str):
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
            await interaction.response.send_message(player_message('Pick a carcass from `/food`.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        sells = int(user['raccoon_sells_today']) if 'raccoon_sells_today' in user.keys() else 0
        if int(user['last_raccoon_day']) < day:
            sells = 0
        if sells >= RACCOON_DAILY_SELLS:
            embed = howlbert_embed('Raccoon Broke', f'The raccoon spent his purse for today (**{RACCOON_DAILY_SELLS}** sales max). Try again after sunrise.', color=ERROR_COLOR)
            embed.set_footer(text='/checklist · /raccoon buy')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        stack = db.get_prey_stack(stack_id)
        if not stack or stack['wolf_id'] != user['id']:
            await interaction.response.send_message(player_message("You don't carry that carcass."), ephemeral=reply_ephemeral())
            return
        if stack['prey_key'] not in RACCOON_PREY_KEYS:
            await interaction.response.send_message(embed=howlbert_embed("Won't Buy", 'The raccoon only wants **small** carcasses; vole, rabbit, hare, or fish. Salvage or `/preypile` the big kills.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        pay = min(12, max(2, stack['uses_left'] * 3))
        db.remove_prey_stack(stack_id)
        db.add_bones(interaction.user.id, pay, wolf_id=user['id'])
        db.update_user(interaction.user.id, last_raccoon_day=day, raccoon_sells_today=sells + 1)
        meta = prey_meta(stack['prey_key'])
        embed = howlbert_embed('Raccoon Wares', color=SUCCESS_COLOR)
        embed.description = f"The raccoon weighs **{meta['name']}**, flips a silver cone, and pays you **{format_bones(pay)}**.\nSales today: **{sells + 1}/{RACCOON_DAILY_SELLS}**"
        embed.set_footer(text='/raccoon buy · /food · /playpen action:toys')
        await interaction.response.send_message(embed=embed)

    @raccoon.command(name='buy', description='buy a toy bundle from the raccoon (3 purchases per sunrise).')
    @app_commands.describe(bundle='toy bundle to buy')
    @app_commands.choices(bundle=[app_commands.Choice(name='scrap bundle; bone + feather', value='scrap'), app_commands.Choice(name='plume bundle; feathers + shell', value='plume'), app_commands.Choice(name='gnaw bundle; bone + stick + acorn', value='gnaw')])
    async def raccoon_buy(self, interaction: discord.Interaction, bundle: str):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        spec = RACCOON_BUNDLES.get(bundle)
        if not spec:
            await interaction.response.send_message(player_message('Unknown bundle.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        buys = int(user['raccoon_buys_today']) if 'raccoon_buys_today' in user.keys() else 0
        if int(user['last_raccoon_day']) < day:
            buys = 0
        if buys >= RACCOON_DAILY_BUYS:
            embed = howlbert_embed('Raccoon Broke', f'No more bundles today (**{RACCOON_DAILY_BUYS}** buys max).', color=ERROR_COLOR)
            embed.set_footer(text='/checklist · /playpen action:toys')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if user['bones'] < spec['price']:
            await interaction.response.send_message(embed=howlbert_embed('Too Poor', f"Need **{spec['price']}** bones.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.add_bones(interaction.user.id, -spec['price'], wolf_id=user['id'])
        for toy_key in spec['toys']:
            grant_amusement(user['id'], toy_key)
        db.update_user(interaction.user.id, last_raccoon_day=day, raccoon_buys_today=buys + 1)
        toys = ', '.join((amusement_meta(k)['name'] for k in spec['toys']))
        embed = howlbert_embed('Raccoon Wares', color=SUCCESS_COLOR)
        embed.description = f"The raccoon flips a bundle; **{spec['name']}** for **{spec['price']}** bones.\nYou gain: {toys}\nBuys today: **{buys + 1}/{RACCOON_DAILY_BUYS}**"
        embed.set_footer(text='/playpen action:toys · /raccoon sell · /raccoon offer')
        await interaction.response.send_message(embed=embed)

    @raccoon.command(name='offer', description='offer an acorn to the raccoon; he trades a random toy (once per sunrise).')
    @app_commands.describe(toy='acorn stack from `/playpen action:toys`')
    @app_commands.autocomplete(toy=_amusement_autocomplete)
    async def raccoon_offer(self, interaction: discord.Interaction, toy: str):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        if int(user['last_raccoon_offer_day']) >= day:
            embed = howlbert_embed('Already Offered', 'The raccoon took an acorn this sunrise.\n\n_Resets next sunrise · `/checklist`_', color=ERROR_COLOR)
            embed.set_footer(text='/playpen action:toys · /raccoon sell')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        try:
            stack_id = int(toy)
        except ValueError:
            await interaction.response.send_message(player_message('Pick a toy from `/playpen action:toys`.'), ephemeral=reply_ephemeral())
            return
        stack = db.get_amusement_stack(stack_id)
        if not stack or stack['wolf_id'] != user['id'] or stack['item_key'] != 'acorn':
            await interaction.response.send_message(embed=howlbert_embed('Needs Acorn', 'The raccoon only haggles for **Acorn** toys.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        import random
        db.remove_amusement_stack(stack_id)
        reward_key = random.choice(['feather', 'shell', 'stick', 'bone', 'talon'])
        grant_amusement(user['id'], reward_key)
        db.update_user(interaction.user.id, last_raccoon_offer_day=day)
        meta = amusement_meta(reward_key)
        embed = howlbert_embed('Raccoon Trade', f"You set an acorn on his stone; he pushes back **{meta['name']}** with a silver cone wink.", color=SUCCESS_COLOR)
        embed.set_footer(text='once per sunrise · /playpen action:toys')
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Explore(bot))