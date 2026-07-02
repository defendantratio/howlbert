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

    ROLLOVER_TIMEZONE,

)

from engine.world import season_label, time_label, weather_label

from engine.lunar import BIRTH_LUNAR_LABELS, active_lunar_phase, rollover_now

from utils.embeds import SUCCESS_COLOR, howlbert_embed



logger = logging.getLogger("howlbert")



_FIELD_LIMIT = 1024  # Discord embed field value character limit


def _clip(text: str) -> str:
    """Clip a field value to Discord's 1024-character hard limit."""
    return text[:_FIELD_LIMIT]


def _format_crisis_lines(entries: list, *, limit: int = 12) -> str:
    """Format rollover note dicts (or legacy plain strings)."""
    lines: list[str] = []
    for entry in entries[:limit]:
        if isinstance(entry, dict):
            name = entry.get("wolf_name") or "Den"
            lines.append(f"**{name}**; {entry.get('line', '')}")
        else:
            lines.append(str(entry))
    if len(entries) > limit:
        lines.append(f"_…and {len(entries) - limit} more._")
    return _clip("\n".join(lines))


def build_rollover_embed(world, crisis: dict) -> discord.Embed:

    embed = howlbert_embed("the den rollovers", color=SUCCESS_COLOR)

    embed.add_field(name="day", value=str(world["day_number"]), inline=True)

    embed.add_field(name="season", value=season_label(world["season"]), inline=True)

    embed.add_field(name="weather", value=weather_label(world["weather"]), inline=True)

    embed.add_field(name="time", value=time_label(world["time_of_day"]), inline=True)



    sky = crisis.get("lunar_phase_label")

    if sky:

        embed.add_field(name="moon", value=sky, inline=True)

    aged = crisis.get("wolves_aged", 0)

    if LUNAR_BIRTH_AGING and aged is not None:

        embed.add_field(name="aged this sunrise", value=str(aged), inline=True)



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

        embed.add_field(name="collapsed", value=_clip("\n".join(lines)), inline=False)

    if stabilized:

        lines = [f"**{d['wolf_name']}**; stabilized after {d['cause']}" for d in stabilized[:10]]

        embed.add_field(name="stabilized", value=_clip("\n".join(lines)), inline=False)

    if deaths:

        loss_lines = [f"**{d['wolf_name']}**; died of {d['cause']}" for d in deaths[:10]]

        if len(deaths) > 10:

            loss_lines.append(f"_…and {len(deaths) - 10} more._")

        loss_lines.append(
            "_medics: `/medic action:lay_to_rest` · mates may need comfort and herbs._"
        )

        embed.add_field(name="losses", value=_clip("\n".join(loss_lines)), inline=False)

    grief_notes = crisis.get("grief_notes", [])

    if grief_notes:

        embed.add_field(
            name="grief in the den",
            value=_format_crisis_lines(grief_notes, limit=8),
            inline=False,
        )



    den_news = crisis.get("den_news", {})

    for label, key in (

        ("🎂 Birthdays", "birthdays"),

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

            embed.add_field(name=label, value=_clip(text), inline=False)



    vitals_ex = crisis.get("vitals_exhaustion", [])

    if vitals_ex:

        text = "\n".join(

            f"**{e['wolf_name']}**; {e['cause']} → exhaustion **{e['old_exhaustion']}** → **{e['new_exhaustion']}**"

            for e in vitals_ex[:8]

        )

        if len(vitals_ex) > 8:

            text += f"\n_…and {len(vitals_ex) - 8} more._"

        embed.add_field(name="needs exhaustion", value=_clip(text), inline=False)



    condition_notes = crisis.get("condition_notes", [])

    if condition_notes:
        embed.add_field(
            name="injuries & disease",
            value=_format_crisis_lines(condition_notes, limit=12),
            inline=False,
        )

    mental_notes = crisis.get("mental_notes", [])
    if mental_notes:
        embed.add_field(
            name="mind & stress",
            value=_format_crisis_lines(mental_notes, limit=8),
            inline=False,
        )

    passive_scavenge = crisis.get("passive_scavenge", [])
    if passive_scavenge:
        embed.add_field(
            name="foraged for themselves",
            value=_format_crisis_lines(passive_scavenge, limit=8),
            inline=False,
        )

    cold_injury = crisis.get("cold_injury", [])
    if cold_injury:
        embed.add_field(
            name="winter cold worsens wounds",
            value=_format_crisis_lines(cold_injury, limit=8),
            inline=False,
        )

    pup_cold = crisis.get("pup_cold", [])
    if pup_cold:
        embed.add_field(
            name="pups chilled in the night",
            value=_format_crisis_lines(pup_cold, limit=8),
            inline=False,
        )

    prey_spoilage = crisis.get("prey_spoilage", [])
    if prey_spoilage:
        embed.add_field(
            name="rotting prey",
            value=_format_crisis_lines(prey_spoilage, limit=8),
            inline=False,
        )



    forager_herbs = crisis.get("forager_herbs", [])

    if forager_herbs:

        lines = [f"**{g['wolf_name']}**; **{g['herb']}**" for g in forager_herbs[:8]]

        if len(forager_herbs) > 8:

            lines.append(f"_…and {len(forager_herbs) - 8} more._")

        embed.add_field(name="forager finds", value=_clip("\n".join(lines)), inline=False)



    season_notes = crisis.get("season_notes", [])

    if season_notes:

        embed.add_field(name="season", value=_clip("\n".join(season_notes)), inline=False)

    plot_notes = crisis.get("plot_notes", [])
    if plot_notes:
        text = "\n".join(plot_notes[:8])
        if len(plot_notes) > 8:
            text += f"\n_…and {len(plot_notes) - 8} more._"
        embed.add_field(name="the blinking", value=_clip(text), inline=False)



    food_cache = crisis.get("food_cache", [])

    if food_cache:

        lines = [f"**{n['wolf_name']}**; {n['text']}" for n in food_cache[:8]]

        embed.add_field(name="food cache", value=_clip("\n".join(lines)), inline=False)



    sacred_notes = crisis.get("sacred_notes", [])

    if sacred_notes:

        lines = [f"**{n['wolf_name']}:** {n['text']}" for n in sacred_notes[:6]]

        embed.add_field(name="sacred neglect", value=_clip("\n".join(lines)), inline=False)



    age_note = (

        "age +1 moon when the sky matches your birth phase (new / half / full)."

        if LUNAR_BIRTH_AGING

        else "Age +1 moon each sunrise."

    )

    embed.set_footer(

        text=(

            "hunger −12 · thirst −14 · low mood/hunger/thirst +1 exhaustion each. "

            "Exhaustion 6 = death. At 0 hunger/thirst, collapse: `/medic action:deathsaves`. "

            f"long-rest: +1 hp, −1 exhaustion. {age_note}"

        )

    )

    return embed



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



async def run_guild_rollover(
    bot: commands.Bot, guild_id: int,
) -> int:
    """Perform every due rollover (including catch-up after downtime). Returns count rolled."""
    now = rollover_now(ROLLOVER_TIMEZONE)
    missed = missed_rollover_count(guild_id, now)
    if missed == 0:
        return 0

    capped = min(missed, MAX_ROLLOVER_CATCHUP)
    if capped < missed:
        logger.warning(
            "guild %s missed %s sunrises; catching up %s (cap %s).",
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
                    embed.title = f"sunrise catch-up ({i + 1}/{capped})"
                await channel.send(embed=embed)
            except discord.HTTPException as exc:
                logger.warning("Could not announce rollover in guild %s: %s", guild_id, exc)
        if world:
            from engine.rp_ambience import post_rp_ambience

            try:
                await post_rp_ambience(bot, guild_id, world)
            except Exception:
                logger.exception("RP ambience failed for guild %s", guild_id)
        await notify_births_ready_after_rollover(bot, world["day_number"])

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
        "auto rollover on at %02d:%02d %s (lunar birth aging: %s).",
        ROLLOVER_HOUR,
        ROLLOVER_MINUTE,
        ROLLOVER_TIMEZONE,
        LUNAR_BIRTH_AGING,
    )

    first_pass = True

    while not bot.is_closed():

        try:
            now = rollover_now(ROLLOVER_TIMEZONE)
            for guild in bot.guilds:

                try:

                    db.get_world(guild.id)
                    due = guild_due_for_rollover(guild.id, now)
                    if first_pass:
                        logger.info(
                            "Startup rollover guild %s: due=%s",
                            guild.id,
                            due,
                        )
                    rolled = await run_guild_rollover(bot, guild.id)

                except Exception:

                    logger.exception("Auto rollover failed for guild %s", guild.id)

            first_pass = False

        except Exception:

            logger.exception("Auto rollover loop error")

        await asyncio.sleep(60)





def start_auto_rollover(bot: commands.Bot) -> None:

    if AUTO_ROLLOVER_ENABLED:

        bot.loop.create_task(auto_rollover_loop(bot))

