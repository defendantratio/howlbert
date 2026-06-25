"""Rollover embed + auto-scheduler."""



from __future__ import annotations



import asyncio

import logging

from datetime import datetime, timedelta



import discord

from discord.ext import commands



import database as db

from config import (

    AUTO_ROLLOVER_ANNOUNCE_CHANNEL_ID,

    AUTO_ROLLOVER_ENABLED,

    LUNAR_BIRTH_AGING,

    ROLLOVER_HOUR,

    ROLLOVER_MINUTE,

    ROLLOVER_STARTUP_DM_HOURS,

    ROLLOVER_TIMEZONE,

)

from engine.world import season_label, time_label, weather_label

from engine.lunar import BIRTH_LUNAR_LABELS, active_lunar_phase, rollover_now

from utils.embeds import SUCCESS_COLOR, howlbert_embed



logger = logging.getLogger("howlbert")





def build_rollover_embed(world, crisis: dict) -> discord.Embed:

    embed = howlbert_embed("The Den Rollovers", color=SUCCESS_COLOR)

    embed.add_field(name="Day", value=str(world["day_number"]), inline=True)

    embed.add_field(name="Season", value=season_label(world["season"]), inline=True)

    embed.add_field(name="Weather", value=weather_label(world["weather"]), inline=True)

    embed.add_field(name="Time", value=time_label(world["time_of_day"]), inline=True)



    sky = crisis.get("lunar_phase_label")

    if sky:

        embed.add_field(name="Moon", value=sky, inline=True)

    aged = crisis.get("wolves_aged", 0)

    if LUNAR_BIRTH_AGING and aged is not None:

        embed.add_field(name="Aged this sunrise", value=str(aged), inline=True)



    collapses = crisis.get("collapses", [])

    deaths = crisis.get("deaths", [])

    stabilized = crisis.get("stabilized", [])

    if collapses:

        lines = [

            f"**{d['wolf_name']}**; collapsed from {d['cause']} · use **`/medic action:deathsaves`**"

            for d in collapses[:10]

        ]

        if len(collapses) > 10:

            lines.append(f"_…and {len(collapses) - 10} more._")

        embed.add_field(name="Collapsed", value="\n".join(lines), inline=False)

    if stabilized:

        lines = [f"**{d['wolf_name']}**; stabilized after {d['cause']}" for d in stabilized[:10]]

        embed.add_field(name="Stabilized", value="\n".join(lines), inline=False)

    if deaths:

        loss_lines = [f"**{d['wolf_name']}**; died of {d['cause']}" for d in deaths[:10]]

        if len(deaths) > 10:

            loss_lines.append(f"_…and {len(deaths) - 10} more._")

        embed.add_field(name="Losses", value="\n".join(loss_lines), inline=False)



    den_news = crisis.get("den_news", {})

    for label, key in (

        ("Age milestones", "age_ups"),

        ("Births ready", "births_ready"),

        ("Expectant mates", "pregnancy_alerts"),

        ("Low treasury", "treasury_warnings"),

        ("Den events", "pack_events"),

    ):

        items = den_news.get(key, [])

        if items:

            text = "\n".join(items[:8])

            if len(items) > 8:

                text += f"\n_…and {len(items) - 8} more._"

            embed.add_field(name=label, value=text, inline=False)



    vitals_ex = crisis.get("vitals_exhaustion", [])

    if vitals_ex:

        text = "\n".join(

            f"**{e['wolf_name']}**; {e['cause']} → exhaustion **{e['old_exhaustion']}** → **{e['new_exhaustion']}**"

            for e in vitals_ex[:8]

        )

        if len(vitals_ex) > 8:

            text += f"\n_…and {len(vitals_ex) - 8} more._"

        embed.add_field(name="Needs exhaustion", value=text, inline=False)



    condition_notes = crisis.get("condition_notes", [])

    if condition_notes:

        lines = [f"**{n['wolf_name']}**; {n['line']}" for n in condition_notes[:12]]

        if len(condition_notes) > 12:

            lines.append(f"_…and {len(condition_notes) - 12} more._")

        embed.add_field(name="Injuries & disease", value="\n".join(lines), inline=False)



    forager_herbs = crisis.get("forager_herbs", [])

    if forager_herbs:

        lines = [f"**{g['wolf_name']}**; **{g['herb']}**" for g in forager_herbs[:8]]

        if len(forager_herbs) > 8:

            lines.append(f"_…and {len(forager_herbs) - 8} more._")

        embed.add_field(name="Forager finds", value="\n".join(lines), inline=False)



    season_notes = crisis.get("season_notes", [])

    if season_notes:

        embed.add_field(name="Season", value="\n".join(season_notes), inline=False)



    food_cache = crisis.get("food_cache", [])

    if food_cache:

        lines = [f"**{n['wolf_name']}**; {n['text']}" for n in food_cache[:8]]

        embed.add_field(name="Food cache", value="\n".join(lines), inline=False)



    sacred_notes = crisis.get("sacred_notes", [])

    if sacred_notes:

        lines = [f"**{n['wolf_name']}:** {n['text']}" for n in sacred_notes[:6]]

        embed.add_field(name="Sacred neglect", value="\n".join(lines), inline=False)



    age_note = (

        "Age +1 moon when the sky matches your birth phase (new / half / full)."

        if LUNAR_BIRTH_AGING

        else "Age +1 moon each sunrise."

    )

    embed.set_footer(

        text=(

            "Hunger −12 · thirst −14 · low mood/hunger/thirst +1 exhaustion each. "

            "Exhaustion 6 = death. At 0 hunger/thirst, collapse: `/medic action:deathsaves`. "

            f"Long-rest: +1 HP, −1 exhaustion. {age_note}"

        )

    )

    return embed


