import discord
from discord import app_commands
from discord.ext import commands
import database as db
from config import WEATHER_HUNT_MODIFIERS
from engine.season_effects import season_hunt_modifier_label
from engine.chat_xp import try_chat_message_xp
from utils.permissions import is_howlbert_admin
from engine.donor import donor_daily_bonus
from engine.lexicon import format_sunrise
from engine.season_effects import season_activity_blurb
from engine.world import forecast_weather, season_blurb, season_label, time_blurb, time_label, weather_label
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label
HAZARD_CHOICES = [app_commands.Choice(name='blizzard', value='blizzard'), app_commands.Choice(name='flood / rapid river', value='flood'), app_commands.Choice(name='wildfire smoke', value='wildfire_smoke'), app_commands.Choice(name='freezing rain / ice', value='freezing_rain'), app_commands.Choice(name='extreme heat', value='extreme_heat'), app_commands.Choice(name='thick fog', value='thick_fog'), app_commands.Choice(name='thunderstorm', value='thunderstorm'), app_commands.Choice(name='avalanche', value='avalanche'), app_commands.Choice(name='deep snow', value='deep_snow'), app_commands.Choice(name='quicksand / mud', value='quicksand')]
HAZARD_SEVERITY_CHOICES = [app_commands.Choice(name='moderate', value='moderate'), app_commands.Choice(name='severe', value='severe'), app_commands.Choice(name='extreme', value='extreme')]
TRAVEL_TERRITORY_CHOICES = [app_commands.Choice(name='river', value='river'), app_commands.Choice(name='swamp', value='swamp'), app_commands.Choice(name='mountain', value='mountain'), app_commands.Choice(name='forest', value='forest'), app_commands.Choice(name='twolegplace', value='twolegplace')]

