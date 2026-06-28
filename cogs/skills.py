import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.skill_checks import SKILL_CATEGORIES, SKILL_SCENARIOS, opponent_required, scenario_keys_for_category
from engine.skill_runner import run_skill_scenario
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label

async def _category_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    choices = []
    for key, label in SKILL_CATEGORIES.items():
        if current and current.lower() not in key and (current.lower() not in label.lower()):
            continue
        choices.append(app_commands.Choice(name=choice_label(label), value=key))
    return choices[:25]

async def _check_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    category = interaction.namespace.category if hasattr(interaction.namespace, 'category') else None
    keys = scenario_keys_for_category(category) if category else list(SKILL_SCENARIOS.keys())
    choices = []
    for key in keys:
        sc = SKILL_SCENARIOS[key]
        tag = ' [opposed]' if sc.opposed else ''
        label = f'{sc.label} (DC {sc.dc}){tag}'
        if current and current.lower() not in key and (current.lower() not in label.lower()):
            continue
        choices.append(app_commands.Choice(name=choice_label(label), value=key))
    return choices[:25]

async def _opponent_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        return []
    choices = []
    seen: set[int] = set()
    pack_id = user['pack_id'] if 'pack_id' in user.keys() else None
    if pack_id:
        for wolf in db.get_pack_den_wolves(pack_id):
            if wolf['discord_id'] == interaction.user.id:
                continue
            if wolf['discord_id'] in seen:
                continue
            seen.add(wolf['discord_id'])
            label = f"{wolf['wolf_name']} (packmate)"
            if current and current.lower() not in label.lower():
                continue
            choices.append(app_commands.Choice(name=choice_label(label), value=str(wolf['discord_id'])))
    for wolf in db.list_user_wolves(interaction.user.id):
        if wolf['id'] == user['id']:
            continue
        if wolf['discord_id'] in seen:
            continue
        seen.add(wolf['discord_id'])
        label = f"{wolf['wolf_name']} (your wolf)"
        if current and current.lower() not in label.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(label), value=str(wolf['discord_id'])))
    return choices[:25]

