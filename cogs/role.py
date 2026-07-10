"""Role-specific quests, events, and Maw faith commands."""
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.character import parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from engine.role_content import pick_prophecy, pick_role_event
from rpg_rules import ROLE_FEATURES, ROLE_LABELS
from utils.currency import format_bones
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label
from utils.wolf_autocomplete import make_member_wolf_autocomplete

_mentor_wolf_autocomplete = make_member_wolf_autocomplete("mentor")

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

def _standing_note(kick: str, user) -> str:
    from engine.broken_canine import standing_expulsion_note
    pack_id = user['pack_id'] if user and 'pack_id' in user.keys() else None
    note = standing_expulsion_note(kick, pack_id)
    if note:
        return note if note.startswith('\n') else f'\n\n{note}'
    return ''

class RoleCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='role', description='role quests, role events, prophecy, shadowing, or rank disputes.')
    @app_commands.describe(action='quests, event, prophecy, shadow, or challenge', mentor='full-ranked packmate to shadow (action:shadow), or packmate to contest (action:challenge)', own_wolf='your other wolf to shadow or challenge (multi-wolf players)', mentor_wolf="specific wolf from that player's roster")
    @app_commands.choices(action=[app_commands.Choice(name='role quests', value='quests'), app_commands.Choice(name='role event', value='event'), app_commands.Choice(name='prophecy (drown-sick)', value='prophecy'), app_commands.Choice(name='shadow a mentor (apprentice)', value='shadow'), app_commands.Choice(name='challenge pack rank', value='challenge')])
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, mentor_wolf=_mentor_wolf_autocomplete)
    async def role(self, interaction: discord.Interaction, action: str, mentor: discord.Member | None = None, own_wolf: str | None = None, mentor_wolf: str | None = None):
        if action == 'quests':
            await self._rolequests(interaction)
        elif action == 'event':
            await self._roleevent(interaction)
        elif action == 'prophecy':
            await self._prophecy(interaction)
        elif action == 'shadow':
            mentor_row = await self._resolve_role_target(interaction, mentor, own_wolf, label='mentor', mentor_wolf=mentor_wolf)
            if mentor_row is not None:
                await self._shadow(interaction, mentor_row)
        elif action == 'challenge':
            target_row = await self._resolve_role_target(interaction, mentor, own_wolf, label='target', mentor_wolf=mentor_wolf)
            if target_row is not None:
                await self._rankdispute(interaction, target_row)

    async def _rolequests(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        role = user['wolf_role'] if 'wolf_role' in user.keys() else 'hunter'
        label = ROLE_LABELS.get(role, role.title())
        rows = db.get_role_quests(interaction.user.id)
        if not rows:
            embed = howlbert_embed(f'Role Quests: {label}', 'No role quests available right now. You may have finished them all, or none are posted for your path yet.')
            embed.set_footer(text='/role action:event · repeats pay less this sunrise')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed(f'Role Quests: {label}', 'Quests only your role can take; accepted automatically.')
        guild_id = interaction.guild.id if interaction.guild else None
        day = db.get_world(guild_id)['day_number'] if guild_id else 0
        for q in rows[:8]:
            db.accept_quest(interaction.user.id, q['id'], day, guild_id=guild_id)
            pack_note = ''
            if q['required_pack']:
                pack_note = f" _(requires {q['required_pack'].title()} pack)_"
            from engine.quest_rewards import format_quest_reward_line
            reward_line = format_quest_reward_line(q['key'], q['reward_bones'])
            embed.add_field(name=f"{q['title']} ({q['difficulty']}); {reward_line}", value=f"`{q['key']}`; {q['description']}{pack_note}", inline=False)
        feature = ROLE_FEATURES.get(role)
        if feature:
            embed.set_footer(text=f'{label} · {feature}')
        await interaction.response.send_message(embed=embed, ephemeral=False)

    async def _roleevent(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        from engine.blooding import blooding_gate_message
        gate = blooding_gate_message(user)
        if gate:
            embed = howlbert_embed('Not Blooded', gate, color=ERROR_COLOR)
            embed.set_footer(text='/bones action:hunt · first kill earns blooding')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        from engine.energy import spend_energy
        _new_energy, _had_energy, role_event_penalty = spend_energy(user, 'role_event')
        _re_first_today = int(user['last_role_event_day']) < day if 'last_role_event_day' in user.keys() else True
        role = user['wolf_role'] if 'wolf_role' in user.keys() else 'hunter'
        pack = user['great_pack'] if 'great_pack' in user.keys() else None
        event = pick_role_event(role, pack)
        body = event['text']
        success = True
        roll_note = ''
        if event.get('skill'):
            profs = parse_proficiencies(user['skill_proficiencies'])
            skill = event['skill']
            result = resolve_check(user, attr_keys=_skill_attrs(skill), skill=skill.title(), dc=event['dc'], proficient=skill in profs, skill_key=skill, game_day=day)
            success = result['success']
            roll_note = '\n\n' + format_roll_result(result)
        if success:
            outcome = event['success']
            if event.get('prophecy'):
                prophecy = pick_prophecy()
                outcome += f'\n\n**Prophecy:** _{prophecy}_'
            _re_bones = max(0, event['bones'])
            db.add_bones(interaction.user.id, _re_bones)
            if event.get('standing'):
                kick = db.adjust_wolf_standing(interaction.user.id, event['standing'])
                outcome += _standing_note(kick, user)
            if role == 'hunter' and _re_first_today:
                from engine.hunt_payout import grant_prey_carcass_canonical, prey_key_for_payout
                prey_key = prey_key_for_payout(_re_bones, user=user, season=world['season'])
                carcass_name = grant_prey_carcass_canonical(user['id'], guild_id=interaction.guild.id, day=day, prey_key=prey_key)
                outcome += f'\n\n{carcass_name} dragged to your hoard (`/food`).'
            if role_event_penalty:
                outcome += f'\n\n_{role_event_penalty}_'
            color = SUCCESS_COLOR
        else:
            outcome = event['failure']
            color = ERROR_COLOR
            if event.get('standing_fail'):
                kick = db.adjust_wolf_standing(interaction.user.id, event['standing_fail'])
                outcome += _standing_note(kick, user)
        db.update_user(interaction.user.id, wolf_id=user['id'], last_role_event_day=day)
        from engine.disease_contract import try_mistmoor_swamp_exposure
        user = db.get_user(interaction.user.id)
        if role == 'drown_sick':
            swamp_note = try_mistmoor_swamp_exposure(user, belly_rip=event.get('title') == 'Belly-Rip Vigil')
            if swamp_note:
                outcome += f'\n\n{swamp_note}'
        embed = howlbert_embed(event['title'], body + roll_note + f'\n\n{outcome}', color=color)
        if success and event.get('bones'):
            embed.add_field(name='Earned', value=format_bones(event['bones'], signed=True), inline=True)
        if success and event.get('standing'):
            embed.add_field(name='Standing', value=f"+{event['standing']}", inline=True)
        if not success and event.get('standing_fail'):
            embed.add_field(name='Standing', value=str(event['standing_fail']), inline=True)
        feature = ROLE_FEATURES.get(role)
        if feature:
            footer = f'{ROLE_LABELS.get(role, role)} · {feature}'
            if len(footer) > 256:
                footer = footer[:253] + '…'
            embed.set_footer(text=footer)
        else:
            embed.set_footer(text='/checklist · costs energy')
        await interaction.response.send_message(embed=embed)

    async def _prophecy(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        role = user['wolf_role'] if 'wolf_role' in user.keys() else 'hunter'
        if role != 'drown_sick':
            embed = howlbert_embed('Not Drown-Sick', f'Only wolves who fell into the Belly-Rip and rose changed can hear prophecies. Your role: **{ROLE_LABELS.get(role, role)}**.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        from engine.energy import spend_energy
        _new_energy, _had_energy, prophecy_penalty = spend_energy(user, 'prophecy')
        from engine.lexicon import season_display
        line = pick_prophecy()
        season = season_display(db.row_val(world, 'season', 'autumn'))
        weather = db.row_val(world, 'weather', 'fog')
        db.update_user(interaction.user.id, wolf_id=user['id'], last_prophecy_day=day)
        embed = howlbert_embed('Prophecy from the Dark Water', f'You press your nose to the mud. The chewing slows.\n\n**_{line}_**\n\nThe moon feels closer tonight. ({season}, {weather})', color=SUCCESS_COLOR)
        footer = 'it will make sense when it happens; or after it does.'
        if prophecy_penalty:
            footer += f' · {prophecy_penalty}'
        embed.set_footer(text=footer)
        await interaction.response.send_message(embed=embed)

    async def _resolve_role_target(self, interaction: discord.Interaction, member: discord.Member | None, own_wolf: str | None, *, label: str, mentor_wolf: str | None = None):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return None
        if member and own_wolf:
            await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use **mentor** or **own_wolf**; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return None
        if own_wolf:
            row = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not row:
                await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', 'No wolf with that name on your account. Check `/wolves`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return None
            if row['id'] == user['id']:
                await interaction.response.send_message(embed=howlbert_embed('Same Wolf', 'Switch active wolf with `/switchwolf`, or pick a different `own_wolf`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return None
            return row
        if member:
            if member.bot or member.id == interaction.user.id:
                await interaction.response.send_message(embed=howlbert_embed('Invalid', 'Pick a different wolf for the `mentor` option.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return None
            if mentor_wolf:
                row = db.find_user_wolf(member.id, mentor_wolf)
            else:
                row = db.get_user(member.id)
            if not row:
                await interaction.response.send_message(embed=howlbert_embed('Not Registered', 'That wolf is not on Howlbert.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return None
            return row
        await interaction.response.send_message(player_message('Pick a wolf via `mentor` or your own wolf via `own_wolf`.'), ephemeral=reply_ephemeral())
        return None

    async def _shadow(self, interaction: discord.Interaction, mentor_row):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        from engine.apprentice_shadow import run_apprentice_shadow
        ok, msg = run_apprentice_shadow(user, mentor_row, day=world['day_number'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Shadow', msg, color=color)
        if ok:
            embed.set_footer(text='medics use `/medic action:observe` instead')
        await interaction.response.send_message(embed=embed, ephemeral=False if ok else reply_ephemeral())

    async def _rankdispute(self, interaction: discord.Interaction, target_row):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        from engine.rank_dispute import run_rank_dispute
        ok, msg = run_rank_dispute(user, target_row, day=world['day_number'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Rank Dispute', msg, color=color)
        if ok:
            embed.set_footer(text='shifts den feed priority · repeats pay less this sunrise')
        await interaction.response.send_message(embed=embed, ephemeral=False if ok else reply_ephemeral())

def _skill_attrs(skill: str) -> tuple[str, ...]:
    from rpg_rules import SKILLS
    if skill in SKILLS:
        return SKILLS[skill][0]
    return ('attr_wis',)

async def setup(bot: commands.Bot):
    await bot.add_cog(RoleCog(bot))