"""Per-wolf setup and daily todo list for `/checklist`."""

from __future__ import annotations

import database as db
from config import JUVENILE_MAX_MOONS, PUP_MAX_MOONS
from engine.aging import stage_for_age
from engine.blooding import is_unblooded_juvenile
from engine.cooldowns import (
    DROWN_SICK_ROLE,
    _used_today,
    can_hunt_again,
    daily_stipend_status,
)
from engine.role_features import is_rogue_wolf
from engine.role_privileges import is_full_forager, is_scout


def _field(user, key: str, default=None):
    if hasattr(user, "keys") and key in user.keys():
        return user[key]
    if isinstance(user, dict):
        return user.get(key, default)
    return default


def _has_text(user, key: str) -> bool:
    val = _field(user, key)
    return bool(val and str(val).strip())


def _has_proxy(user) -> bool:
    prefix = _field(user, "proxy_prefix")
    suffix = _field(user, "proxy_suffix")
    return bool((prefix and str(prefix).strip()) or (suffix and str(suffix).strip()))


def _col_int(user, key: str, default: int = 0) -> int:
    return int(_field(user, key, default) or default)


def _can_forage_again(user, day: int) -> bool:
    if is_full_forager(user):
        return True
    return _col_int(user, "last_forage_day") < day


def _can_explore_again(user, day: int) -> bool:
    if is_scout(user):
        return True
    return _col_int(user, "last_explore_day") < day


def _pending_setup_items(user) -> list[str]:
    items: list[str] = []

    if not _has_proxy(user):
        items.append("set proxy tag (`/proxy set`)")
    if not _has_text(user, "ic_location"):
        items.append("set ic location (`/location set`)")

    age = int(_field(user, "age_months", 24) or 24)
    stage = stage_for_age(age)
    wolf_id = int(_field(user, "id", 0) or 0)

    if stage == "pup":
        if age < PUP_MAX_MOONS:
            items.append("reach juvenile age (6 moons)")
        return items

    if int(_field(user, "last_hunt_day", 0) or 0) <= 0:
        items.append("first hunt (`/bones action:hunt`)")

    if stage == "juvenile" and age < JUVENILE_MAX_MOONS:
        if is_unblooded_juvenile(user):
            items.append("earn blooding on a hunt kill")
        elif _field(user, "has_blooding") and wolf_id:
            keys = db.get_wolf_journal_event_keys(wolf_id)
            if not any(k.startswith("rite_blooding") for k in keys):
                items.append("hold blooding rite (`/rite blooding`)")

    return items


def _pending_daily_items(
    user,
    day: int,
    *,
    guild_id: int | None = None,
    season: str = "spring",
    prestige_tier: int = 0,
    is_booster: bool = False,
    donor_bonus: int = 0,
) -> list[str]:
    if day <= 0:
        return []

    items: list[str] = []
    age = int(_field(user, "age_months", 24) or 24)
    stage = stage_for_age(age)
    pack_id = _field(user, "pack_id")

    if pack_id and not is_rogue_wolf(user):
        daily_status, _note = daily_stipend_status(
            user, day, prestige_tier, is_booster=is_booster, donor_bonus=donor_bonus
        )
        if daily_status == "ready":
            items.append("collect den stipend (`/bones action:daily`)")

    if stage == "pup":
        if not _used_today(user, day, "last_play_day"):
            items.append("play in the den (`/playpen action:play`)")
        return items

    if can_hunt_again(user, day):
        items.append("hunt (`/bones action:hunt`)")
    if not _used_today(user, day, "last_work_day"):
        items.append("den work (`/bones action:work`)")

    if is_rogue_wolf(user):
        if not _used_today(user, day, "last_scavenge_day"):
            items.append("scavenge (`/field action:scavenge`)")
    elif not pack_id and not _used_today(user, day, "last_scavenge_day"):
        items.append("scavenge (`/field action:scavenge`)")

    if _can_forage_again(user, day):
        items.append("forage (`/field action:forage`)")

    if _can_explore_again(user, day):
        items.append("explore (`/explore venture`)")

    if not _used_today(user, day, "last_sniff_day"):
        items.append("sniff the wind (`/field action:sniff`)")

    if pack_id:
        if not _used_today(user, day, "last_howl_day"):
            items.append("pack howl (`/howl`)")
        if not _used_today(user, day, "last_socialize_day"):
            items.append("socialize (`/playpen action:socialize`)")

    if stage != "pup" and not _used_today(user, day, "last_role_event_day"):
        items.append("role event (`/role action:event`)")

    from engine.conditions import manual_long_rest_used_today

    if not manual_long_rest_used_today(user, day):
        items.append("long rest (`/vitals action:rest type:long`)")

    if is_scout(user):
        if not _used_today(user, day, "last_survey_day"):
            items.append("scout survey (`/scout action:survey`)")
        if not _used_today(user, day, "last_trail_day"):
            items.append("mark a trail (`/scout action:trail`)")

    role = _field(user, "wolf_role", "hunter")
    if role == DROWN_SICK_ROLE and not _used_today(user, day, "last_prophecy_day"):
        items.append("prophecy (`/role action:prophecy`)")

    from engine.role_features import is_full_medic
    from engine.sacred_visits import sacred_visit_due

    if is_full_medic(user):
        if sacred_visit_due(user, day):
            items.append("sacred visit (`/medic action:sacred`)")
        if int(_field(user, "last_medic_rounds_day", 0) or 0) < day:
            items.append("den checkup (`/medic action:checkup`)")

    if pack_id and guild_id and not is_rogue_wolf(user):
        from engine.herb_growing import evaluate_growth

        plantings = db.get_pack_herb_plantings(pack_id)
        if plantings:
            if not db.pack_garden_tended_today(pack_id, day):
                items.append("tend garden (`/garden tend`)")
            ready = False
            for planting in plantings:
                result, _updates = evaluate_growth(
                    herb_key=planting["herb_key"],
                    planted_day=int(planting["planted_day"]),
                    last_tended_day=int(planting["last_tended_day"]),
                    last_eval_day=int(planting["last_eval_day"]),
                    health=int(planting["health"]),
                    season=season,
                    current_day=day,
                )
                if result.ready:
                    ready = True
                    break
            if ready:
                items.append("harvest garden (`/garden harvest`)")

        from config import CAT_PACT_RECEIVE_MIN_TRUST, WOLF_PACT_RECEIVE_MIN_STANDING

        if not _used_today(user, day, "last_cat_receive_day"):
            for pact in db.list_active_cat_pacts(guild_id, pack_id):
                if int(pact["trust"]) >= CAT_PACT_RECEIVE_MIN_TRUST:
                    items.append("receive clan goods (`/pact action:receive`)")
                    break
        if not _used_today(user, day, "last_wolf_receive_day"):
            for treaty in db.list_active_wolf_treaties(guild_id, pack_id):
                standing = db.get_pack_relation(
                    guild_id, pack_id, int(treaty["other_pack_id"])
                )
                if standing >= WOLF_PACT_RECEIVE_MIN_STANDING:
                    items.append("receive wolf-pack goods (`/pact action:receive`)")
                    break
        if not _used_today(user, day, "last_duplicate_trade_day"):
            if db.list_active_cat_pacts(guild_id, pack_id) or db.list_active_wolf_treaties(
                guild_id, pack_id
            ):
                items.append("trade duplicates (`/pact action:trade`)")
        if db.list_active_cat_pacts(guild_id, pack_id) or db.list_active_wolf_treaties(
            guild_id, pack_id
        ):
            items.append("review treaties (`/pact action:view`)")

        from engine.pack_amusement_store import count_depositable_amusement
        from engine.pack_herb_store import count_depositable_inventory_herbs

        if count_depositable_inventory_herbs(user) > 0:
            items.append("deposit herbs to den store (`/herbs action:store mode:depositall`)")
        if count_depositable_amusement(user) > 0:
            items.append("deposit toys to den store (`/playpen action:toystore mode:depositall`)")

    return items