def build_startup_briefing_crisis(guild_id: int, world) -> dict:
    """Den-news snapshot for morning startup when sunrise already rolled."""
    from engine.lunar import BIRTH_LUNAR_LABELS, active_lunar_phase, lunar_phase_label, rollover_now
    from engine.plot_blinking import plot_den_news_line, plot_phase
    from engine.rollover_news import collect_den_news

    day = int(world["day_number"])
    crisis: dict = {"den_news": collect_den_news(day, [])}
    phase = plot_phase(guild_id)
    if phase > 0:
        line = plot_den_news_line(phase, day)
        if line:
            crisis["den_news"].setdefault("pack_events", []).append(line)
    sky = active_lunar_phase(rollover_now(ROLLOVER_TIMEZONE))
    crisis["lunar_phase_label"] = (
        BIRTH_LUNAR_LABELS[sky] if sky else lunar_phase_label(rollover_now(ROLLOVER_TIMEZONE))
    )
    return crisis


async def maybe_send_startup_den_briefing(
    bot: commands.Bot, guild: discord.Guild, *, now: datetime
) -> None:
    """DM den news when the bot starts in the morning window but sunrise already ran."""
    if not within_startup_den_news_dm_window(now):
        return
    if guild_due_for_rollover(guild.id, now):
        return
    world = db.get_world(guild.id)
    crisis = build_startup_briefing_crisis(guild.id, world)
    from utils.notifications import notify_den_news_after_rollover

    try:
        await notify_den_news_after_rollover(
            bot, guild, world, crisis, catch_up_days=0, briefing=True
        )
    except Exception:
        logger.exception("Startup den briefing DM failed for guild %s", guild.id)


def _rollover_moment(day: datetime.date, tz) -> datetime:

    return datetime(

        day.year,

        day.month,

        day.day,

        ROLLOVER_HOUR,

        ROLLOVER_MINUTE,

        tzinfo=tz,

    )





def _parse_last_rollover(raw: str | None) -> datetime | None:

    if not raw:

        return None

    try:

        return datetime.fromisoformat(raw)

    except ValueError:

        return None





# Cap catch-up so a long outage does not block startup for minutes.
MAX_ROLLOVER_CATCHUP = 31


def missed_rollover_count(guild_id: int, now: datetime) -> int:
    """Scheduled sunrises that passed while the bot was offline (or not yet rolled)."""
    world = db.get_world(guild_id)
    last = _parse_last_rollover(world["last_rollover"])
    tz = now.tzinfo
    if last is None:
        return 1 if now >= _rollover_moment(now.date(), tz) else 0

    last_local = last.astimezone(tz)
    count = 0
    day = last_local.date()
    while day <= now.date():
        moment = _rollover_moment(day, tz)
        if moment > last_local and now >= moment:
            count += 1
        day += timedelta(days=1)
    return count


def guild_due_for_rollover(guild_id: int, now: datetime) -> bool:
    return missed_rollover_count(guild_id, now) > 0


def within_startup_den_news_dm_window(now: datetime) -> bool:
    """
    True when the bot came online soon after today's scheduled sunrise.
    Used to DM den news when rollover was missed because the bot was offline.
    """
    tz = now.tzinfo
    moment = _rollover_moment(now.date(), tz)
    if now < moment:
        return False
    return now <= moment + timedelta(hours=ROLLOVER_STARTUP_DM_HOURS)


