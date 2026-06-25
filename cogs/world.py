import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import WEATHER_HUNT_MODIFIERS
from engine.season_effects import season_hunt_modifier_label
from engine.chat_xp import try_chat_message_xp
from engine.cooldowns import build_cooldown_fields
from utils.permissions import is_howlbert_admin
from engine.donor import donor_daily_bonus
from engine.lexicon import format_sunrise
from engine.season_effects import season_activity_blurb
from engine.world import forecast_weather, season_blurb, season_label, time_blurb, time_label, weather_label
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, trim_embed_fields
from utils.permissions import is_howlbert_admin


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

    @app_commands.command(
        name="world",
        description="Time, weather, forecast, cooldowns, or plot for this den.",
    )
    @app_commands.describe(action="time, weather, forecast, cooldowns, or plot")
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Time & moon", value="time"),
            app_commands.Choice(name="Weather", value="weather"),
            app_commands.Choice(name="Forecast", value="forecast"),
            app_commands.Choice(name="Cooldowns", value="cooldowns"),
            app_commands.Choice(name="Plot (The Blinking)", value="plot"),
        ]
    )
    async def world_info(self, interaction: discord.Interaction, action: str = "time"):
        if action == "time":
            await self._time(interaction)
        elif action == "weather":
            await self._weather(interaction)
        elif action == "forecast":
            await self._weatherforecast(interaction)
        elif action == "cooldowns":
            await self._cooldowns(interaction)
        elif action == "plot":
            await self._plot(interaction)

    async def _time(self, interaction: discord.Interaction):
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.get_world(guild_id)
        from config import LUNAR_BIRTH_AGING, ROLLOVER_TIMEZONE
        from engine.lunar import lunar_phase_label, rollover_now

        now = rollover_now(ROLLOVER_TIMEZONE)
        embed = howlbert_embed(
            f"Sunrise {world['day_number']}; {time_label(world['time_of_day'])}",
            (
                f"{season_label(world['season'])}\n{season_blurb(world['season'])}\n"
                f"{season_activity_blurb(world['season'])}\n\n"
                f"{time_blurb(world['time_of_day'])}\n\n"
                f"**Moon:** {lunar_phase_label(now)}"
            ),
        )
        age_line = (
            "Wolves age when the sky matches their birth moon (new / half / full)."
            if LUNAR_BIRTH_AGING
            else "Each sunrise ages every wolf one moon."
        )
        embed.set_footer(
            text=f"{format_sunrise(world['day_number'])} since the den began counting · {age_line}"
        )
        await interaction.response.send_message(embed=embed)

    async def _plot(self, interaction: discord.Interaction):
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.get_world(guild_id)
        from engine.plot_blinking import PLOT_TITLE, plot_status_fields

        embed = howlbert_embed(
            PLOT_TITLE,
            "Canon-first RP frame; mechanics apply while a phase is active.",
        )
        for name, value, inline in plot_status_fields(world):
            embed.add_field(name=name, value=value, inline=inline)
        phase = int(world["plot_phase"]) if "plot_phase" in world.keys() else 0
        if phase > 0:
            embed.set_footer(
                text=(
                    f"Sunrise {world['day_number']} · {season_label(world['season'])} · "
                    "accept plot quests on `/quest action:board`"
                )
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="setplotphase",
        description="Set Book One plot phase 0–12 (server admin). 0 = off.",
    )
    @app_commands.describe(phase="0 = off, 1–12 = The Blinking beats")
    async def setplotphase(self, interaction: discord.Interaction, phase: int):
        if not is_howlbert_admin(interaction):
            embed = howlbert_embed(
                "Denied",
                "Only server admins may set the plot phase.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.set_plot_phase(guild_id, phase)
        from engine.plot_blinking import PLOT_TITLE, phase_meta

        meta = phase_meta(int(world["plot_phase"]))
        if meta:
            body = f"Phase **{world['plot_phase']}** — **{meta['title']}**\n_{meta['news']}_"
        else:
            body = "Plot **off**; Book One mechanics paused."
        embed = howlbert_embed(PLOT_TITLE, body, color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="plotadvance",
        description="Advance Book One to the next plot phase (server admin).",
    )
    async def plotadvance(self, interaction: discord.Interaction):
        if not is_howlbert_admin(interaction):
            embed = howlbert_embed(
                "Denied",
                "Only server admins may advance the plot.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        new_phase, world = db.advance_plot_phase(guild_id)
        from engine.plot_blinking import PLOT_TITLE, phase_meta

        meta = phase_meta(new_phase)
        if meta:
            body = (
                f"Advanced to phase **{new_phase}** — **{meta['title']}**\n"
                f"_{meta['news']}_\n\n{meta['mechanics']}"
            )
        else:
            body = "Plot is off or already at phase 12."
        embed = howlbert_embed(PLOT_TITLE, body, color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="setseason",
        description="Set the in-game season (server admin).",
    )
    @app_commands.describe(season="Which season the den is in")
    @app_commands.choices(
        season=[
            app_commands.Choice(name="Newgrowth (spring)", value="spring"),
            app_commands.Choice(name="Highsun (summer)", value="summer"),
            app_commands.Choice(name="Leaf-drop (autumn)", value="autumn"),
            app_commands.Choice(name="Leaf-bare (winter)", value="winter"),
        ]
    )
    async def setseason(self, interaction: discord.Interaction, season: str):
        if not is_howlbert_admin(interaction):
            embed = howlbert_embed(
                "Denied",
                "Only server admins may set the season.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.get_world(guild_id)
        old_day = int(world["day_number"])
        new_day = db.align_day_to_season(old_day, season)
        world = db.save_world(
            guild_id,
            day_number=new_day,
            season=season,
            weather=world["weather"],
            time_of_day=world["time_of_day"],
        )
        day_note = ""
        if new_day != old_day:
            day_note = f"\nSunrise counter adjusted **{old_day}** → **{new_day}** so rollovers stay in sync."
        embed = howlbert_embed(
            "Season Set",
            f"The den is now in **{season_label(season)}**.\n{season_blurb(season)}{day_note}",
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed)

    async def _weather(self, interaction: discord.Interaction):
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.get_world(guild_id)
        modifier = WEATHER_HUNT_MODIFIERS.get(world["weather"], 0)
        effect = "No effect on hunts." if modifier == 0 else f"{modifier:+d}% hunt bones (weather)."
        season_effect = season_hunt_modifier_label(world["season"])

        embed = howlbert_embed(weather_label(world["weather"]), f"{effect}\n{season_effect.capitalize()}.")
        await interaction.response.send_message(embed=embed)

    async def _weatherforecast(self, interaction: discord.Interaction):
        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.get_world(guild_id)
        forecast = forecast_weather(world["weather"])
        lines = [f"**Day {world['day_number'] + i}**; {weather_label(w)}" for i, w in enumerate(forecast, 1)]
        embed = howlbert_embed("Weather Forecast", "\n".join(lines))
        await interaction.response.send_message(embed=embed)

    async def _cooldowns(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed(
                "Not Registered",
                "Use `/register` first.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_id = self._guild_id(interaction)
        day = db.get_world(guild_id)["day_number"] if guild_id else 0
        account = db.get_account(interaction.user.id)
        prestige_tier = account["prestige_tier"] if account else 0

        embed = howlbert_embed(f"Cooldowns; Day {day}" if guild_id else "Cooldowns")
        is_booster = bool(
            isinstance(interaction.user, discord.Member) and interaction.user.premium_since
        )
        donor_bonus = donor_daily_bonus(interaction.user.id)
        for name, value, inline in build_cooldown_fields(
            user,
            day,
            guild_id=guild_id,
            prestige_tier=prestige_tier,
            is_booster=is_booster,
            donor_bonus=donor_bonus,
            discord_admin=is_howlbert_admin(interaction),
        ):
            embed.add_field(name=name, value=value, inline=inline)
        embed = trim_embed_fields(embed)
        if guild_id:
            embed.set_footer(
                text="Activities reset each sunrise. Patrol/scout need an active pack war. "
                "Wolves age 1 moon per sunrise."
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="hazard",
        description="Face a weather hazard; opposed roll vs the environment.",
    )
    @app_commands.describe(
        hazard="Type of weather hazard",
        severity="How severe the conditions are",
    )
    @app_commands.choices(
        hazard=[
            app_commands.Choice(name="Blizzard", value="blizzard"),
            app_commands.Choice(name="Flood / Rapid River", value="flood"),
            app_commands.Choice(name="Wildfire Smoke", value="wildfire_smoke"),
            app_commands.Choice(name="Freezing Rain / Ice", value="freezing_rain"),
            app_commands.Choice(name="Extreme Heat", value="extreme_heat"),
            app_commands.Choice(name="Thick Fog", value="thick_fog"),
            app_commands.Choice(name="Thunderstorm", value="thunderstorm"),
            app_commands.Choice(name="Avalanche", value="avalanche"),
            app_commands.Choice(name="Deep Snow", value="deep_snow"),
            app_commands.Choice(name="Quicksand / Mud", value="quicksand"),
        ],
        severity=[
            app_commands.Choice(name="Moderate", value="moderate"),
            app_commands.Choice(name="Severe", value="severe"),
            app_commands.Choice(name="Extreme", value="extreme"),
        ],
    )
    async def hazard(
        self,
        interaction: discord.Interaction,
        hazard: str,
        severity: str = "severe",
    ):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed("Not Registered", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from engine.weather_hazards import format_hazard_result, resolve_weather_hazard

        result = resolve_weather_hazard(user, hazard, severity)
        if result["damage"]:
            new_hp = max(0, user["hp"] - result["damage"])
            db.set_user_conditions(interaction.user.id, hp=new_hp)
            if new_hp == 0:
                db.enter_dying_state(interaction.user.id)

        effects = result.get("effects") or {}
        if effects.get("exhaustion"):
            db.set_user_conditions(
                interaction.user.id,
                exhaustion=min(6, int(user["exhaustion"]) + int(effects["exhaustion"])),
            )
        if effects.get("thirst_loss"):
            db.adjust_thirst(user["id"], -int(effects["thirst_loss"]))
        if effects.get("mood_loss"):
            db.adjust_mood(user["id"], -int(effects["mood_loss"]))
        if effects.get("smoke_debuff"):
            db.update_user(interaction.user.id, wolf_id=user["id"], smoke_debuff=1)
        if hazard in ("blizzard", "freezing_rain", "deep_snow") and not result["success"]:
            from engine.disease_contract import try_weather_fever_exposure

            fever = try_weather_fever_exposure(user)
            if fever:
                effects = dict(effects)
                effects["fever_note"] = fever

        color = SUCCESS_COLOR if result["success"] else ERROR_COLOR
        embed = howlbert_embed("Weather Hazard", format_hazard_result(result), color=color)
        if effects.get("fever_note"):
            embed.description = (embed.description or "") + f"\n\n{effects['fever_note']}"
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rollover", description="Advance the in-game day (admin).")
    async def rollover(self, interaction: discord.Interaction):
        if not is_howlbert_admin(interaction):
            embed = howlbert_embed("Denied", "Only server admins may call a rollover.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_id = self._guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world, crisis = db.perform_rollover(guild_id)
        from engine.rollover_announce import build_rollover_embed

        embed = build_rollover_embed(world, crisis)
        await interaction.response.send_message(embed=embed)

        from utils.notifications import notify_births_ready_after_rollover

        await notify_births_ready_after_rollover(self.bot, world["day_number"])

    @app_commands.command(
        name="wilderness",
        description="Travel hazards, random encounters, or rest omens.",
    )
    @app_commands.describe(
        action="travel, encounter, or omen",
        territory="River, swamp, mountain, forest, or Twolegplace (travel)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Travel hazard", value="travel"),
            app_commands.Choice(name="Random encounter", value="encounter"),
            app_commands.Choice(name="Rest omen", value="omen"),
        ],
        territory=[
            app_commands.Choice(name="River", value="river"),
            app_commands.Choice(name="Swamp", value="swamp"),
            app_commands.Choice(name="Mountain", value="mountain"),
            app_commands.Choice(name="Forest", value="forest"),
            app_commands.Choice(name="Twolegplace", value="twolegplace"),
        ],
    )
    async def wilderness(
        self,
        interaction: discord.Interaction,
        action: str,
        territory: str = "forest",
    ):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.get_world(interaction.guild.id)
        day = world["day_number"]

        if action == "travel":
            from engine.travel_hazards import roll_travel_hazard

            ok, body = roll_travel_hazard(
                user, territory, day=day, season=world["season"], guild_id=interaction.guild.id
            )
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            embed = howlbert_embed("Travel Hazard", body, color=color)
            await interaction.response.send_message(embed=embed)
            return

        if action == "encounter":
            from engine.travel_hazards import roll_wilderness_encounter

            kind, body = roll_wilderness_encounter()
            if world["season"] == "spring" and kind == "encounter":
                body += "\n_Spring mating season; rivals may challenge (`/courtship action:rival`)._"
            embed = howlbert_embed("Wilderness", body)
            await interaction.response.send_message(embed=embed)
            return

        from engine.travel_hazards import roll_rest_omen

        kind, body = roll_rest_omen()
        if kind == "good":
            db.update_user_by_id(user["id"], omen_buff="good")
            body += "\n_Advantage on your first roll next sunrise._"
        elif kind == "bad":
            db.update_user_by_id(user["id"], omen_buff="bad")
            body += "\n_Disadvantage on your first roll next sunrise._"
        elif kind == "vision":
            new_mood = db.adjust_mood(user["id"], 4)
            body += f"\n**+4 mood** (now **{new_mood}**)."
        embed = howlbert_embed("StarClan Omen", body)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(World(bot))