def _pending_watch_items(user, guild_id: int | None, day: int) -> list[str]:
    pack_id = _field(user, "pack_id")
    if not guild_id or not pack_id or day <= 0:
        return []
    from engine.pack_relations import HOSTILE_STANDING_THRESHOLD

    items: list[str] = []
    for row in db.list_pack_relations(guild_id, pack_id):
        if int(row["standing"]) <= HOSTILE_STANDING_THRESHOLD:
            items.append(
                f"border watch — hostile with **{row['other_pack_name']}** "
                f"({row['standing']}/10); sniff/survey risk up."
            )
    alert = db.get_active_raid_alert_for_victim(guild_id, pack_id, day)
    if alert:
        suspect = db.get_pack(int(alert["suspect_pack_id"]))
        sname = suspect["name"] if suspect else "a rival"
        items.append(
            f"treasury raid alert — **`/pack audit`** or **`/pack accuse`** (suspect: {sname})."
        )
    return items


def collect_wolf_checklist(
    user,
    *,
    day: int = 0,
    guild_id: int | None = None,
    season: str = "spring",
    prestige_tier: int = 0,
    is_booster: bool = False,
    donor_bonus: int = 0,
) -> tuple[list[str], list[str], list[str]]:
    """Return (setup todos, daily todos, watch todos); only incomplete items."""
    setup = _pending_setup_items(user)
    today = _pending_daily_items(
        user,
        day,
        guild_id=guild_id,
        season=season,
        prestige_tier=prestige_tier,
        is_booster=is_booster,
        donor_bonus=donor_bonus,
    )
    watch = _pending_watch_items(user, guild_id, day)
    return setup, today, watch


def format_wolf_checklist(setup: list[str], today: list[str], watch: list[str] | None = None) -> str | None:
    """markdown checklist with ☐ boxes; none when nothing pending."""
    watch = watch or []
    if not setup and not today and not watch:
        return None
    parts: list[str] = []
    if setup:
        parts.append("**setup**\n" + "\n".join(f"☐ {label}" for label in setup))
    if today:
        parts.append("**today**\n" + "\n".join(f"☐ {label}" for label in today))
    if watch:
        parts.append("**watch**\n" + "\n".join(f"☐ {label}" for label in watch))
    text = "\n\n".join(parts)
    if len(text) > 4000:
        text = text[:3997] + "…"
    return text


def build_wolf_checklist(
    user,
    *,
    day: int = 0,
    guild_id: int | None = None,
    season: str | None = None,
    prestige_tier: int = 0,
    is_booster: bool = False,
    donor_bonus: int = 0,
) -> str | None:
    if season is None and guild_id:
        world = db.get_world(guild_id)
        season = world["season"] if world else "spring"
    season = season or "spring"
    setup, today, watch = collect_wolf_checklist(
        user,
        day=day,
        guild_id=guild_id,
        season=season,
        prestige_tier=prestige_tier,
        is_booster=is_booster,
        donor_bonus=donor_bonus,
    )
    return format_wolf_checklist(setup, today, watch)
