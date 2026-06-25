"""Thirst; separate from hunger; creek drinks and prey moisture restore it."""

from __future__ import annotations

from config import (
    DRINK_COOLDOWN_MINUTES,
    DRINK_HP_RESTORE,
    DRINK_HUNGER_RESTORE,
    DRINK_MOOD_RESTORE,
    DRINK_THIRST_RESTORE,
    NEEDS_EXHAUSTION_GAIN,
    THIRST_CRITICAL_THRESHOLD,
    THIRST_HUNT_PENALTY_PCT,
    THIRST_LOW_THRESHOLD,
    THIRST_MAX,
    THIRST_ROLLOVER_DECAY,
)
from engine.time_cooldowns import cooldown_minutes_remaining

HUNT_ACTIVITIES = frozenset({"hunt", "scavenge", "track", "fishing"})

_PREY_THIRST: dict[str, int] = {
    "fish": 22,
    "vole": 6,
    "hare": 8,
    "rabbit": 8,
    "grouse": 7,
    "agouti": 7,
    "beaver": 10,
    "deer": 12,
    "elk": 14,
    "carrion": 3,
}


def user_thirst(user) -> int:
    if "thirst" not in user.keys():
        return 80
    return int(user["thirst"])


def drink_cooldown_minutes(user) -> int:
    last_at = user["last_drink_at"] if "last_drink_at" in user.keys() else ""
    return cooldown_minutes_remaining(last_at or None, DRINK_COOLDOWN_MINUTES)


def thirst_activity_block(user) -> str | None:
    thirst = user_thirst(user)
    if thirst < THIRST_CRITICAL_THRESHOLD:
        return (
            f"You're parched (**{thirst}/{THIRST_MAX}**); `/drink` at the creek, eat moist prey, "
            "or ask your **Alpha** for `/packlife action:drinkall` before ranging out."
        )
    return None


def apply_thirst_bone_penalty(amount: int, thirst: int) -> tuple[int, str]:
    if amount <= 0 or thirst >= THIRST_LOW_THRESHOLD:
        return amount, ""
    reduced = max(0, int(amount * (100 - THIRST_HUNT_PENALTY_PCT) / 100))
    note = f"Low thirst ({thirst}); **−{THIRST_HUNT_PENALTY_PCT}%** bone payout."
    return reduced, note


def meal_thirst_gain(prey_key: str, uses_consumed: int = 1) -> int:
    per_use = _PREY_THIRST.get(prey_key, 8)
    return min(THIRST_MAX, per_use * uses_consumed)


def format_thirst_line(user) -> str:
    thirst = user_thirst(user)
    if thirst <= 0:
        note = "; **dying**; roll **`/medic action:deathsaves`** or get **`/medic action:stabilize`**."
    elif thirst <= THIRST_ROLLOVER_DECAY:
        note = "; will **collapse** at next sunrise without water."
    elif thirst < THIRST_CRITICAL_THRESHOLD:
        note = "; parched; strenuous activity blocked until you drink."
    elif thirst < THIRST_LOW_THRESHOLD:
        note = (
            f"; low; hunt payouts **−{THIRST_HUNT_PENALTY_PCT}%**, "
            f"**+{NEEDS_EXHAUSTION_GAIN} exhaustion** each sunrise until you drink."
        )
    else:
        note = ""
    return f"**{thirst}/{THIRST_MAX}**{note}"


def drink_at_creek(user, *, day: int, season: str, guild_id: int | None = None) -> tuple[bool, str]:
    """Creek drink; once per hour (real time), unlimited over a long day."""
    from engine.vitals import living_wolf_block

    import database as db

    block = living_wolf_block(user)
    if block:
        return False, block

    wait = drink_cooldown_minutes(user)
    if wait > 0:
        return False, f"The creek is right there; give it **{wait}** min before you lap again."

    db.update_user(
        user["discord_id"],
        last_drink_at=db.utcnow(),
        last_drink_day=day,
        wolf_id=user["id"],
    )
    from engine.plot_blinking import plot_drink_thirst_bonus

    gp = user["great_pack"] if "great_pack" in user.keys() else None
    thirst_restore = DRINK_THIRST_RESTORE
    plot_line = ""
    if guild_id is not None:
        bonus, plot_line = plot_drink_thirst_bonus(guild_id, gp)
        thirst_restore = max(1, thirst_restore + bonus)
    thirst = db.adjust_thirst(user["id"], thirst_restore)
    hunger = db.adjust_hunger(user["id"], DRINK_HUNGER_RESTORE)
    hp_gain = min(user["max_hp"] - user["hp"], DRINK_HP_RESTORE)
    if hp_gain > 0:
        db.set_user_conditions(user["discord_id"], wolf_id=user["id"], hp=user["hp"] + hp_gain)
    mood = db.adjust_mood(user["id"], DRINK_MOOD_RESTORE)

    msg = (
        f"Cold water from the **{season}** creek; thirst **{thirst}** (+{thirst_restore}), "
        f"hunger **{hunger}** (+{DRINK_HUNGER_RESTORE}), mood **{mood}** (+{DRINK_MOOD_RESTORE})"
    )
    if plot_line:
        msg += f"\n_{plot_line}_"
    if guild_id is not None:
        from engine.plot_blinking import try_plot_witness

        msg += try_plot_witness(user, guild_id, day, action="drink")
    if hp_gain:
        msg += f", **+{hp_gain} HP**"
    msg += f". _(Next drink in {DRINK_COOLDOWN_MINUTES} min.)_"
    return True, msg


def run_drinkall(
    pack_id: int,
    day: int,
    *,
    caller=None,
    discord_admin: bool = False,
) -> tuple[bool, str, int]:
    """Alpha leads the den to the creek; thirst restore for all packmates once per sunrise."""
    import database as db

    from engine.pack_leadership import PACK_BULK_ALPHA_ONLY_MSG, can_run_pack_bulk_action
    from engine.vitals import living_wolf_block

    pack = db.get_pack(pack_id)
    if not pack:
        return False, "Pack not found.", 0
    if caller and not can_run_pack_bulk_action(caller, pack, discord_admin=discord_admin):
        return False, PACK_BULK_ALPHA_ONLY_MSG, 0
    if int(pack["last_drinkall_day"]) >= day:
        return False, "The den already drank together at the creek this sunrise.", 0

    members = db.get_pack_den_wolves(pack_id)
    if not members:
        return False, "No wolves in the den.", 0

    drank = 0
    lines: list[str] = []
    for wolf in members:
        block = living_wolf_block(wolf)
        if block:
            lines.append(f"**{wolf['wolf_name']}**; {block}")
            continue
        thirst = db.adjust_thirst(wolf["id"], DRINK_THIRST_RESTORE)
        lines.append(f"**{wolf['wolf_name']}** → thirst **{thirst}** (+{DRINK_THIRST_RESTORE})")
        drank += 1

    if drank == 0:
        return False, "No packmate could drink at the creek.", 0

    db.set_pack_drinkall_day(pack_id, day)
    summary = "\n".join(lines[:12])
    if len(lines) > 12:
        summary += f"\n_…and {len(lines) - 12} more._"
    msg = (
        f"**Communal drink** at the creek; **{drank}** wolf(s) lapped up.\n{summary}"
    )
    return True, msg, drank