class Skills(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='skills', description='run a catalogued survival skill check (tracking, stealth, herbs, …).')
    @app_commands.describe(category='skill category', check='specific check from the basil rules', opponent='wolf to roll against (required for opposed checks)', helper='medic or packmate assisting your roll (advantage if they pass dc 10)', group='run as a pack group check (half must succeed)', rained='recent rain/snow washed scent (tracking)', yarrow='force yarrow on stabilize (auto-used if in herb bag)')
    @app_commands.autocomplete(category=_category_autocomplete, check=_check_autocomplete, opponent=_opponent_autocomplete)
    async def skills(self, interaction: discord.Interaction, category: str, check: str, opponent: str | None=None, helper: discord.Member | None=None, group: bool=False, rained: bool=False, yarrow: bool=False):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        scenario = SKILL_SCENARIOS.get(check)
        if not scenario or scenario.category != category:
            await interaction.response.send_message(player_message('Pick a **check** that matches the **category**.'), ephemeral=reply_ephemeral())
            return
        opponent_row = None
        if opponent:
            try:
                opp_id = int(opponent)
            except ValueError:
                await interaction.response.send_message(player_message('Invalid opponent.'), ephemeral=reply_ephemeral())
                return
            if opp_id == interaction.user.id:
                await interaction.response.send_message(player_message('Pick another wolf; not yourself.'), ephemeral=reply_ephemeral())
                return
            opponent_row = db.get_user(opp_id)
            if not opponent_row:
                await interaction.response.send_message(player_message("Opponent isn't registered on Howlbert."), ephemeral=reply_ephemeral())
                return
        world = db.get_world(interaction.guild.id)
        from engine.herb_buffs import sedated_blocks_activity
        if category in ('tracking', 'stealth', 'navigation') and sedated_blocks_activity(user, world['day_number']):
            await interaction.response.send_message(embed=howlbert_embed('Sedated', '**Sedated**; valerian or poppy holds you in deep rest. No tracking, stealth, or ranging until next sunrise.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if group:
            if not user['pack_id']:
                await interaction.response.send_message(player_message('Join a pack for **group** checks.'), ephemeral=reply_ephemeral())
                return
            from engine.group_checks import run_group_check
            wolves = [w for w in db.get_pack_den_wolves(user['pack_id']) if w['condition'] not in ('dead', 'dying')]
            scenario = SKILL_SCENARIOS.get(check)
            if not scenario:
                await interaction.response.send_message(player_message('Unknown check.'), ephemeral=reply_ephemeral())
                return
            ok, body = run_group_check(wolves, dc=scenario.dc, attr_keys=scenario.attr_keys, skill_key=scenario.skill_key, skill_label=scenario.skill_label, day=world['day_number'])
            from engine.skill_runner import apply_scenario_mechanics
            synth = {'success': ok, 'outcome': 'success' if ok else 'failure', 'total': None, 'dc': scenario.dc}
            _, mech = apply_scenario_mechanics(user, scenario, synth, day=world['day_number'], weather=world['weather'], guild_id=interaction.guild.id)
            if mech:
                body += '\n\n' + '\n\n'.join(mech)
            embed = howlbert_embed(f'Group: {scenario.label}', body, color=SUCCESS_COLOR if ok else ERROR_COLOR)
            embed.set_footer(text='/skills group:true · pack howl coordination')
            await interaction.response.send_message(embed=embed)
            return
        helper_row = None
        if helper:
            helper_row = db.get_user(helper.id)
            if not helper_row:
                await interaction.response.send_message(player_message("Helper isn't registered."), ephemeral=reply_ephemeral())
                return
        if helper_row and (not opponent_row):
            from engine.group_checks import run_assisted_check
            scenario = SKILL_SCENARIOS.get(check)
            if not scenario or scenario.category != category:
                await interaction.response.send_message(player_message('Pick a **check** that matches the **category**.'), ephemeral=reply_ephemeral())
                return
            ok, body = run_assisted_check(user, helper_row, dc=scenario.dc, attr_keys=scenario.attr_keys, skill_key=scenario.skill_key, skill_label=scenario.skill_label, day=world['day_number'])
            from engine.skill_runner import apply_scenario_mechanics
            synth = {'success': ok, 'outcome': 'success' if ok else 'failure', 'total': None, 'dc': scenario.dc}
            _, mech = apply_scenario_mechanics(user, scenario, synth, day=world['day_number'], weather=world['weather'], guild_id=interaction.guild.id)
            if mech:
                body += '\n\n' + '\n\n'.join(mech)
            embed = howlbert_embed(scenario.label, body, color=SUCCESS_COLOR if ok else ERROR_COLOR)
            embed.set_footer(text='/skills helper: · assisted check')
            await interaction.response.send_message(embed=embed)
            return
        ok, body, _ = run_skill_scenario(user, check, day=world['day_number'], weather=world['weather'], time_of_day=world['time_of_day'], rained=rained, yarrow_bonus=yarrow, opponent=opponent_row, guild_id=interaction.guild.id)
        embed = howlbert_embed(scenario.label, body, color=SUCCESS_COLOR if ok else ERROR_COLOR)
        footer = f'/skills · {SKILL_CATEGORIES.get(category, category)}'
        if scenario.opposed:
            footer += ' · opposed'
        embed.set_footer(text=footer)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='skilllist', description='list skill checks in a category (reference).')
    @app_commands.describe(category='category to list')
    @app_commands.autocomplete(category=_category_autocomplete)
    async def skilllist(self, interaction: discord.Interaction, category: str):
        if category not in SKILL_CATEGORIES:
            await interaction.response.send_message(player_message('Unknown category.'), ephemeral=reply_ephemeral())
            return
        lines = []
        for sc in SKILL_SCENARIOS.values():
            if sc.category != category:
                continue
            tag = ' · **opposed**' if sc.opposed else ''
            lines.append(f'**{sc.label}**; DC **{sc.dc}**{tag}')
        embed = howlbert_embed(SKILL_CATEGORIES[category], '\n'.join(lines) or 'None.')
        embed.set_footer(text='opposed checks need `/skills opponent:` · night adds +2 dc to tracking/stealth')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

async def setup(bot: commands.Bot):
    await bot.add_cog(Skills(bot))