class World(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try_chat_message_xp(message)

    def _guild_id(self, interaction: discord.Interaction) -> int | None:
        if interaction.guild:
            return interaction.guild.id
        return None

    @app_commands.command(name='world', description='time, weather, hazards, travel, cooldowns, or plot for this den.')
    @app_commands.describe(action='time, weather, forecast, cooldowns, plot, hazard, travel, encounter, or omen', hazard_type='weather hazard (action:hazard)', severity='hazard severity (action:hazard)', territory='territory type (action:travel)')
    @app_commands.choices(action=[app_commands.Choice(name='time & moon', value='time'), app_commands.Choice(name='weather', value='weather'), app_commands.Choice(name='forecast', value='forecast'), app_commands.Choice(name='cooldowns', value='cooldowns'), app_commands.Choice(name='plot (the blinking)', value='plot'), app_commands.Choice(name='weather hazard', value='hazard'), app_commands.Choice(name='travel hazard', value='travel'), app_commands.Choice(name='wilderness encounter', value='encounter'), app_commands.Choice(name='rest omen', value='omen')], hazard_type=HAZARD_CHOICES, severity=HAZARD_SEVERITY_CHOICES, territory=TRAVEL_TERRITORY_CHOICES)
    async def world_info(self, interaction: discord.Interaction, action: str='time', hazard_type: str='blizzard', severity: str='severe', territory: str='forest'):
        if action == 'time':
            await self._time(interaction)
        elif action == 'weather':
            await self._weather(interaction)
        elif action == 'forecast':
            await self._weatherforecast(interaction)
        elif action == 'cooldowns':
            await self._cooldowns(interaction)
        elif action == 'plot':
            await self._plot(interaction)
        elif action == 'hazard':
            await self._run_weather_hazard(interaction, hazard_type, severity)
        elif action == 'travel':
            await self._run_travel_hazard(interaction, territory)
        elif action == 'encounter':
            await self._run_wilderness_encounter(interaction)
        elif action == 'omen':
            await self._run_rest_omen(interaction)

    async def _time(self, interaction: discord.Interaction):
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(guild_id)
        from config import LUNAR_BIRTH_AGING, ROLLOVER_TIMEZONE
        from engine.lunar import lunar_phase_label, rollover_now
        from engine.world import effective_time_of_day
        now = rollover_now(ROLLOVER_TIMEZONE)
        live_tod = effective_time_of_day(world)
        embed = howlbert_embed(f"Sunrise {world['day_number']}; {time_label(live_tod)}", f"{season_label(world['season'])}\n{season_blurb(world['season'])}\n{season_activity_blurb(world['season'])}\n\n{time_blurb(live_tod)}\n\n**Moon:** {lunar_phase_label(now)}")
        age_line = 'Wolves age when the sky matches their birth moon (new / half / full).' if LUNAR_BIRTH_AGING else 'Each sunrise ages every wolf one moon.'
        embed.set_footer(text=f"{format_sunrise(world['day_number'])} since the den began counting · {age_line}")
        await interaction.response.send_message(embed=embed)

    async def _plot(self, interaction: discord.Interaction):
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(guild_id)
        from engine.plot_blinking import PLOT_TITLE, plot_status_fields
        embed = howlbert_embed(PLOT_TITLE, 'Canon-first RP frame; mechanics apply while a phase is active.')
        for name, value, inline in plot_status_fields(world):
            embed.add_field(name=name, value=value, inline=inline)
        phase = int(world['plot_phase']) if 'plot_phase' in world.keys() else 0
        if phase > 0:
            embed.set_footer(text=f"sunrise {world['day_number']} · {season_label(world['season'])} · accept plot quests on `/quest action:board`")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='setplotphase', description='set book one plot phase 0–12 (server admin). 0 = off.')
    @app_commands.describe(phase='0 = off, 1–12 = the blinking beats')
    async def setplotphase(self, interaction: discord.Interaction, phase: int):
        if not is_howlbert_admin(interaction):
            embed = howlbert_embed('Denied', 'Only server admins may set the plot phase.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.set_plot_phase(guild_id, phase)
        from engine.plot_blinking import PLOT_TITLE, phase_meta
        meta = phase_meta(int(world['plot_phase']))
        if meta:
            body = f"Phase **{world['plot_phase']}** — **{meta['title']}**\n_{meta['news']}_"
        else:
            body = 'Plot **off**; Book One mechanics paused.'
        embed = howlbert_embed(PLOT_TITLE, body, color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='plotadvance', description='advance book one to the next plot phase (server admin).')
    async def plotadvance(self, interaction: discord.Interaction):
        if not is_howlbert_admin(interaction):
            embed = howlbert_embed('Denied', 'Only server admins may advance the plot.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        new_phase, world = db.advance_plot_phase(guild_id)
        from engine.plot_blinking import PLOT_TITLE, phase_meta
        meta = phase_meta(new_phase)
        if meta:
            body = f"Advanced to phase **{new_phase}** — **{meta['title']}**\n_{meta['news']}_\n\n{meta['mechanics']}"
        else:
            body = 'Plot is off or already at phase 12.'
        embed = howlbert_embed(PLOT_TITLE, body, color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='setseason', description='pin the in-game season, or return it to real-world sync (server admin).')
    @app_commands.describe(season='which season to pin the den to, or auto for real-world sync')
    @app_commands.choices(season=[app_commands.Choice(name='newgrowth (spring)', value='spring'), app_commands.Choice(name='highsun (summer)', value='summer'), app_commands.Choice(name='leaf-drop (autumn)', value='autumn'), app_commands.Choice(name='leaf-bare (winter)', value='winter'), app_commands.Choice(name='auto (real-world sync)', value='auto')])
    async def setseason(self, interaction: discord.Interaction, season: str):
        if not is_howlbert_admin(interaction):
            embed = howlbert_embed('Denied', 'Only server admins may set the season.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(guild_id)
        if season == 'auto':
            db.set_season_override(guild_id, None)
            from database import real_world_season
            from engine.lunar import rollover_now
            from config import ROLLOVER_TIMEZONE
            current = real_world_season(rollover_now(ROLLOVER_TIMEZONE))
            db.save_world(guild_id, day_number=world['day_number'], season=current, weather=world['weather'], time_of_day=world['time_of_day'])
            embed = howlbert_embed('Season Set', f'The den now follows the real-world calendar; currently **{season_label(current)}**.\n{season_blurb(current)}', color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            return
        db.set_season_override(guild_id, season)
        db.save_world(guild_id, day_number=world['day_number'], season=season, weather=world['weather'], time_of_day=world['time_of_day'])
        embed = howlbert_embed('Season Set', f'The den is now pinned to **{season_label(season)}**.\n{season_blurb(season)}\n_will stay this season until `/world action:setseason season:auto`._', color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    async def _weather(self, interaction: discord.Interaction):
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(guild_id)
        modifier = WEATHER_HUNT_MODIFIERS.get(world['weather'], 0)
        effect = 'No effect on hunts.' if modifier == 0 else f'{modifier:+d}% hunt bones (weather).'
        season_effect = season_hunt_modifier_label(world['season'])
        embed = howlbert_embed(weather_label(world['weather']), f'{effect}\n{season_effect.capitalize()}.')
        await interaction.response.send_message(embed=embed)

    async def _weatherforecast(self, interaction: discord.Interaction):
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(guild_id)
        forecast = forecast_weather(world['weather'])
        lines = [f"**Day {world['day_number'] + i}**; {weather_label(w)}" for i, w in enumerate(forecast, 1)]
        embed = howlbert_embed('Weather Forecast', '\n'.join(lines))
        await interaction.response.send_message(embed=embed)

    async def _cooldowns(self, interaction: discord.Interaction):
        # `/checklist` is the single source of truth for "what's left this
        # sunrise" — this action is now an alias so the two views can't drift.
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        guild_id = self._guild_id(interaction)
        day = db.get_world(guild_id)['day_number'] if guild_id else 0
        account = db.get_account(interaction.user.id)
        prestige_tier = account['prestige_tier'] if account else 0
        is_booster = bool(isinstance(interaction.user, discord.Member) and interaction.user.premium_since)
        donor_bonus = donor_daily_bonus(interaction.user.id)
        from engine.wolf_checklist import build_wolf_checklist

        body = build_wolf_checklist(
            user, day=day, guild_id=guild_id, prestige_tier=prestige_tier,
            is_booster=is_booster, donor_bonus=donor_bonus,
        )
        if not body:
            body = "nothing left this sunrise — you're caught up."
        embed = howlbert_embed(f"{user['wolf_name']}'s Checklist; Day {day}" if guild_id else f"{user['wolf_name']}'s Checklist", body)
        if guild_id:
            from config import LUNAR_BIRTH_AGING
            age_line = 'wolves age when the sky matches their birth moon (new / half / full).' if LUNAR_BIRTH_AGING else 'wolves age 1 moon per sunrise.'
            embed.set_footer(text='same list as `/checklist` · activities reset each sunrise. ' + age_line)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _run_weather_hazard(self, interaction: discord.Interaction, hazard: str, severity: str):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.weather_hazards import format_hazard_result, resolve_weather_hazard
        result = resolve_weather_hazard(user, hazard, severity)
        if result['damage']:
            from engine.vitals import apply_hp_damage
            _, extras = apply_hp_damage(user, result['damage'])
            if extras:
                result = dict(result)
                result['dying_lines'] = extras
        effects = result.get('effects') or {}
        if effects.get('exhaustion'):
            db.set_user_conditions(interaction.user.id, exhaustion=min(6, int(user['exhaustion']) + int(effects['exhaustion'])))
        if effects.get('thirst_loss'):
            db.adjust_thirst(user['id'], -int(effects['thirst_loss']))
        if effects.get('mood_loss'):
            db.adjust_mood(user['id'], -int(effects['mood_loss']))
        if effects.get('smoke_debuff'):
            db.update_user(interaction.user.id, wolf_id=user['id'], smoke_debuff=1)
        if hazard in ('blizzard', 'freezing_rain', 'deep_snow') and (not result['success']):
            from engine.disease_contract import try_weather_fever_exposure
            fever = try_weather_fever_exposure(user)
            if fever:
                effects = dict(effects)
                effects['fever_note'] = fever
        color = SUCCESS_COLOR if result['success'] else ERROR_COLOR
        body = format_hazard_result(result)
        for line in result.get('dying_lines') or []:
            body += f'\n\n{line}'
        embed = howlbert_embed('Weather Hazard', body, color=color)
        if effects.get('fever_note'):
            embed.description = (embed.description or '') + f"\n\n{effects['fever_note']}"
        user = db.get_user(interaction.user.id)
        from engine.vitals import vitals_response_footer
        embed.set_footer(text=vitals_response_footer(user, default='/world action:hazard · /vitals action:condition · /medic action:treat'))
        await interaction.response.send_message(embed=embed)

    async def _run_travel_hazard(self, interaction: discord.Interaction, territory: str):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        from engine.travel_hazards import roll_travel_hazard
        ok, body = roll_travel_hazard(user, territory, day=world['day_number'], season=world['season'], guild_id=interaction.guild.id, weather=world['weather'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Travel Hazard', body, color=color)
        user = db.get_user(interaction.user.id)
        from engine.vitals import vitals_response_footer
        footer = 'Once per travel roll; rest at den or try another territory after sunrise.'
        if world['season'] == 'winter' and world['weather'] in ('snow', 'blizzard', 'hail'):
            footer = 'Winter blizzards may double hazard checks · ' + footer
        embed.set_footer(text=vitals_response_footer(user, default=footer + ' · /world action:encounter · action:omen'))
        await interaction.response.send_message(embed=embed)

    async def _run_wilderness_encounter(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        from engine.travel_hazards import roll_wilderness_encounter
        kind, body, enc_id = roll_wilderness_encounter(user, day=world['day_number'], guild_id=interaction.guild.id, channel_id=interaction.channel_id)
        if world['season'] == 'spring' and kind == 'encounter':
            body += '\n_Spring mating season; rivals may challenge (`/courtship action:rival`)._'
        embed = howlbert_embed('Wilderness', body)
        embed.set_footer(text='/world action:travel · action:omen · combat uses the panel below')
        if enc_id:
            from utils.combat_views import make_combat_view
            await interaction.response.send_message(embed=embed, view=make_combat_view(enc_id, self.bot))
        else:
            await interaction.response.send_message(embed=embed)

    async def _run_rest_omen(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        from engine.starclan_omens import mark_rest_omen, rest_omen_available, roll_rest_omen
        world = db.get_world(interaction.guild.id)
        day = int(world['day_number'])
        if not rest_omen_available(user, day):
            embed = howlbert_embed('Already Read', "You already sought **StarClan**'s counsel this sunrise.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        kind, body = roll_rest_omen()
        mark_rest_omen(user, day)
        if kind == 'good':
            db.update_user_by_id(user['id'], omen_buff='good')
            body += '\n_Advantage on your first roll next sunrise._'
        elif kind == 'bad':
            db.update_user_by_id(user['id'], omen_buff='bad')
            body += '\n_Disadvantage on your first roll next sunrise._'
        elif kind == 'vision':
            new_mood = db.adjust_mood(user['id'], 4)
            body += f'\n**+4 mood** (now **{new_mood}**).'
        embed = howlbert_embed('StarClan Omen', body)
        embed.set_footer(text='once per sunrise · /world action:cooldowns')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='hazard', description='face a weather hazard; opposed roll vs the environment.')
    @app_commands.describe(hazard='type of weather hazard', severity='how severe the conditions are')
    @app_commands.choices(hazard=HAZARD_CHOICES, severity=HAZARD_SEVERITY_CHOICES)
    async def hazard(self, interaction: discord.Interaction, hazard: str, severity: str='severe'):
        await self._run_weather_hazard(interaction, hazard, severity)

    @app_commands.command(name='rollover', description='advance the in-game day (admin).')
    async def rollover(self, interaction: discord.Interaction):
        if not is_howlbert_admin(interaction):
            embed = howlbert_embed('Denied', 'Only server admins may call a rollover.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        world, crisis = db.perform_rollover(guild_id)
        from engine.rollover_announce import build_rollover_embed
        embed = build_rollover_embed(world, crisis)
        await interaction.response.send_message(embed=embed)
        from engine.rp_ambience import post_rp_ambience
        try:
            await post_rp_ambience(self.bot, guild_id, world)
        except Exception:
            pass
        from utils.notifications import notify_births_ready_after_rollover
        await notify_births_ready_after_rollover(self.bot, world['day_number'])

    @app_commands.command(name='wilderness', description='travel hazards, random encounters, or rest omens.')
    @app_commands.describe(action='travel, encounter, or omen', territory='river, swamp, mountain, forest, or twolegplace (travel)')
    @app_commands.choices(action=[app_commands.Choice(name='travel hazard', value='travel'), app_commands.Choice(name='random encounter', value='encounter'), app_commands.Choice(name='rest omen', value='omen')], territory=TRAVEL_TERRITORY_CHOICES)
    async def wilderness(self, interaction: discord.Interaction, action: str, territory: str='forest'):
        if action == 'travel':
            await self._run_travel_hazard(interaction, territory)
        elif action == 'encounter':
            await self._run_wilderness_encounter(interaction)
        else:
            await self._run_rest_omen(interaction)

async def setup(bot: commands.Bot):
    await bot.add_cog(World(bot))