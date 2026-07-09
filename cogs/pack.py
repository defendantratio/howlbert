import random
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.pack_leadership import can_act_as_pack_alpha, can_act_as_pack_officer, can_resolve_war
from engine.pack_food import deposit_all_to_pack_stash, deposit_to_pack_stash, format_pack_stash_line, run_feedall, withdraw_from_pack_stash
from engine.thirst import run_drinkall
from engine.pack_unity import format_unity_meter, standing_effect_text, unity_effect_text
from engine.character import attr_modifier, get_attr
from config import CURRENCY_LABEL, GREAT_PACKS, MAX_PACK_TAX_RATE
from engine.prey_storage import format_prey_hoard_line
from utils.currency import format_bones
from utils.replies import reply_ephemeral
from utils.embeds import EMBED_COLOR, ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label
from utils.permissions import is_howlbert_admin
from utils.wolf_autocomplete import make_member_wolf_autocomplete

def _is_pack_officer(user, pack, *, discord_admin: bool=False) -> bool:
    return can_act_as_pack_officer(user, pack, discord_admin=discord_admin)

def _is_alpha(user, pack, *, discord_admin: bool=False) -> bool:
    return can_act_as_pack_alpha(user, pack, discord_admin=discord_admin)

_target_wolf_name_autocomplete = make_member_wolf_autocomplete("target")
_wolf_name_autocomplete = make_member_wolf_autocomplete("wolf")

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

async def _personal_prey_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
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

async def _pack_stash_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    user = db.get_user(interaction.user.id)
    if not user or not user['pack_id'] or (not interaction.guild):
        return []
    world = db.get_world(interaction.guild.id)
    stacks = db.get_pack_prey_stacks(user['pack_id'])
    choices = []
    for stack in stacks:
        label = format_pack_stash_line(stack, world['day_number'])
        if current and current not in label.lower() and (current not in str(stack['id'])):
            continue
        choices.append(app_commands.Choice(name=choice_label(label), value=str(stack['id'])))
    return choices[:25]

