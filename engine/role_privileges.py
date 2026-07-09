"""Role-based activity privileges (hunter, forager, medic)."""

from __future__ import annotations

from config import HUNTER_HUNTS_PER_SUNRISE
from engine.role_features import has_any_role, is_full_medic

HUNTER_ROLE = "hunter"
FORAGER_ROLE = "forager"
MEDIC_ROLE = "medic"
SCOUT_ROLE = "scout"
GUARD_ROLE = "guard"

HERB_HEAL_DAILY_LIMIT = 3
HERB_TREAT_DAILY_LIMIT = 3


def wolf_role_key(user) -> str:
    if not user:
        return HUNTER_ROLE
    return user["wolf_role"] if "wolf_role" in user.keys() else HUNTER_ROLE


def is_hunter(user) -> bool:
    return has_any_role(user, HUNTER_ROLE, "hunter_apprentice")


def hunts_used_today(user, day: int) -> int:
    if not user:
        return 0
    last_uses_day = int(user["last_hunt_uses_day"]) if "last_hunt_uses_day" in user.keys() else 0
    if last_uses_day < day:
        return 0
    return int(user["hunt_uses_today"]) if "hunt_uses_today" in user.keys() else 0


def hunts_remaining_today(user, day: int) -> int:
    if not user:
        return 0
    if not is_hunter(user):
        last = int(user["last_hunt_day"]) if "last_hunt_day" in user.keys() else 0
        return 1 if last < day else 0
    return max(0, HUNTER_HUNTS_PER_SUNRISE - hunts_used_today(user, day))


def hunts_left_footer(user, day: int, *, role_prefix: bool = True) -> str:
    """Footer fragment for the hunt allotment. Hunting is never hard-capped; past
    the allotment it just yields less, so the wording never implies a block."""
    left = hunts_remaining_today(user, day)
    if left <= 0:
        core = "past your daily hunts; more still work but yield less"
    else:
        noun = "hunt" if left == 1 else "hunts"
        core = f"{left} full-yield {noun} left this sunrise (more still work, at less)"
    if role_prefix and is_hunter(user):
        return f"hunter: {core}"
    return core


def record_hunt_use(discord_id: int, *, wolf_id: int, day: int) -> None:
    import database as db

    user = db.get_user(discord_id)
    uses = hunts_used_today(user, day) + 1
    db.update_user(
        discord_id,
        wolf_id=wolf_id,
        last_hunt_day=day,
        last_hunt_uses_day=day,
        hunt_uses_today=uses,
    )


def is_forager(user) -> bool:
    return has_any_role(user, FORAGER_ROLE, "forager_apprentice")


def is_full_forager(user) -> bool:
    return has_any_role(user, FORAGER_ROLE)


def is_medic(user) -> bool:
    return is_full_medic(user)


def is_scout(user) -> bool:
    return has_any_role(user, SCOUT_ROLE, "scout_apprentice")


def is_guard(user) -> bool:
    return has_any_role(user, GUARD_ROLE)


def rescout_uses_today(user, day: int) -> int:
    if not is_scout(user):
        return 0
    if int(user["last_rescout_day"]) < day:
        return 0
    return int(user["rescout_uses_today"]) if "rescout_uses_today" in user.keys() else 0


def rescout_uses_remaining(user, day: int) -> int:
    from config import SCOUT_RESCOUTS_PER_DAY

    if not is_scout(user):
        return 0
    return max(0, SCOUT_RESCOUTS_PER_DAY - rescout_uses_today(user, day))


def can_rescout_again(user, day: int) -> bool:
    """Scouts may rescout without a daily cap."""
    if is_scout(user):
        return True
    return rescout_uses_remaining(user, day) > 0


def can_hunt_again(user, day: int) -> bool:
    """hunters get hunter_hunts_per_sunrise per sunrise; others once."""
    if is_hunter(user):
        return hunts_used_today(user, day) < HUNTER_HUNTS_PER_SUNRISE
    return int(user["last_hunt_day"]) < day


def forage_check_params(user, profs) -> tuple[tuple[str, str], str, str, bool]:
    """Territory forage roll: trained gatherers use Herblore; others use Survival."""
    prof_set = set(profs) if profs is not None else set()
    if is_forager(user) or "herblore" in prof_set:
        return (
            ("attr_int", "attr_wis"),
            "herblore",
            "herblore",
            is_forager(user) or "herblore" in prof_set,
        )
    return (
        ("attr_con", "attr_str"),
        "survival",
        "survival",
        "survival" in prof_set,
    )


def forage_sunrise_footer(user, *, success_hint: bool = False) -> str:
    """Footer after a territory forage attempt (full foragers may go again)."""
    if is_full_forager(user):
        base = "Forager · forage again this sunrise · fatigue still applies"
        if success_hint:
            return f"in `/bones action:inventory` · `/medic action:treat herb:herb_arnica` · {base}"
        return base
    if is_forager(user):
        base = "forager apprentice · forage again this sunrise; dc climbs each repeat"
        if success_hint:
            return f"in `/bones action:inventory` · `/medic action:treat herb:herb_arnica` · {base}"
        return base
    if success_hint:
        return (
            "in `/bones action:inventory` · `/medic action:treat herb:herb_arnica` · "
            "forage again this sunrise; dc climbs each repeat"
        )
    return "forage again this sunrise; dc climbs each repeat."


def herb_heal_limit_reached(user) -> bool:
    """short-rest comfrey healing; medics (green tongue) have no cap."""
    if is_medic(user):
        return False
    return int(user["herb_heals_today"]) >= HERB_HEAL_DAILY_LIMIT


def treat_limit_reached(user) -> bool:
    """medics may `/medic action:treat` without the daily herb cap; apprentices and others are capped."""
    if is_medic(user):
        return False
    return int(user["herb_treats_today"] if "herb_treats_today" in user.keys() else 0) >= HERB_TREAT_DAILY_LIMIT


def activity_cooldown_label(user, activity: str, *, ready: bool, day: int = 0) -> str:
    """Human label for /cooldowns; hunters and foragers show role perks."""
    if activity == "hunt":
        left = hunts_remaining_today(user, day)
        if left > 0:
            cap = HUNTER_HUNTS_PER_SUNRISE if is_hunter(user) else 1
            return f"ready ({left}/{cap} left)"
        return "used"
    if activity == "forage" and is_full_forager(user):
        return "unlimited (forager)"
    if activity == "explore" and is_scout(user):
        return "unlimited (scout)"
    if activity == "rescout" and is_scout(user):
        return "unlimited (scout)"
    if activity == "treat" and is_medic(user):
        return "unlimited (medic)"
    if activity == "stabilize" and is_medic(user):
        return "unlimited (medic)"
    if activity == "surgery" and is_medic(user):
        return "ready (medic)" if ready else "used this sunrise"
    return "ready" if ready else "used"