async def run_guild_rollover(
    bot: commands.Bot, guild_id: int, *, dm_den_news: bool = False
) -> int:
    """Perform every due rollover (including catch-up after downtime). Returns count rolled."""
    now = rollover_now(ROLLOVER_TIMEZONE)
    missed = missed_rollover_count(guild_id, now)
    if missed == 0:
        return 0

    capped = min(missed, MAX_ROLLOVER_CATCHUP)
    if capped < missed:
        logger.warning(
            "Guild %s missed %s sunrises; catching up %s (cap %s).",
            guild_id,
            missed,
            capped,
            MAX_ROLLOVER_CATCHUP,
        )

    channel = await _resolve_announce_channel(bot, guild_id)
    from utils.notifications import notify_births_ready_after_rollover

    world = None
    for i in range(capped):
        world, crisis = db.perform_rollover(guild_id, rollover_at=now)
        if channel:
            try:
                embed = build_rollover_embed(world, crisis)
                if capped > 1:
                    embed.title = f"Sunrise catch-up ({i + 1}/{capped})"
                await channel.send(embed=embed)
            except discord.HTTPException as exc:
                logger.warning("Could not announce rollover in guild %s: %s", guild_id, exc)
        await notify_births_ready_after_rollover(bot, world["day_number"])

    if dm_den_news and world and crisis:
        guild = bot.get_guild(guild_id)
        if guild:
            from utils.notifications import notify_den_news_after_rollover

            try:
                await notify_den_news_after_rollover(
                    bot, guild, world, crisis, catch_up_days=capped
                )
            except Exception:
                logger.exception("Den news DM failed for guild %s", guild_id)

    logger.info(
        "Auto rollover guild %s: %s sunrise(s) → day %s",
        guild_id,
        capped,
        world["day_number"] if world else "?",
    )
    return capped





async def _resolve_announce_channel(

    bot: commands.Bot, guild_id: int

) -> discord.TextChannel | None:

    if AUTO_ROLLOVER_ANNOUNCE_CHANNEL_ID:

        ch = bot.get_channel(AUTO_ROLLOVER_ANNOUNCE_CHANNEL_ID)

        if isinstance(ch, discord.TextChannel) and ch.guild.id == guild_id:

            return ch

        try:

            fetched = await bot.fetch_channel(AUTO_ROLLOVER_ANNOUNCE_CHANNEL_ID)

            if isinstance(fetched, discord.TextChannel) and fetched.guild.id == guild_id:

                return fetched

        except discord.HTTPException:

            pass



    guild = bot.get_guild(guild_id)

    if not guild:

        return None

    if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:

        return guild.system_channel

    for channel in guild.text_channels:

        if channel.permissions_for(guild.me).send_messages:

            return channel

    return None





async def auto_rollover_loop(bot: commands.Bot) -> None:

    await bot.wait_until_ready()

    if not AUTO_ROLLOVER_ENABLED:

        logger.info("AUTO_ROLLOVER_ENABLED is off; use /rollover manually.")

        return



    logger.info(
        "Auto rollover on at %02d:%02d %s (lunar birth aging: %s; startup DM window %sh).",
        ROLLOVER_HOUR,
        ROLLOVER_MINUTE,
        ROLLOVER_TIMEZONE,
        LUNAR_BIRTH_AGING,
        ROLLOVER_STARTUP_DM_HOURS,
    )

    first_pass = True

    while not bot.is_closed():

        try:
            now = rollover_now(ROLLOVER_TIMEZONE)
            dm_on_catchup = first_pass and within_startup_den_news_dm_window(now)

            for guild in bot.guilds:

                try:

                    db.get_world(guild.id)
                    due = guild_due_for_rollover(guild.id, now)
                    if first_pass:
                        logger.info(
                            "Startup rollover guild %s: due=%s dm_window=%s",
                            guild.id,
                            due,
                            dm_on_catchup,
                        )
                    rolled = await run_guild_rollover(
                        bot, guild.id, dm_den_news=dm_on_catchup and due
                    )
                    if first_pass and dm_on_catchup and rolled == 0:
                        await maybe_send_startup_den_briefing(bot, guild, now=now)

                except Exception:

                    logger.exception("Auto rollover failed for guild %s", guild.id)

            first_pass = False

        except Exception:

            logger.exception("Auto rollover loop error")

        await asyncio.sleep(60)





def start_auto_rollover(bot: commands.Bot) -> None:

    if AUTO_ROLLOVER_ENABLED:

        bot.loop.create_task(auto_rollover_loop(bot))

