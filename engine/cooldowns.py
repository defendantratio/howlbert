"""Per-sunrise activity status for /cooldowns."""

from __future__ import annotations

import sqlite3

import database as db
from config import BOOST_DAILY_BONUS, DAILY_REWARD, SNIFF_HUNT_BONUS_PCT
from engine.role_features import has_any_role, is_full_medic, wolf_role_key
from engine.prestige import apply_bone_bonus, bone_bonus_pct
from engine.role_privileges import (
    HERB_HEAL_DAILY_LIMIT,
    HERB_TREAT_DAILY_LIMIT,
    activity_cooldown_label,
    can_explore_again,
    can_forage_again,
    can_hunt_again,
    can_rescout_again,
    can_verge_forage_again,
    is_medic,
    is_scout,
    treat_limit_reached,
)
from utils.currency import format_bones

DROWN_SICK_ROLE = "drown_sick"


def _col(user: sqlite3.Row, name: str, default: int = 0) -> int:
    if name not in user.keys():
        return default
    return int(user[name])


def _used_today(user: sqlite3.Row, day: int, column: str) -> bool:
    return _col(user, column) >= day


def daily_stipend_amount(
    prestige_tier: int, *, is_booster: bool = False, donor_bonus: int = 0
) -> int:
    base = apply_bone_bonus(DAILY_REWARD, prestige_tier)
    if is_booster:
        base += BOOST_DAILY_BONUS
    if donor_bonus > 0:
        base += donor_bonus
    return base


def daily_ration_note(
    prestige_tier: int,
    *,
    pack_name: str | None = None,
    treasury: int | None = None,
    is_booster: bool = False,
    donor_bonus: int = 0,
) -> str:
    """Where `/bones action:daily` bones come from; shown on `/world action:cooldowns`."""
    base = DAILY_REWARD
    payout = daily_stipend_amount(
        prestige_tier, is_booster=is_booster, donor_bonus=donor_bonus
    )
    bonus_pct = bone_bonus_pct(prestige_tier)
    lines = [
        "paid from **pack treasury** each sunrise (hunt tax, `/pack deposit`, prey-pile shares).",
        f"stipend: **{format_bones(payout)}**",
    ]
    if is_booster:
        lines.append(
            f"_includes **+{BOOST_DAILY_BONUS}** den patron boost (paid to you, not treasury)._"
        )
    if donor_bonus > 0:
        lines.append(
            f"_includes **+{donor_bonus}** supporter thank-you (paid to you, not treasury)._"
        )
    if bonus_pct > 0:
        lines.append(
            f"_(base {format_bones(base)} + {bonus_pct}% prestige; +1 xp; debits treasury)_"
        )
    else:
        lines.append(f"_(base {format_bones(base)}; +1 xp; debits treasury)_")
    if pack_name is not None and treasury is not None:
        lines.append(f"**{pack_name}** treasury: **{format_bones(treasury)}**")
    return "\n".join(lines)


def daily_stipend_status(
    user: sqlite3.Row,
    day: int,
    prestige_tier: int,
    *,
    is_booster: bool = False,
    donor_bonus: int = 0,
) -> tuple[str, str]:
    """Status line + full note for /cooldowns daily field."""
    base_payout = daily_stipend_amount(prestige_tier, is_booster=False)
    payout = daily_stipend_amount(
        prestige_tier, is_booster=is_booster, donor_bonus=donor_bonus
    )
    from engine.role_features import is_rogue_wolf

    if is_rogue_wolf(user):
        note = (
            "**rogues** cannot draw a den stipend; earn bones with `/bones action:hunt`, "
            "`/bones action:work`, or `/field action:scavenge`."
        )
        if _used_today(user, day, "last_daily_day"):
            return "n/a", note
        return "rogue", note

    pack_id = user["pack_id"] if "pack_id" in user.keys() else None
    if not pack_id:
        note = daily_ration_note(prestige_tier)
        note += "\n**loners** cannot draw a stipend; `/setfaction` to join a great pack."
        if _used_today(user, day, "last_daily_day"):
            return "used", note
        return "no pack", note

    pack = db.get_pack(pack_id)
    treasury = int(pack["treasury"]) if pack else 0
    pack_name = pack["name"] if pack else "pack"
    note = daily_ration_note(
        prestige_tier,
        pack_name=pack_name,
        treasury=treasury,
        is_booster=is_booster,
        donor_bonus=donor_bonus,
    )

    if _used_today(user, day, "last_daily_day"):
        return "used", note
    if treasury < base_payout:
        return f"treasury low ({format_bones(treasury)} need {format_bones(base_payout)})", note
    return "ready", note