class Pack(commands.Cog):
    pack = app_commands.Group(name='pack', description='great pack treasury, tax, territory, and wars.')

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _require_pack_member(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return (None, None)
        if not user['pack_id']:
            embed = howlbert_embed('No Pack', 'Join a Great Pack with `/register` or `/setfaction`, or walk as a lone wolf.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return (None, None)
        pack = db.get_pack(user['pack_id'])
        if not pack:
            embed = howlbert_embed('Pack Not Found', "That Great Pack isn't in this den.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return (None, None)
        return (user, pack)

    @pack.command(name='treasury', description="view your pack's communal bone stash.")
    async def pack_treasury(self, interaction: discord.Interaction):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        embed = howlbert_embed(f"{pack['name']} Treasury", color=SUCCESS_COLOR)
        embed.add_field(name='Communal Bones', value=format_bones(pack['treasury']), inline=True)
        embed.add_field(name='Tax Rate', value=f"{pack['tax_rate']}%", inline=True)
        from engine.rollover_news import treasury_warning_line
        with db.get_db() as conn:
            member_count = conn.execute('SELECT COUNT(*) AS c FROM users WHERE pack_id = ?', (pack['id'],)).fetchone()['c']
        warn = treasury_warning_line(pack, member_count)
        if warn:
            embed.add_field(name='Warning', value=warn, inline=False)
        from engine.pack_season_goals import format_stash_goal_line
        if interaction.guild:
            world = db.get_world(interaction.guild.id)
            goal_line = format_stash_goal_line(pack, world['season'])
            if goal_line:
                embed.add_field(name='Season Goal', value=goal_line, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @pack.command(name='deposit', description='store bones in the pack treasury.')
    @app_commands.describe(amount='bones to deposit')
    async def pack_deposit(self, interaction: discord.Interaction, amount: int):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if amount <= 0:
            embed = howlbert_embed('Invalid Amount', 'Enter a positive number of bones.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not db.transfer_to_pack_treasury(interaction.user.id, pack['id'], amount):
            embed = howlbert_embed('Deposit Failed', 'Not enough bones.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        updated_pack = db.get_pack(pack['id'])
        updated_user = db.get_user(interaction.user.id)
        embed = howlbert_embed('Deposited', color=SUCCESS_COLOR)
        embed.add_field(name='Amount', value=format_bones(amount), inline=True)
        embed.add_field(name='Treasury', value=format_bones(updated_pack['treasury']), inline=True)
        embed.add_field(name='Your Balance', value=format_bones(updated_user['bones']), inline=True)
        # NOTE: do not also call db.increment_quest_progress(..., 'deposit') here;
        # transfer_to_pack_treasury already advances 'deposit' quests by the real
        # bone amount. Calling both double-counted progress on every deposit.
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @pack.command(name='withdraw', description='take bones from the pack treasury (alpha or advisor).')
    @app_commands.describe(amount='bones to withdraw')
    async def pack_withdraw(self, interaction: discord.Interaction, amount: int):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not _is_pack_officer(user, pack, discord_admin=is_howlbert_admin(interaction)):
            embed = howlbert_embed('Officers Only', 'Alpha or Advisor role required.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if amount <= 0:
            embed = howlbert_embed('Invalid Amount', 'Enter a positive number of bones.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not db.transfer_from_pack_treasury(interaction.user.id, pack['id'], amount):
            embed = howlbert_embed('Withdraw Failed', 'Treasury is too light.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        updated_pack = db.get_pack(pack['id'])
        updated_user = db.get_user(interaction.user.id)
        embed = howlbert_embed('Withdrawn', color=SUCCESS_COLOR)
        embed.add_field(name='Amount', value=format_bones(amount), inline=True)
        embed.add_field(name='Treasury', value=format_bones(updated_pack['treasury']), inline=True)
        embed.add_field(name='Your Balance', value=format_bones(updated_user['bones']), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
    stash = app_commands.Group(name='stash', description='shared den food reserve; rots slower than personal hoard.', parent=pack)

    @stash.command(name='list', description='view carcasses in the pack food reserve.')
    async def stash_list(self, interaction: discord.Interaction):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        stacks = db.get_pack_prey_stacks(pack['id'])
        if not stacks:
            embed = howlbert_embed(f"{pack['name']}; Food Reserve", 'Empty; deposit carcasses with **`/pack stash deposit`**.\nReserve meat rots **slower** than personal hoard.')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        lines = [format_pack_stash_line(s, world['day_number']) for s in stacks]
        fed_day = int(pack['last_feedall_day']) if 'last_feedall_day' in pack.keys() else 0
        drank_day = int(pack['last_drinkall_day']) if 'last_drinkall_day' in pack.keys() else 0
        fed_note = ' · fed this sunrise' if fed_day >= world['day_number'] else ''
        drank_note = ' · drank this sunrise' if drank_day >= world['day_number'] else ''
        embed = howlbert_embed(f"{pack['name']}; Food Reserve", '\n'.join(lines))
        embed.set_footer(text=f'alpha: `/packlife action:feedall` · `action:drinkall`{fed_note}{drank_note}')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @stash.command(name='deposit', description='add food from your hoard to the den reserve.')
    @app_commands.describe(food='stack id from `/food`')
    @app_commands.autocomplete(food=_personal_prey_autocomplete)
    async def stash_deposit(self, interaction: discord.Interaction, food: str):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        try:
            stack_id = int(food)
        except ValueError:
            await interaction.response.send_message(player_message('Pick something from `/food`.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        ok, msg = deposit_to_pack_stash(user, stack_id, pack_id=pack['id'], guild_id=interaction.guild.id, day=world['day_number'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        if ok:
            db.increment_quest_progress(interaction.user.id, 'deposit')
        await interaction.response.send_message(embed=howlbert_embed('Food Reserve', msg, color=color))

    @stash.command(name='depositall', description='deposit all fresh kills from your hoard to the den reserve.')
    async def stash_depositall(self, interaction: discord.Interaction):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        count, msg = deposit_all_to_pack_stash(user, pack_id=pack['id'], guild_id=interaction.guild.id, day=world['day_number'])
        color = SUCCESS_COLOR if count > 0 else ERROR_COLOR
        if count > 0:
            db.increment_quest_progress(interaction.user.id, 'deposit')
        await interaction.response.send_message(embed=howlbert_embed('Food Reserve', msg, color=color))

    @stash.command(name='withdraw', description='take food from the reserve into your hoard.')
    @app_commands.describe(food='stack id from `/pack stash list`')
    @app_commands.autocomplete(food=_pack_stash_autocomplete)
    async def stash_withdraw(self, interaction: discord.Interaction, food: str):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        try:
            stack_id = int(food)
        except ValueError:
            await interaction.response.send_message(player_message('Pick a stack from `/pack stash list`.'), ephemeral=reply_ephemeral())
            return
        ok, msg = withdraw_from_pack_stash(user, stack_id, pack_id=pack['id'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Food Reserve', msg, color=color))

    @app_commands.command(name='packlife', description='feed or water the whole den.')
    @app_commands.describe(action='feedall or drinkall')
    @app_commands.choices(action=[app_commands.Choice(name='feed all packmates', value='feedall'), app_commands.Choice(name='drink at creek (all)', value='drinkall')])
    async def packlife(self, interaction: discord.Interaction, action: str):
        if action == 'feedall':
            await self._feedall(interaction)
        elif action == 'drinkall':
            await self._drinkall(interaction)

    async def _feedall(self, interaction: discord.Interaction):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        ok, msg, _ = run_feedall(pack['id'], world['day_number'], caller=user, discord_admin=is_howlbert_admin(interaction))
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Feed All', msg, color=color))

    async def _drinkall(self, interaction: discord.Interaction):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        ok, msg, _ = run_drinkall(pack['id'], world['day_number'], caller=user, discord_admin=is_howlbert_admin(interaction))
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Drink All', msg, color=color))

    @pack.command(name='taxrate', description="view your pack's hunt tax rate.")
    async def pack_taxrate(self, interaction: discord.Interaction):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        embed = howlbert_embed(f"{pack['name']} Tax", f"**{pack['tax_rate']}%** of hunt earnings go to the treasury.")
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @pack.command(name='settax', description='set pack tax rate 0 to 25% (alpha only).')
    @app_commands.describe(rate='tax percentage on hunt earnings')
    async def pack_settax(self, interaction: discord.Interaction, rate: int):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not _is_alpha(user, pack, discord_admin=is_howlbert_admin(interaction)):
            embed = howlbert_embed('Alpha Only', 'Your active wolf must have the **Alpha** role and lead this pack.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if rate < 0 or rate > MAX_PACK_TAX_RATE:
            embed = howlbert_embed('Invalid Rate', f'Tax must be between 0 and {MAX_PACK_TAX_RATE}%.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        db.set_pack_tax_rate(pack['id'], rate)
        embed = howlbert_embed('Tax Updated', f'Pack tax is now **{rate}%**.', color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @pack.command(name='pardon', description='lift the rejoin cooldown for a wolf this den exiled (alpha only).')
    @app_commands.describe(wolf='the exiled wolf to pardon', wolf_name="specific wolf from that player's roster", own_wolf='your other wolf to pardon (multi-wolf players)')
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, wolf_name=_wolf_name_autocomplete)
    async def pack_pardon(self, interaction: discord.Interaction, wolf: discord.Member | None = None, wolf_name: str | None = None, own_wolf: str | None = None):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not _is_alpha(user, pack, discord_admin=is_howlbert_admin(interaction)):
            embed = howlbert_embed('Alpha Only', 'Your active wolf must have the **Alpha** role and lead this pack.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if wolf and own_wolf:
            await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use **wolf** or **own_wolf**; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if own_wolf:
            target = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not target:
                await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', 'No wolf with that name on your account. Check `/wolves`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
        elif wolf:
            if wolf_name:
                target = db.find_user_wolf(wolf.id, wolf_name)
            else:
                target = db.get_user(wolf.id)
            if not target:
                embed = howlbert_embed('Not Registered', f'{wolf.display_name} is not on Howlbert.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        else:
            await interaction.response.send_message(embed=howlbert_embed('No Target', 'Provide a **wolf** or **own_wolf** to pardon.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        ok = db.pardon_exile_by_wolf_id(target['id'], pack['id'])
        if not ok:
            embed = howlbert_embed('Nothing to Pardon', f"**{target['wolf_name']}** isn't under an exile from **{pack['name']}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Pardoned', f"**{target['wolf_name']}** may walk back into **{pack['name']}** with `/setfaction` whenever they choose.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    @pack.command(name='upgrade', description='spend treasury to improve the den; blunts bad-weather hunt penalties (alpha only).')
    async def pack_upgrade(self, interaction: discord.Interaction):
        from config import DEN_UPGRADE_MAX_LEVEL, DEN_UPGRADE_WEATHER_MITIGATION_PCT

        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not _is_alpha(user, pack, discord_admin=is_howlbert_admin(interaction)):
            embed = howlbert_embed('Alpha Only', 'Your active wolf must have the **Alpha** role and lead this pack.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        level = int(pack['den_upgrade_level']) if 'den_upgrade_level' in pack.keys() else 0
        if level >= DEN_UPGRADE_MAX_LEVEL:
            embed = howlbert_embed('Den Fully Upgraded', f"**{pack['name']}**'s den is already at the max (level **{level}**).", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        ok, new_level, cost = db.upgrade_den(pack['id'])
        if not ok:
            embed = howlbert_embed('Not Enough Bones', f"den upgrade to level **{level + 1}** needs **{format_bones(cost)}** in the treasury.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        mitigation = new_level * DEN_UPGRADE_WEATHER_MITIGATION_PCT
        embed = howlbert_embed('Den Upgraded', f"**{pack['name']}**'s den is now level **{new_level}**; bad weather costs **{mitigation}%** less on hunts. spent **{format_bones(cost)}**.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    @pack.command(name='territory', description='view territory held across the wild.')
    async def pack_territory(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        territories = db.get_territories(interaction.guild.id)
        lines = []
        for t in territories:
            owner = t['owner_name'] or 'Unclaimed'
            lines.append(f"**{t['name']}** (`{t['key']}`); {owner} · +{t['daily_bonus']}🦴/rollover")
        embed = howlbert_embed('Territory Map', '\n'.join(lines) if lines else 'No territories mapped.')
        await interaction.response.send_message(embed=embed)

    @pack.command(name='challenge', description='challenge for control of a territory (alpha only).')
    @app_commands.describe(territory='territory key from /pack territory')
    async def pack_challenge(self, interaction: discord.Interaction, territory: str):
        user, pack = await self._require_pack_member(interaction)
        if not user or not interaction.guild:
            return
        if not _is_alpha(user, pack, discord_admin=is_howlbert_admin(interaction)):
            embed = howlbert_embed('Alpha Only', 'Your active wolf must have the **Alpha** role and lead this pack.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        terr = db.get_territory_by_key(interaction.guild.id, territory)
        if not terr:
            embed = howlbert_embed('Unknown Territory', 'Check `/pack territory`.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if terr['owner_pack_id'] == pack['id']:
            embed = howlbert_embed('Already Yours', 'Your pack holds this ground.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if db.territory_has_active_war(interaction.guild.id, terr['id']):
            embed = howlbert_embed('War Underway', 'This territory is already contested.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if db.get_active_war_for_pack(interaction.guild.id, pack['id']):
            embed = howlbert_embed('Already at War', 'Your pack is in another conflict.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        day = db.get_world(interaction.guild.id)['day_number']
        db.start_war(interaction.guild.id, terr['id'], pack['id'], terr['owner_pack_id'], day)
        defender = 'unclaimed wilds' if not terr['owner_pack_id'] else 'the defending pack'
        embed = howlbert_embed('War Declared', f"**{pack['name']}** challenges **{terr['name']}** held by {defender}.\nEarn points with `/pack patrol` and `/pack scout`. The **Alpha** or a **Diplomat** ends the war with `/pack resolvewar` when the fight is decided.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    @pack.command(name='resolvewar', description='alpha or diplomat; end the active war and award territory by score.')
    async def pack_resolvewar(self, interaction: discord.Interaction):
        user, pack = await self._require_pack_member(interaction)
        if not user or not interaction.guild:
            return
        if not can_resolve_war(user, pack, discord_admin=is_howlbert_admin(interaction)):
            embed = howlbert_embed('Denied', 'Only the pack **Alpha** or a **Diplomat** can resolve a war.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        war = db.get_active_war_for_pack(interaction.guild.id, pack['id'])
        if not war:
            embed = howlbert_embed('No Active War', "Your pack isn't fighting for territory.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        status = db.resolve_war(war['id'])
        if not status:
            embed = howlbert_embed('Resolve Failed', "This war can't be resolved yet (needs 2 rollovers or invalid state).", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        attacker = db.get_pack(war['attacker_pack_id'])
        defender = db.get_pack(war['defender_pack_id']) if war['defender_pack_id'] else None
        attacker_name = attacker['name'] if attacker else 'Attackers'
        defender_name = defender['name'] if defender else 'the wilds'
        if status == 'won_attacker':
            outcome = f"**{attacker_name}** takes **{war['territory_name']}**."
        elif status == 'won_defender':
            outcome = f"**{defender_name}** holds **{war['territory_name']}**."
        else:
            outcome = f"**{war['territory_name']}**; neither side breaks the line. Status quo."
        embed = howlbert_embed('War Resolved', outcome, color=SUCCESS_COLOR)
        embed.add_field(name='Final Score', value=f"Attack {war['attacker_score']}; Defend {war['defender_score']}", inline=False)
        await interaction.response.send_message(embed=embed)

    async def _war_action(self, interaction: discord.Interaction, day_column: str, action_label: str, points_fn):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        war = db.get_active_war_for_pack(interaction.guild.id, pack['id'])
        if not war:
            embed = howlbert_embed('No Active War', "Your pack isn't fighting for territory.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        user = db.get_user(interaction.user.id)
        from engine.diminishing import next_use_multiplier
        _pat_mult, _pat_n = next_use_multiplier(user, day_column, day)
        points = points_fn(user)
        if _pat_n > 1:
            points = max(1, int(points * _pat_mult))
        db.add_war_score(war['id'], pack['id'], points)
        db.increment_quest_progress(interaction.user.id, 'patrol', guild_id=interaction.guild.id)
        db.update_user(interaction.user.id, **{day_column: day})
        war = db.get_active_war_for_pack(interaction.guild.id, pack['id'])
        embed = howlbert_embed(f'{action_label} Complete', color=SUCCESS_COLOR)
        embed.add_field(name='Territory', value=war['territory_name'], inline=True)
        embed.add_field(name='Points Earned', value=str(points), inline=True)
        embed.add_field(name='Score', value=f"Attack {war['attacker_score']}; Defend {war['defender_score']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @pack.command(name='patrol', description='patrol contested territory during a pack war.')
    @app_commands.describe(collaborate='call a collab war patrol; packmates join via buttons (2 to 4 wolves)')
    async def pack_patrol(self, interaction: discord.Interaction, collaborate: bool=False):
        if collaborate:
            from cogs.collab_patrol import post_collab_war_patrol_call
            await post_collab_war_patrol_call(interaction, self.bot)
            return
        await self._war_action(interaction, 'last_patrol_day', 'Patrol', lambda u: random.randint(2, 5) + max(0, attr_modifier(get_attr(u, 'con'))))

    @pack.command(name='scout', description='scout enemy movements during a pack war.')
    async def pack_scout(self, interaction: discord.Interaction):
        await self._war_action(interaction, 'last_scout_day', 'Scout', lambda u: random.randint(1, 4) + max(0, attr_modifier(get_attr(u, 'wis'))))

    @pack.command(name='unity', description="view your den's pack unity (−5 to 10).")
    async def pack_unity(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user or not user['pack_id']:
            embed = howlbert_embed('No Pack', 'Lone wolves have no pack unity. Join a Great Pack with `/setfaction`.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        pack = db.get_pack(user['pack_id'])
        unity = pack['pack_unity'] if 'pack_unity' in pack.keys() else 5
        embed = howlbert_embed(f"{pack['name']}; Pack Unity", color=SUCCESS_COLOR)
        embed.add_field(name='Unity', value=format_unity_meter(unity), inline=True)
        embed.add_field(name='Effect', value=unity_effect_text(unity), inline=False)
        if interaction.guild:
            from engine.pack_season_goals import format_stash_goal_line
            world = db.get_world(interaction.guild.id)
            goal_line = format_stash_goal_line(pack, world['season'])
            if goal_line:
                embed.add_field(name='Season Goal', value=goal_line, inline=False)
        embed.set_footer(text='gain: /howl, den charms, fresh-kill, pups, winning wars. loss: losing wars, declaring war. at −5: pack dissolves.')
        await interaction.response.send_message(embed=embed)

    @pack.command(name='relations', description='rival standing with neighboring dens (0 to 10).')
    async def pack_relations(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user or not user['pack_id']:
            embed = howlbert_embed('No Pack', 'Join a Great Pack first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        rows = db.list_pack_relations(interaction.guild.id, user['pack_id'])
        if not rows:
            embed = howlbert_embed('No Rivals Tracked', 'Neutral (5) with all packs until relations change through war or diplomacy.')
            await interaction.response.send_message(embed=embed)
            return
        lines = []
        for row in rows:
            standing = row['standing']
            from engine.pack_relations import relation_tag_label
            tag = relation_tag_label(standing)
            lines.append(f"**{row['other_pack_name']}**; {standing}/10 ({tag})")
        lines.append('\n**Effects:** ≥8 friendly (share hunts) · ≤3 hostile (attack on sight) · **0 war** (constant skirmishes; auto territory war when no conflict is active).')
        lines.append('_Change standing: share territory (+1), help vs enemy (+2), diplomatic howl (+1); fight over prey (−1), scent over-mark (−2), kill rival (−3). At **0**, a border war opens automatically unless your den is already at war._')
        embed = howlbert_embed('Rival Relations', '\n'.join(lines))
        embed.set_footer(text='`/pack relation` · `/pack howl` · `/pack share` · `/pack aid`')
        await interaction.response.send_message(embed=embed)

    @pack.command(name='relation', description='check standing with another great pack.')
    @app_commands.describe(pack_name='greyspire, mistmoor, thistlehide, or silverrush')
    async def pack_relation(self, interaction: discord.Interaction, pack_name: str):
        user = db.get_user(interaction.user.id)
        if not user or not user['pack_id']:
            embed = howlbert_embed('No Pack', 'Join a Great Pack first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        other = db.get_pack_by_name(pack_name)
        if not other:
            embed = howlbert_embed('Unknown Den', f'No pack named **{pack_name}**.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        standing = db.get_pack_relation(interaction.guild.id, user['pack_id'], other['id'])
        from engine.pack_relations import relation_effect_text, relation_tag_label
        embed = howlbert_embed(f"Relation: {other['name']}", f'Standing: **{standing}/10** ({relation_tag_label(standing)})\n\n{relation_effect_text(standing)}')
        await interaction.response.send_message(embed=embed)

    async def _great_pack_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        choices = []
        for key, info in GREAT_PACKS.items():
            label = info['name']
            if current and current.lower() not in label.lower() and (current.lower() not in key):
                continue
            choices.append(app_commands.Choice(name=choice_label(label), value=key))
        return choices[:25]

    @pack.command(name='audit', description='guard/alpha treasury audit after a rival raid (recover bones).')
    async def pack_audit(self, interaction: discord.Interaction):
        user, pack = await self._require_pack_member(interaction)
        if not user or not interaction.guild:
            return
        world = db.get_world(interaction.guild.id)
        from engine.pack_raid_ecology import try_treasury_audit
        embed = try_treasury_audit(interaction, user, pack, world['day_number'])
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @pack.command(name='accuse', description='alpha/beta name a rival den for a treasury raid.')
    @app_commands.describe(target_pack='which great pack you accuse')
    @app_commands.autocomplete(target_pack=_great_pack_autocomplete)
    async def pack_accuse(self, interaction: discord.Interaction, target_pack: str):
        user, pack = await self._require_pack_member(interaction)
        if not user or not interaction.guild:
            return
        world = db.get_world(interaction.guild.id)
        from engine.pack_raid_ecology import try_raid_accuse
        embed = try_raid_accuse(interaction, user, pack, target_pack, world['day_number'])
        await interaction.response.send_message(embed=embed)

    @pack.command(name='howl', description='diplomatic howl to a rival great pack (+1 standing on success).')
    @app_commands.describe(target_pack='greyspire, mistmoor, thistlehide, or silverrush')
    @app_commands.autocomplete(target_pack=_great_pack_autocomplete)
    async def pack_diplomatic_howl(self, interaction: discord.Interaction, target_pack: str):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        from engine.pack_diplomacy import diplomatic_howl
        world = db.get_world(interaction.guild.id)
        ok, msg = diplomatic_howl(user, pack, guild_id=interaction.guild.id, day=world['day_number'], target_pack=target_pack, weather=world['weather'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = 'Diplomatic Howl' if ok else 'Howl Unanswered'
        embed = howlbert_embed(title, msg, color=color)
        if ok:
            from engine.pack_relations import relation_effect_text
            target_row = db.get_pack_by_key(target_pack.strip().lower())
            if target_row:
                rel = db.get_pack_relation(interaction.guild.id, pack['id'], target_row['id'])
                embed.set_footer(text=relation_effect_text(rel))
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @pack.command(name='share', description='share hunting territory with a rival pack (+1 standing; spends energy).')
    @app_commands.describe(target_pack='greyspire, mistmoor, thistlehide, or silverrush')
    @app_commands.autocomplete(target_pack=_great_pack_autocomplete)
    async def pack_share(self, interaction: discord.Interaction, target_pack: str):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        from engine.pack_diplomacy import share_territory
        world = db.get_world(interaction.guild.id)
        ok, msg = share_territory(user, pack, guild_id=interaction.guild.id, day=world['day_number'], target_pack=target_pack)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Territory Shared' if ok else 'Share Failed', msg, color=color)
        if ok:
            from engine.pack_relations import relation_effect_text
            target_row = db.get_pack_by_key(target_pack.strip().lower())
            if target_row:
                rel = db.get_pack_relation(interaction.guild.id, pack['id'], target_row['id'])
                embed.set_footer(text=relation_effect_text(rel))
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @pack.command(name='aid', description='aid a rival pack at war (+2 standing when they have an active war).')
    @app_commands.describe(target_pack='greyspire, mistmoor, thistlehide, or silverrush')
    @app_commands.autocomplete(target_pack=_great_pack_autocomplete)
    async def pack_aid(self, interaction: discord.Interaction, target_pack: str):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        from engine.pack_diplomacy import aid_rival_pack
        world = db.get_world(interaction.guild.id)
        ok, msg = aid_rival_pack(user, pack, guild_id=interaction.guild.id, day=world['day_number'], target_pack=target_pack)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Aid Sent' if ok else 'Aid Failed', msg, color=color)
        if ok:
            from engine.pack_relations import relation_effect_text
            target_row = db.get_pack_by_key(target_pack.strip().lower())
            if target_row:
                rel = db.get_pack_relation(interaction.guild.id, pack['id'], target_row['id'])
                embed.set_footer(text=relation_effect_text(rel))
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @pack.command(name='tradepack', description='trade all duplicate hoard items to a wolf in another great pack.')
    @app_commands.describe(wolf='wolf in another pack (must accept standing)', wolf_name="specific wolf from that player's roster", own_wolf='your other wolf in another pack (multi-wolf players)', pack_name='their great pack name (optional check)')
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, wolf_name=_wolf_name_autocomplete)
    async def pack_tradepack(self, interaction: discord.Interaction, wolf: discord.Member | None = None, wolf_name: str | None = None, own_wolf: str | None = None, pack_name: str | None = None):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        if wolf and own_wolf:
            await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use **wolf** or **own_wolf**; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if own_wolf:
            recipient = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not recipient:
                await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', 'No wolf with that name on your account. Check `/wolves`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if recipient['id'] == user['id']:
                await interaction.response.send_message(embed=howlbert_embed('Same Wolf', 'Switch active wolf with `/switchwolf`, or pick a different `own_wolf`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
        elif wolf:
            if wolf.bot or wolf.id == interaction.user.id:
                await interaction.response.send_message(embed=howlbert_embed('Invalid Target', 'Pick another wolf.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if wolf_name:
                recipient = db.find_user_wolf(wolf.id, wolf_name)
            else:
                recipient = db.get_user(wolf.id)
            if not recipient:
                await interaction.response.send_message(embed=howlbert_embed('Not Registered', 'They have no wolf.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
        else:
            await interaction.response.send_message(embed=howlbert_embed('No Target', 'Provide a **wolf** or **own_wolf**.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if pack_name:
            other = db.get_pack_by_name(pack_name)
            if not other or recipient['pack_id'] != other['id']:
                await interaction.response.send_message(embed=howlbert_embed('Wrong Pack', f"**{recipient['wolf_name']}** is not in **{pack_name}**.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
        world = db.get_world(interaction.guild.id)
        from engine.duplicate_trade import trade_duplicates_between_wolves
        ok, msg = trade_duplicates_between_wolves(user, recipient, guild_id=interaction.guild.id, day=world['day_number'], require_pack_trade=True)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Pack Duplicate Trade' if ok else 'Trade Failed', msg, color=color)
        if ok:
            embed.set_footer(text='/pack relation · /trade duplicates · packmates')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @pack.command(name='brokenrite', description='read the latest rite of the broken canine in your great pack.')
    async def pack_brokenrite(self, interaction: discord.Interaction):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        import json
        from engine.broken_canine import RITE_NAME
        row = db.get_latest_broken_canine_rite(pack['id'])
        if not row:
            embed = howlbert_embed(
                RITE_NAME,
                "No leadership rite has been recorded for this pack yet.\n\nThere are no heirs in this den; the "
                "Alpha's seat is earned through combat. When an **Alpha**'s standing falls to **−5**, or the seat "
                "simply opens with more than one eligible wolf left to claim it, the pack holds the rite; every "
                "eligible wolf fights; the winner becomes Alpha.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        logs = json.loads(row['log_json'])
        embed = howlbert_embed(RITE_NAME, '\n'.join(logs))
        embed.set_footer(text=f"sunrise {row['triggered_day']} · outcome: {row['outcome']}")
        await interaction.response.send_message(embed=embed)

    @pack.command(name='judge', description='dissent, view dissents, denounce a packmate, or second a denouncement.')
    @app_commands.describe(action='dissent, dissents, denounce, or second', target='the packmate (denounce/second)', target_wolf_name="specific wolf from that player's roster", own_wolf='your other wolf as target (multi-wolf players)', subject='decision you object to (dissent)', reason='why (dissent/denounce)')
    @app_commands.choices(action=[app_commands.Choice(name='file dissent (officer only)', value='dissent'), app_commands.Choice(name='view recorded dissents', value='dissents'), app_commands.Choice(name='denounce a packmate', value='denounce'), app_commands.Choice(name='second a denouncement', value='second')])
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, target_wolf_name=_target_wolf_name_autocomplete)
    async def pack_judge(self, interaction: discord.Interaction, action: str, target: discord.Member | None = None, target_wolf_name: str | None = None, own_wolf: str | None = None, subject: str | None = None, reason: str | None = None):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if action == 'dissent':
            if not subject or not reason:
                await interaction.response.send_message(player_message('Provide **subject** and **reason**.'), ephemeral=reply_ephemeral())
                return
            if not _is_pack_officer(user, pack, discord_admin=is_howlbert_admin(interaction)):
                embed = howlbert_embed('Officers Only', 'Alpha, Advisor, or Diplomat role required to formally dissent.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            day = db.get_world(interaction.guild.id)['day_number'] if interaction.guild else 0
            db.record_pack_dissent(
                pack_id=pack['id'],
                dissenter_wolf_id=user['id'],
                dissenter_name=user['wolf_name'],
                subject=subject.strip()[:120],
                reason=reason.strip()[:300],
                day=day,
            )
            embed = howlbert_embed(
                'Dissent Recorded',
                f"**{user['wolf_name']}** formally objects to **{subject.strip()[:120]}**:\n_{reason.strip()[:300]}_\n\n"
                "on the record. it changes nothing by itself; but the den remembers who spoke against it.",
                color=EMBED_COLOR,
            )
            await interaction.response.send_message(embed=embed)
            return

        if action == 'dissents':
            rows = db.list_recent_pack_dissents(pack['id'], limit=8)
            if not rows:
                embed = howlbert_embed('No Dissents', 'No officer has formally objected to a den decision yet.\n\nUse `/pack judge action:dissent` to put one on record.')
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            lines = [
                f"sunrise **{row['day']}**; **{row['dissenter_name']}** on **{row['subject']}**: _{row['reason']}_"
                for row in rows
            ]
            embed = howlbert_embed(f"{pack['name']}; Recorded Dissents", '\n\n'.join(lines))
            await interaction.response.send_message(embed=embed)
            return

        if action in ('denounce', 'second'):
            if target and own_wolf:
                await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use **target** or **own_wolf**; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if own_wolf:
                target_row = _resolve_own_wolf(interaction.user.id, own_wolf)
                if not target_row:
                    await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', 'No wolf with that name on your account. Check `/wolves`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                    return
                if target_row['id'] == user['id']:
                    await interaction.response.send_message(embed=howlbert_embed('Same Wolf', 'Switch active wolf with `/switchwolf`, or pick a different `own_wolf`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                    return
            elif target:
                if target.bot or target.id == interaction.user.id:
                    await interaction.response.send_message(embed=howlbert_embed('Pick Another Wolf', 'You cannot target yourself.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                    return
                if target_wolf_name:
                    target_row = db.find_user_wolf(target.id, target_wolf_name)
                else:
                    target_row = db.get_user(target.id)
            else:
                await interaction.response.send_message(player_message('Pick a **target** packmate or your own wolf via `own_wolf`.'), ephemeral=reply_ephemeral())
                return

        if action == 'denounce':
            if not reason:
                await interaction.response.send_message(player_message('Provide a **reason**.'), ephemeral=reply_ephemeral())
                return
            if not target_row or target_row['pack_id'] != pack['id']:
                target_label = own_wolf or (target.display_name if target else '?')
                await interaction.response.send_message(embed=howlbert_embed('Not a Packmate', f'**{target_label}** is not in **{pack["name"]}**.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if db.get_open_denouncement_for_target(pack['id'], target_row['id']):
                await interaction.response.send_message(embed=howlbert_embed('Already Open', f"**{target_row['wolf_name']}** already has an open denouncement; use `action:second` to back it.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            from config import DENOUNCEMENT_SECONDS_REQUIRED
            day = db.get_world(interaction.guild.id)['day_number'] if interaction.guild else 0
            denouncement_id = db.create_denouncement(
                pack_id=pack['id'],
                target_wolf_id=target_row['id'],
                target_name=target_row['wolf_name'],
                denouncer_wolf_id=user['id'],
                denouncer_name=user['wolf_name'],
                reason=reason.strip()[:300],
                day=day,
            )
            embed = howlbert_embed(
                'Denouncement Raised',
                f"**{user['wolf_name']}** denounces **{target_row['wolf_name']}**:\n_{reason.strip()[:300]}_\n\n"
                f"this costs **{target_row['wolf_name']}** nothing yet; it needs **{DENOUNCEMENT_SECONDS_REQUIRED}** "
                f"other packmates to second it before the den actually acts on it.",
                color=EMBED_COLOR,
            )
            embed.set_footer(text=f'denouncement #{denouncement_id}')
            await interaction.response.send_message(embed=embed)
            return

        if action == 'second':
            if not target_row or target_row['pack_id'] != pack['id']:
                target_label = own_wolf or (target.display_name if target else '?')
                await interaction.response.send_message(embed=howlbert_embed('Not a Packmate', f'**{target_label}** is not in **{pack["name"]}**.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            row = db.get_open_denouncement_for_target(pack['id'], target_row['id'])
            if not row:
                await interaction.response.send_message(embed=howlbert_embed('Nothing Open', f"No open denouncement against **{target_row['wolf_name']}**. Start one with `action:denounce`.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if user['id'] in (row['denouncer_wolf_id'], target_row['id']):
                await interaction.response.send_message(embed=howlbert_embed('Cannot Second', 'The original denouncer and the accused cannot second this.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            new_count = db.second_denouncement(row['id'], user['id'])
            if new_count is None:
                await interaction.response.send_message(embed=howlbert_embed('Already Seconded', "You've already backed this denouncement.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            from config import DENOUNCEMENT_SECONDS_REQUIRED, DENOUNCEMENT_STANDING_PENALTY
            if new_count >= DENOUNCEMENT_SECONDS_REQUIRED:
                db.resolve_denouncement(row['id'])
                kick = db.adjust_wolf_standing_by_id(target_row['id'], DENOUNCEMENT_STANDING_PENALTY)
                standing_note = '**cast out**' if kick == 'kicked' else f'standing **{DENOUNCEMENT_STANDING_PENALTY}**'
                embed = howlbert_embed(
                    'Denouncement Upheld',
                    f"**{new_count}** packmates seconded it; the den acts.\n**{target_row['wolf_name']}**: {standing_note}.\n_{row['reason']}_",
                    color=ERROR_COLOR,
                )
            else:
                embed = howlbert_embed(
                    'Second Recorded',
                    f"**{user['wolf_name']}** backs the denouncement of **{target_row['wolf_name']}** "
                    f"(**{new_count}/{DENOUNCEMENT_SECONDS_REQUIRED}**).",
                    color=EMBED_COLOR,
                )
            await interaction.response.send_message(embed=embed)
            return

    @app_commands.command(name='foster', description='send a pup to an allied pack as a diplomatic gesture (alpha only).')
    @app_commands.describe(pup='the pup to foster out (their wolf name)', target_pack='name of the receiving pack')
    async def foster(self, interaction: discord.Interaction, pup: str, target_pack: str):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not _is_alpha(user, pack, discord_admin=is_howlbert_admin(interaction)):
            await interaction.response.send_message(embed=howlbert_embed('Alpha Only', 'Only the alpha can send a pup to another den.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            return
        with db.get_db() as conn:
            pup_row = conn.execute(
                "SELECT * FROM users WHERE pack_id = ? AND wolf_name = ? COLLATE NOCASE AND condition NOT IN ('dead', 'dying')",
                (pack['id'], pup.strip()),
            ).fetchone()
        if not pup_row:
            await interaction.response.send_message(embed=howlbert_embed('Pup Not Found', f'No living wolf named **{pup}** in your pack.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from config import PUP_MAX_MOONS
        if int(pup_row['age_months']) > PUP_MAX_MOONS:
            await interaction.response.send_message(embed=howlbert_embed('Not a Pup', f'**{pup_row["wolf_name"]}** is grown; fostering is for young wolves only.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        other = db.get_pack_by_name(target_pack)
        if not other:
            with db.get_db() as conn:
                other = conn.execute("SELECT * FROM packs WHERE name LIKE ? COLLATE NOCASE", (f'%{target_pack}%',)).fetchone()
        if not other or int(other['id']) == int(pack['id']):
            await interaction.response.send_message(embed=howlbert_embed('Pack Not Found', f'No pack matching **{target_pack}**.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        standing = db.get_pack_relation(interaction.guild.id, int(pack['id']), int(other['id']))
        if standing < 5:
            await interaction.response.send_message(embed=howlbert_embed('Too Hostile', f'Standing with **{other["name"]}** is **{standing}/10**; foster requires neutral or better standing.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        with db.get_db() as conn:
            conn.execute(
                "UPDATE users SET pack_id = ?, foster_pack_id = ? WHERE id = ?",
                (other['id'], pack['id'], pup_row['id']),
            )
        body = (
            f"**{pup_row['wolf_name']}** leaves **{pack['name']}** and is received by **{other['name']}**.\n\n"
            f"The host den's healers earn standing each sunrise for keeping them well. "
            f"If standing between the dens falls below **5**, the arrangement becomes a hostage situation.\n\n"
            f"_Use `/wolfadmin` to return the pup if the foster arrangement ends._"
        )
        await interaction.response.send_message(embed=howlbert_embed('Pup Fostered', body, color=SUCCESS_COLOR))

    @app_commands.command(name='schism', description='break from your pack and found a new den. requires pack unity below 30.')
    @app_commands.describe(new_pack_name='name for the den you are founding')
    async def schism(self, interaction: discord.Interaction, new_pack_name: str):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not interaction.guild:
            return
        if not new_pack_name or len(new_pack_name.strip()) < 2:
            await interaction.response.send_message(embed=howlbert_embed('Name Required', 'Give the new den a name.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if db.get_pack_by_name(new_pack_name.strip()):
            await interaction.response.send_message(embed=howlbert_embed('Name Taken', f'A pack named **{new_pack_name}** already exists.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.pack_schism import execute_schism
        world = db.get_world(interaction.guild.id)
        ok, body = execute_schism(user, pack=pack, guild_id=interaction.guild.id, new_pack_name=new_pack_name.strip(), day=world['day_number'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = 'Den Fractures' if ok else 'Schism Blocked'
        await interaction.response.send_message(embed=howlbert_embed(title, body, color=color))

    @app_commands.command(name='tribute', description='send bones to another pack to clear blood debt (alpha/advisor only).')
    @app_commands.describe(target_pack='name of the pack you owe blood debt to', amount='bones to send from your treasury')
    async def tribute(self, interaction: discord.Interaction, target_pack: str, amount: int):
        user, pack = await self._require_pack_member(interaction)
        if not user:
            return
        if not _is_pack_officer(user, pack, discord_admin=is_howlbert_admin(interaction)):
            await interaction.response.send_message(embed=howlbert_embed('Officers Only', 'Alpha or Advisor required to offer tribute.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if amount <= 0:
            await interaction.response.send_message(embed=howlbert_embed('Invalid Amount', 'Enter a positive number.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            return
        other = db.get_pack_by_name(target_pack)
        if not other:
            with db.get_db() as conn:
                other = conn.execute("SELECT * FROM packs WHERE name LIKE ? COLLATE NOCASE", (f'%{target_pack}%',)).fetchone()
        if not other or int(other['id']) == int(pack['id']):
            await interaction.response.send_message(embed=howlbert_embed('Pack Not Found', f'No pack named **{target_pack}**. Check `/pack relations`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if int(pack['treasury']) < amount:
            await interaction.response.send_message(embed=howlbert_embed('Short on Bones', f'Treasury holds **{pack["treasury"]}**; tribute requires **{amount}**.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        debt = db.get_pack_blood_debt(interaction.guild.id, int(pack['id']), int(other['id']))
        with db.get_db() as conn:
            conn.execute("UPDATE packs SET treasury = treasury - ? WHERE id = ?", (amount, pack['id']))
            conn.execute("UPDATE packs SET treasury = treasury + ? WHERE id = ?", (amount, other['id']))
        cleared = debt > 0 and amount >= debt * 50
        if cleared:
            db.clear_pack_blood_debt(interaction.guild.id, int(pack['id']), int(other['id']))
        debt_line = f"\n**{debt}** blood debt **cleared**. the obligation is settled." if cleared else (f"\n**{debt}** blood debt remains; increase the tribute to clear it fully." if debt > 0 else "\nno blood debt between your dens; this tribute is a gesture of goodwill.")
        await interaction.response.send_message(embed=howlbert_embed('Tribute Sent', f"**{amount:,}** bones sent from **{pack['name']}** to **{other['name']}**.{debt_line}", color=SUCCESS_COLOR))


async def setup(bot: commands.Bot):
    await bot.add_cog(Pack(bot))