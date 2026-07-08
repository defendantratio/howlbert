import discord
from discord import app_commands
from discord.ext import commands
import database as db
from rpg_rules import DC_TIERS, ROLE_LABELS, SKILLS
from engine.character import attr_modifier, parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from engine.shop_items import consume_item_by_key, has_item
from engine.role_features import can_use_role_reroll, has_any_role
from engine.role_privileges import HERB_HEAL_DAILY_LIMIT, herb_heal_limit_reached
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label

class Rpg(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='rpg', description='roll checks, set attributes, or delete your profile.')
    @app_commands.describe(action='roll, setstats, or delete', skill='skill to roll (roll)', attribute='raw attribute check (roll)', dc='difficulty (roll)', use_safe_roll='spend a safe roll on failure (roll)', use_role_reroll='elder/diplomat role reroll on failure (roll)', strength='strength 1 to 10 (setstats)', dexterity='dexterity 1 to 10 (setstats)', constitution='constitution 1 to 10 (setstats)', intelligence='intelligence 1 to 10 (setstats)', charisma='charisma 1 to 10 (setstats)', wisdom='wisdom 1 to 10 (setstats)', confirm='type delete to confirm profile deletion')
    @app_commands.choices(action=[app_commands.Choice(name='roll a check', value='roll'), app_commands.Choice(name='set attributes', value='setstats'), app_commands.Choice(name='delete profile', value='delete')], skill=[app_commands.Choice(name=label, value=key) for key, (_, label) in SKILLS.items()], attribute=[app_commands.Choice(name='strength', value='attr_str'), app_commands.Choice(name='dexterity', value='attr_dex'), app_commands.Choice(name='survival / constitution', value='attr_con'), app_commands.Choice(name='intelligence', value='attr_int'), app_commands.Choice(name='charisma', value='attr_cha'), app_commands.Choice(name='wisdom', value='attr_wis')], dc=[app_commands.Choice(name='easy (10): routine', value=10), app_commands.Choice(name='moderate (15): challenging', value=15), app_commands.Choice(name='hard (20): desperate', value=20), app_commands.Choice(name='legendary (25): nearly impossible', value=25)])
    async def rpg_hub(self, interaction: discord.Interaction, action: str, skill: str | None=None, attribute: str | None=None, dc: app_commands.Range[int, 1, 40]=15, use_safe_roll: bool=False, use_role_reroll: bool=False, strength: app_commands.Range[int, 1, 10] | None=None, dexterity: app_commands.Range[int, 1, 10] | None=None, constitution: app_commands.Range[int, 1, 10] | None=None, intelligence: app_commands.Range[int, 1, 10] | None=None, charisma: app_commands.Range[int, 1, 10] | None=None, wisdom: app_commands.Range[int, 1, 10] | None=None, confirm: str | None=None):
        if action == 'roll':
            await self._roll(interaction, skill, attribute, dc, use_safe_roll, use_role_reroll)
        elif action == 'setstats':
            if None in (strength, dexterity, constitution, intelligence, charisma, wisdom):
                embed = howlbert_embed('Missing Stats', 'Provide all six attributes for **setstats**.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            await self._setstats(interaction, strength, dexterity, constitution, intelligence, charisma, wisdom)
        elif action == 'delete':
            await self._deleteprofile(interaction, confirm or '')

    async def _roll(self, interaction: discord.Interaction, skill: str | None=None, attribute: str | None=None, dc: app_commands.Range[int, 1, 40]=15, use_safe_roll: bool=False, use_role_reroll: bool=False):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not skill and (not attribute):
            embed = howlbert_embed('Choose a Check', 'Pick a **skill** (e.g. Tracking) or an **attribute** (e.g. Wisdom).', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if use_safe_roll and (not has_item(interaction.user.id, 'safe_roll')):
            embed = howlbert_embed('No Safe Roll', 'Buy a **Safe Roll** from `/bones action:shop` or set `use_safe_roll:false`.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        day = 0
        if interaction.guild_id:
            world = db.get_world(interaction.guild_id)
            if world:
                day = int(world['day_number'])

        def _role_reroll_allowed(check_result: dict) -> bool:
            if not use_role_reroll or check_result['success']:
                return False
            if check_result['outcome'] == 'critical_failure':
                return False
            if not can_use_role_reroll(user, day):
                return False
            if has_any_role(user, 'elder') and skill:
                return True
            if has_any_role(user, 'diplomat'):
                if attribute == 'attr_cha':
                    return True
                if skill:
                    attr_keys, _ = SKILLS[skill]
                    return 'attr_cha' in attr_keys
            return False
        role_reroll_note = ''
        if skill:
            attr_keys, skill_label = SKILLS[skill]
            result = resolve_check(user, attr_keys=attr_keys, skill=skill_label, dc=dc, proficient=False, allow_safe_roll=use_safe_roll, has_safe_roll=use_safe_roll and has_item(interaction.user.id, 'safe_roll'), skill_key=skill, game_day=day or None)
            title = f'{skill_label} Check'
            if _role_reroll_allowed(result):
                first_die = result['die']
                result = resolve_check(user, attr_keys=attr_keys, skill=skill_label, dc=dc, proficient=False, skill_key=skill, game_day=day or None)
                role_reroll_note = f'🎲 **Role reroll**; first die was **{first_die}**; rolled again.\n'
                db.update_user(interaction.user.id, wolf_id=user['id'], last_role_reroll_day=day)
        else:
            label_map = {'attr_str': 'Strength', 'attr_dex': 'Dexterity', 'attr_con': 'Survival / Constitution', 'attr_int': 'Intelligence', 'attr_cha': 'Charisma', 'attr_wis': 'Wisdom'}
            result = resolve_check(user, attr_keys=(attribute,), skill=label_map.get(attribute, attribute), dc=dc, proficient=False, allow_safe_roll=use_safe_roll, has_safe_roll=use_safe_roll and has_item(interaction.user.id, 'safe_roll'), game_day=day or None)
            title = f"{label_map.get(attribute, 'Attribute')} Check"
            if _role_reroll_allowed(result):
                first_die = result['die']
                result = resolve_check(user, attr_keys=(attribute,), skill=label_map.get(attribute, attribute), dc=dc, proficient=False, game_day=day or None)
                role_reroll_note = f'🎲 **Role reroll**; first die was **{first_die}**; rolled again.\n'
                db.update_user(interaction.user.id, wolf_id=user['id'], last_role_reroll_day=day)
        if result.get('safe_roll_used'):
            consume_item_by_key(interaction.user.id, 'safe_roll')
        setback_note = ''
        if skill:
            from engine.character_traits import maybe_apply_failure_setback, maybe_apply_success_recovery
            if not result['success']:
                setback_note = maybe_apply_failure_setback(user, skill_key=skill, outcome=result['outcome'], game_day=day or None, total=result['total'], dc=dc)
            else:
                setback_note = maybe_apply_success_recovery(user, skill_key=skill, game_day=day or None, dc=dc)
            if setback_note:
                setback_note = f'\n{setback_note}'
        color = SUCCESS_COLOR if result['success'] else ERROR_COLOR
        body = role_reroll_note + format_roll_result(result) + setback_note
        embed = howlbert_embed(title, body, color=color)
        tier_name = next((k for k, v in DC_TIERS.items() if v == dc), None)
        footer = f'dc tier: {tier_name.title()} ({dc})' if tier_name else ''
        footer += (' · ' if footer else '') + 'for guided skill checks with bonuses & dice: /skills'
        embed.set_footer(text=footer)
        await interaction.response.send_message(embed=embed)

    async def _deleteprofile(self, interaction: discord.Interaction, confirm: str):
        if confirm.strip().upper() != 'DELETE':
            embed = howlbert_embed('Not Confirmed', 'Re-run with `confirm: DELETE` to permanently remove your wolf.\nYour account prestige and legacy are **kept**.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', "You don't have a wolf profile to delete.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        wolf_name = user['wolf_name']
        outcome = db.delete_wolf_profile(interaction.user.id)
        if outcome == 'alpha_transfer':
            embed = howlbert_embed('Cannot Delete', "You're the Alpha of a den with other wolves. Transfer leadership or leave the pack before deleting your profile.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Profile Deleted', color=SUCCESS_COLOR)
        embed.description = f'**{wolf_name}** has left the wild.\nPrestige and legacy on your account are unchanged.'
        remaining = db.count_user_wolves(interaction.user.id)
        if remaining:
            active = db.get_user(interaction.user.id)
            if active:
                embed.add_field(name='Active Wolf', value=f"Now playing as **{active['wolf_name']}**.", inline=False)
        else:
            embed.set_footer(text='use /register to create a new wolf.')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _setstats(self, interaction: discord.Interaction, strength: app_commands.Range[int, 1, 10], dexterity: app_commands.Range[int, 1, 10], constitution: app_commands.Range[int, 1, 10], intelligence: app_commands.Range[int, 1, 10], charisma: app_commands.Range[int, 1, 10], wisdom: app_commands.Range[int, 1, 10]):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        stats = {'attr_str': strength, 'attr_dex': dexterity, 'attr_con': constitution, 'attr_int': intelligence, 'attr_cha': charisma, 'attr_wis': wisdom}
        role = user['wolf_role'] if 'wolf_role' in user.keys() else 'hunter'
        from engine.conditions import validate_stats
        error = validate_stats(role, stats)
        if error:
            from rpg_rules import ROLE_ATTRIBUTE_RANGES
            lo, hi = ROLE_ATTRIBUTE_RANGES.get(role, (16, 20))
            embed = howlbert_embed('Invalid Spread', f'{error}\n\nYour role **{ROLE_LABELS.get(role, role)}** allows total **{lo}; {hi}**.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        db.set_user_stats(interaction.user.id, stats)
        total = sum(stats.values())
        from engine.character import compute_max_hp, format_max_hp_breakdown
        max_hp = compute_max_hp(strength, constitution)
        embed = howlbert_embed('Stats Updated', color=SUCCESS_COLOR)
        embed.description = f'STR {strength} · DEX {dexterity} · CON {constitution}\nINT {intelligence} · CHA {charisma} · WIS {wisdom}\n**Total: {total}**\n**Max HP:** {format_max_hp_breakdown(strength, constitution, max_hp=max_hp)}'
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='vitals', description='view conditions, rest, lick wounds, or escape quarantine.')
    @app_commands.describe(action='condition, rest, lick_wound, or escape_quarantine', rest_type='short or long rest (rest)', use_herb='use comfrey for short rest healing (rest)')
    @app_commands.choices(action=[app_commands.Choice(name='view conditions', value='condition'), app_commands.Choice(name='rest', value='rest'), app_commands.Choice(name='lick wound (heal 1 hp; diminishing on repeat)', value='lick_wound'), app_commands.Choice(name='escape quarantine (dex roll, standing risk)', value='escape_quarantine')], rest_type=[app_commands.Choice(name='long rest (6 to 8 hours sleep)', value='long'), app_commands.Choice(name='short rest (10 to 30 min)', value='short')])
    async def vitals(self, interaction: discord.Interaction, action: str, rest_type: str='long', use_herb: bool=False):
        if action == 'condition':
            await self._condition(interaction)
        elif action == 'rest':
            await self._rest(interaction, rest_type, use_herb)
        elif action == 'lick_wound':
            await self._lick_wound(interaction)
        elif action == 'escape_quarantine':
            await self._escape_quarantine(interaction)

    async def _condition(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.vitals_decay import apply_time_decay
        _decay_applied, _ = apply_time_decay(user)
        if _decay_applied:
            user = db.get_user(interaction.user.id) or user
        from engine.character import format_max_hp_breakdown
        from engine.conditions import format_conditions
        from engine.exhaustion_effects import effective_max_hp, user_exhaustion
        from engine.hunger import format_hunger_line
        from engine.mood import format_mood_line
        from engine.thirst import format_thirst_line
        day = None
        if interaction.guild_id:
            world = db.get_world(interaction.guild_id)
            if world:
                day = world['day_number']
        embed = howlbert_embed(f"{user['wolf_name']}: Conditions", format_conditions(user, day=day))
        str_val = int(user['attr_str']) if 'attr_str' in user.keys() else 5
        con_val = int(user['attr_con']) if 'attr_con' in user.keys() else 5
        embed.add_field(name='HP', value=f"{user['hp']}/{effective_max_hp(user)}\n{format_max_hp_breakdown(str_val, con_val, max_hp=int(user['max_hp']))}" + (f"\n_(exhaustion cap {effective_max_hp(user)}; base {user['max_hp']})_" if user_exhaustion(user) >= 6 else ''), inline=True)
        embed.add_field(name='Mood', value=format_mood_line(user), inline=True)
        embed.add_field(name='Hunger', value=format_hunger_line(user), inline=True)
        embed.add_field(name='Hydration', value=format_thirst_line(user), inline=True)
        from engine.energy import energy_line
        embed.add_field(name='Energy', value=energy_line(user), inline=True)
        from engine.treatment_plan import build_treatment_checklist
        checklist = build_treatment_checklist(user, day=day)
        embed.add_field(name='Treatment plan', value=checklist, inline=False)
        from engine.healer_refusal import healer_refusal_reminder
        refusal = healer_refusal_reminder(user, pack_id=user['pack_id'] if user['pack_id'] else None)
        if refusal:
            embed.add_field(name="Healer's Code", value=refusal, inline=False)
        from engine.herb_buffs import format_active_herb_buffs
        herb_buffs = ''
        if day is not None:
            herb_buffs = format_active_herb_buffs(user, day)
        if herb_buffs:
            embed.add_field(name='Herb effects', value=herb_buffs, inline=False)
        footer = '/medic action:treat · /medic action:surgery · Long rest each sunrise'
        cond = user['condition'] if 'condition' in user.keys() else 'healthy'
        if cond == 'dying' or (int(user['hp']) <= 0 and cond != 'dead'):
            footer = '`/medic action:deathsaves` · `/medic action:stabilize` · ' + footer
        embed.set_footer(text=footer)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _rest(self, interaction: discord.Interaction, rest_type: str='long', use_herb: bool=False):
        import random
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        if rest_type == 'long':
            from engine.conditions import apply_long_rest_benefits, manual_long_rest_used_today, mark_manual_long_rest
            if manual_long_rest_used_today(user, day):
                embed = howlbert_embed('Already Rested', 'You already took a long rest this sunrise (sunrise sleep counts separately).', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            from engine.activity_exhaustion import clear_activity_fatigue
            rest = apply_long_rest_benefits(user, season=world['season'] if world and 'season' in world.keys() else None)
            clear_activity_fatigue(user, day)
            mark_manual_long_rest(user, day)
            db.set_user_conditions(interaction.user.id, hp=rest['hp'], exhaustion=rest['exhaustion'], last_rest_day=day, herb_heals_today=0)
            db.update_user(interaction.user.id, wolf_id=user['id'], mood=rest['mood'])
            from engine.energy import hunger_factor as _hf
            from config import ENERGY_LONG_REST_GAIN
            old_energy = int(user['energy']) if 'energy' in user.keys() and user['energy'] is not None else 100
            energy_gain = int(round(ENERGY_LONG_REST_GAIN * _hf(user)))
            new_energy = db.adjust_energy(user['id'], energy_gain)
            db.update_user(interaction.user.id, wolf_id=user['id'], last_energy_at=db.utcnow())
            energy_line = f"\nEnergy **+{new_energy - old_energy}** (now {new_energy}/100)." if new_energy != old_energy else ''
            mood_gain = rest['mood'] - int(user['mood'])
            hp_gain = rest['hp'] - int(user['hp'])
            ex_drop = int(user['exhaustion']) - rest['exhaustion']
            embed = howlbert_embed('Long Rest', f"Recovered **{hp_gain} HP** (now {rest['hp']}/{user['max_hp']}).\nExhaustion **−{ex_drop}** ({user['exhaustion']} → {rest['exhaustion']})" + (f"\nMood **+{mood_gain}** (now {rest['mood']})." if mood_gain else '') + energy_line + '\n\n_Still need `/eat` and `/drink` for hunger and hydration._', color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            return
        if herb_heal_limit_reached(user):
            embed = howlbert_embed('Limit Reached', f'You can only use comfrey on short rest **{HERB_HEAL_DAILY_LIMIT}** times per sunrise.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        heal = 0
        if use_herb:
            item = db.get_item_by_key('herb_comfrey')
            if not item or db.get_inventory_quantity(interaction.user.id, item['id']) < 1:
                embed = howlbert_embed('No Comfrey', 'You need comfrey in `/bones action:inventory` or your herb bag.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            heal = random.randint(1, 4) + 1
            db.consume_item(interaction.user.id, item['id'])
        from engine.activity_exhaustion import clear_activity_fatigue
        from config import SHORT_REST_EXHAUSTION_RELIEF
        new_hp = min(user['max_hp'], user['hp'] + heal) if heal else user['hp']
        clear_activity_fatigue(user, day)
        old_exhaustion = int(user['exhaustion']) if 'exhaustion' in user.keys() else 0
        ex_note = ''
        new_exhaustion = max(0, old_exhaustion - SHORT_REST_EXHAUSTION_RELIEF)
        fields = {'hp': new_hp, 'herb_heals_today': user['herb_heals_today'] + (1 if heal else 0), 'exhaustion': new_exhaustion}
        if new_exhaustion != old_exhaustion:
            ex_note = f" Exhaustion **−{old_exhaustion - new_exhaustion}** (now {new_exhaustion})."
        db.set_user_conditions(interaction.user.id, **fields)
        from engine.energy import hunger_factor as _hf
        from config import ENERGY_SHORT_REST_GAIN
        old_energy = int(user['energy']) if 'energy' in user.keys() and user['energy'] is not None else 100
        new_energy = db.adjust_energy(user['id'], int(round(ENERGY_SHORT_REST_GAIN * _hf(user))))
        db.update_user(interaction.user.id, wolf_id=user['id'], last_energy_at=db.utcnow())
        energy_note = f" Energy **+{new_energy - old_energy}** (now {new_energy}/100)." if new_energy != old_energy else ''
        msg = 'Short rest.' + (f" Comfrey healed **{heal} HP** (now {new_hp}/{user['max_hp']})." if heal else ' No herb used.') + ex_note + energy_note
        if old_exhaustion == 0:
            msg += f' _(No exhaustion to clear. Clears activity strain; HP recovery needs comfrey.)_'
        else:
            msg += f' _(Clears activity strain; reduces exhaustion by {SHORT_REST_EXHAUSTION_RELIEF} per rest. HP recovery needs comfrey.)_'
        embed = howlbert_embed('Short Rest', msg, color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    async def _escape_quarantine(self, interaction: discord.Interaction):
        import random
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(embed=howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.quarantine import is_quarantined
        if not is_quarantined(user):
            await interaction.response.send_message(embed=howlbert_embed('Not Quarantined', 'you are not in the sick den.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        attr_dex = int(user['attr_dex']) if 'attr_dex' in user.keys() else 0
        mod = attr_modifier(attr_dex)
        die = random.randint(1, 20)
        total = die + mod
        dc = 12
        if total >= dc:
            db.set_quarantined(interaction.user.id, False, wolf_id=user['id'])
            embed = howlbert_embed(
                'Escaped',
                f'you slip out of the sick den while the medic is away. quarantine lifted.\n\n_roll: **{die}** + dex **{mod:+}** = **{total}** vs dc {dc}_\n\n_if a medic or alpha notices you are gone, they may re-quarantine you._',
                color=SUCCESS_COLOR,
            )
            embed.set_footer(text='ephemeral; only you see this')
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            result = db.adjust_wolf_standing(interaction.user.id, -5)
            caught_note = ''
            if result == 'kicked':
                caught_note = '\n_standing so low you have been cast out of the pack._'
            embed = howlbert_embed(
                'Caught',
                f'you are caught mid-sneak. the medic scent-marks you back to the den. **−5 standing**.{caught_note}\n\n_roll: **{die}** + dex **{mod:+}** = **{total}** vs dc {dc}_',
                color=ERROR_COLOR,
            )
            embed.set_footer(text='ephemeral; only you see this')
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _lick_wound(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(embed=howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        cond = user['condition'] if 'condition' in user.keys() else 'healthy'
        if cond in ('dead', 'dying'):
            await interaction.response.send_message(embed=howlbert_embed('Cannot Act', 'a wolf in this condition cannot tend to themselves.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not interaction.guild_id:
            await interaction.response.send_message(embed=howlbert_embed('Server Only', 'Use this in a server.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.conditions import parse_injuries
        injuries = parse_injuries(user['active_injuries'] if 'active_injuries' in user.keys() else None)
        if not injuries:
            await interaction.response.send_message(embed=howlbert_embed('No Wounds', 'you have no active injuries to tend to.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        import random
        world = db.get_world(interaction.guild_id)
        day = world['day_number'] if world else 1
        last_lick = int(user['last_lick_day']) if 'last_lick_day' in user.keys() else 0
        max_hp = int(user['max_hp']) if 'max_hp' in user.keys() else 10
        current_hp = int(user['hp']) if 'hp' in user.keys() else max_hp
        # no cooldown: the first tending each sunrise heals; licking again only
        # irritates the raw skin (diminishing returns), and over-licking can
        # fester into a sore, so spamming it backfires instead of being blocked.
        already_tended = last_lick >= day
        if already_tended:
            msg = 'you lick at the wounds again, but they are already tended; more licking only worries the raw skin.'
            color = ERROR_COLOR
            if 'infected_wound' not in injuries and random.random() < 0.15:
                import json
                from engine.conditions import add_injury
                injuries = add_injury(injuries, 'infected_wound')
                db.set_user_conditions(interaction.user.id, wolf_id=user['id'], active_injuries=json.dumps(injuries))
                msg += ' licked raw, it festers; **infected wound**.'
            embed = howlbert_embed('Lick Wound', msg, color=color)
            embed.set_footer(text='/vitals action:condition · /medic action:treat')
            await interaction.response.send_message(embed=embed)
            return
        db.update_user(interaction.user.id, wolf_id=user['id'], last_lick_day=day)
        if current_hp >= max_hp:
            await interaction.response.send_message(embed=howlbert_embed('Lick Wound', 'you work your tongue along each wound carefully. your hp is already full; the licking soothes but heals nothing new.', color=SUCCESS_COLOR))
            return
        new_hp = min(max_hp, current_hp + 1)
        db.set_user_conditions(interaction.user.id, wolf_id=user['id'], hp=new_hp)
        embed = howlbert_embed('Lick Wound', f'you work your tongue carefully across each wound, cleaning dirt and slowing the bleed. **+1 hp** (now {new_hp}/{max_hp}).\n\n_tend again and the raw skin only worsens; pairs with medic treatment_', color=SUCCESS_COLOR)
        embed.set_footer(text='/vitals action:condition · /medic action:treat')
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Rpg(bot))