def build_cooldown_fields(
    user: sqlite3.Row,
    day: int,
    *,
    guild_id: int | None,
    prestige_tier: int = 0,
    is_booster: bool = False,
    donor_bonus: int = 0,
    discord_admin: bool = False,
) -> list[tuple[str, str, bool]]:
    """Return embed fields: (name, value, inline)."""
    if not guild_id:
        return [("server", "join a den server to track sunrise cooldowns.", False)]

    fields: list[tuple[str, str, bool]] = []

    def _status(user: sqlite3.Row, activity: str, *, ready: bool) -> str:
        return activity_cooldown_label(user, activity, ready=ready, day=day)

    daily_status, daily_note = daily_stipend_status(
        user, day, prestige_tier, is_booster=is_booster, donor_bonus=donor_bonus
    )
    fields.append(("/bones action:daily", f"{daily_status}\n{daily_note}", False))

    # Economy & gathering
    simple_day = [
        ("/bones action:hunt", "hunt", lambda: can_hunt_again(user, day)),
        ("/field action:forage", "forage", lambda: can_forage_again(user, day)),
        (
            "/field action:verge",
            "verge forage",
            lambda: can_verge_forage_again(user, day),
        ),
        ("/field action:scavenge", "scavenge", lambda: not _used_today(user, day, "last_scavenge_day")),
        ("/field action:track", "track", lambda: not _used_today(user, day, "last_track_day")),
        ("/field action:fishing", "fishing", lambda: not _used_today(user, day, "last_fishing_day")),
        ("/bones action:work", "work", lambda: not _used_today(user, day, "last_work_day")),
        ("/bones action:crime", "crime", lambda: not _used_today(user, day, "last_crime_day")),
    ]
    for label, key, ready_fn in simple_day:
        ready = ready_fn()
        fields.append((label, _status(user, key, ready=ready), True))

    fields.append(
        (
            "/preypile",
            _status(user, "preypile", ready=not _used_today(user, day, "last_prey_pile_day")),
            True,
        )
    )

    from engine.conditions import manual_long_rest_used_today

    rest_long = _status(user, "rest", ready=not manual_long_rest_used_today(user, day))
    used_heals = _col(user, "herb_heals_today")
    if is_medic(user):
        heal_line = "short herb: **unlimited** comfrey (green tongue)"
    else:
        heal_line = f"short herb: **{used_heals}/{HERB_HEAL_DAILY_LIMIT}** comfrey"
    fields.append(
        (
            "/vitals action:rest",
            f"long: **{rest_long}** · {heal_line}",
            True,
        )
    )

    if is_medic(user):
        treat_line = _status(user, "treat", ready=True)
        stabilize_line = _status(user, "stabilize", ready=True)
    else:
        used_treats = _col(user, "herb_treats_today")
        treat_ready = _status(user, "treat", ready=not treat_limit_reached(user))
        treat_line = f"**{used_treats}/{HERB_TREAT_DAILY_LIMIT}** today · {treat_ready}"
        stabilize_line = "ready; medicine dc 15 (herbs optional)"
    fields.append(
        (
            "/medic action:treat · /medic action:stabilize",
            f"treat: {treat_line}\nstabilize: {stabilize_line}",
            False,
        )
    )

    fields.append(
        (
            "/howl",
            _status(user, "howl", ready=not _used_today(user, day, "last_howl_day")),
            True,
        )
    )
    fields.append(
        (
            "/sign",
            _status(user, "sign", ready=not _used_today(user, day, "last_sign_day")),
            True,
        )
    )
    fields.append(
        (
            "/sign read",
            _status(user, "read den signs", ready=not _used_today(user, day, "last_sign_read_day")),
            True,
        )
    )
    if wolf_role_key(user) == "medic":
        fields.append(
            (
                "/medic action:checkup",
                _status(
                    user,
                    "den checkup",
                    ready=not _used_today(user, day, "last_medic_rounds_day"),
                ),
                True,
            )
        )
    sniff_ready = not _used_today(user, day, "last_sniff_day")
    sniff_bonus = int(user["sniff_bonus_day"]) >= day if "sniff_bonus_day" in user.keys() else False
    sniff_label = _status(user, "sniff", ready=sniff_ready)
    if sniff_bonus:
        sniff_label = f"{sniff_label} · **+{SNIFF_HUNT_BONUS_PCT}% hunt/track**"
    fields.append(
        (
            "/field action:sniff",
            sniff_label,
            True,
        )
    )
    fields.append(
        (
            "/explore venture",
            _status(user, "explore", ready=can_explore_again(user, day))
            + (
                "\n_Explore + rescout unlimited · survey/trail once each_"
                if is_scout(user)
                else ("\n_Resets next sunrise_" if not can_explore_again(user, day) else "")
            ),
            True,
        )
    )
    if is_scout(user):
        fields.append(
            (
                "/scout",
                "\n".join(
                    (
                        f"rescout: {_status(user, 'rescout', ready=can_rescout_again(user, day))} · unlimited",
                        f"survey: {_status(user, 'survey', ready=not _used_today(user, day, 'last_survey_day'))} · once/sunrise",
                        f"trail: {_status(user, 'trail', ready=not _used_today(user, day, 'last_trail_day'))} · once/sunrise",
                    )
                ),
                False,
            )
        )
    from engine.pack_leadership import can_run_pack_bulk_action

    pack_id = user["pack_id"] if "pack_id" in user.keys() else None
    pack = db.get_pack(pack_id) if pack_id else None
    if can_run_pack_bulk_action(user, pack, discord_admin=discord_admin):
        fields.append(
            (
                "/playpen action:playall",
                _status(user, "playall", ready=not _used_today(user, day, "last_playall_day")),
                True,
            )
        )
        if pack_id:
            feedall_ready = bool(pack) and int(pack["last_feedall_day"]) < day
            drinkall_day = (
                int(pack["last_drinkall_day"])
                if "last_drinkall_day" in pack.keys()
                else 0
            )
            drinkall_ready = bool(pack) and drinkall_day < day
            fields.append(
                (
                    "/packlife action:feedall",
                    _status(user, "feedall", ready=feedall_ready),
                    True,
                )
            )
            fields.append(
                (
                    "/packlife action:drinkall",
                    _status(user, "drinkall", ready=drinkall_ready),
                    True,
                )
            )
    elif pack_id:
        fields.append(
            (
                "pack-wide den commands",
                "alpha only: `/playpen action:playall`, `/packlife action:feedall`, "
                "`/packlife action:drinkall`",
                False,
            )
        )
    fields.append(
        (
            "/playpen action:play",
            _status(user, "play", ready=not _used_today(user, day, "last_play_day")),
            True,
        )
    )
    fields.append(
        (
            "/playpen action:socialize",
            _status(
                user,
                "socialize",
                ready=not _used_today(user, day, "last_socialize_day"),
            ),
            True,
        )
    )
    fields.append(
        (
            "/playpen action:groom",
            _status(user, "groom", ready=not _used_today(user, day, "last_groom_day")),
            True,
        )
    )
    from config import DRINK_COOLDOWN_MINUTES
    from engine.thirst import drink_cooldown_minutes
    from engine.wild_encounters import wild_encounter_cooldown_minutes

    drink_wait = drink_cooldown_minutes(user)
    fields.append(
        (
            "/drink",
            f"{_status(user, 'drink', ready=drink_wait == 0)}"
            + (f" · **{drink_wait}** min" if drink_wait else f" · every {DRINK_COOLDOWN_MINUTES} min"),
            True,
        )
    )
    ambush_wait = wild_encounter_cooldown_minutes(user)
    fields.append(
        (
            "/combat encounter",
            f"{_status(user, 'wild encounter', ready=ambush_wait == 0)}"
            + (f" · **{ambush_wait}** min" if ambush_wait else ""),
            True,
        )
    )
    fields.append(
        (
            "/role action:event",
            _status(user, "roleevent", ready=not _used_today(user, day, "last_role_event_day")),
            True,
        )
    )

    from engine.blooding import format_blooding_status

    blooding = format_blooding_status(user)
    if blooding:
        fields.append(("/bones action:hunt", f"needed for blooding\n{blooding}", False))

    role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
    if role == DROWN_SICK_ROLE:
        prophecy_ready = not _used_today(user, day, "last_prophecy_day")
        fields.append(
            (
                "/role action:prophecy",
                _status(user, "prophecy", ready=prophecy_ready),
                True,
            )
        )

    from engine.role_features import is_full_medic
    from engine.sacred_visits import format_sacred_visit_reminder, sacred_visit_due

    if is_full_medic(user):
        reminder = format_sacred_visit_reminder(user, day)
        if reminder:
            fields.append(
                (
                    "/medic action:sacred",
                    f"{_status(user, 'sacred visit', ready=not sacred_visit_due(user, day))}\n{reminder}",
                    False,
                )
            )
        surgery_ready = int(user["last_surgery_day"] if "last_surgery_day" in user.keys() else 0) < day
        fields.append(
            (
                "/medic action:surgery",
                _status(user, "surgery", ready=surgery_ready)
                + " · stitch · set bone · extract · amputate",
                True,
            )
        )

    fields.append(
        (
            "/courtship action:court",
            _status(user, "court", ready=not _used_today(user, day, "last_court_day")),
            True,
        )
    )
    fields.append(
        (
            "/pupcare action:adopt",
            _status(user, "adoptpup", ready=not _used_today(user, day, "last_adopt_day")),
            True,
        )
    )
    fields.append(
        (
            "/pupcare action:feed",
            _status(user, "nurse", ready=not _used_today(user, day, "last_nurse_day")),
            True,
        )
    )
    fields.append(
        (
            "den charm",
            _status(user, "den_charm", ready=not _used_today(user, day, "last_den_charm_day")),
            True,
        )
    )
    fields.append(
        (
            "/pack war",
            "\n".join(
                (
                    f"patrol: {_status(user, 'patrol', ready=not _used_today(user, day, 'last_patrol_day'))}",
                    f"scout: {_status(user, 'scout', ready=not _used_today(user, day, 'last_scout_day'))}",
                )
            ),
            False,
        )
    )

    if pack_id and guild_id:
        from config import CAT_PACT_RECEIVE_MIN_TRUST

        receive_ready = not _used_today(user, day, "last_cat_receive_day")
        trade_ready = not _used_today(user, day, "last_duplicate_trade_day")
        fields.append(
            (
                "/pact",
                "\n".join(
                    (
                        f"receive: {_status(user, 'cat receive', ready=receive_ready)} · trust **{CAT_PACT_RECEIVE_MIN_TRUST}+**",
                        f"trade duplicates: {_status(user, 'cat trade', ready=trade_ready)} · once/sunrise",
                    )
                ),
                False,
            )
        )

    return fields
