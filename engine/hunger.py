"""Wolvden-style hunger; separate from mood; prey and rollover drive it."""

from __future__ import annotations

from config import (
    HUNGER_CRITICAL_THRESHOLD,
    HUNGER_HUNT_PENALTY_PCT,
    HUNGER_LOW_THRESHOLD,
    HUNGER_MAX,
    HUNGER_ROLLOVER_DECAY,
    NEEDS_EXHAUSTION_GAIN,
)

HUNT_ACTIVITIES = frozenset({"hunt", "scavenge", "track", "fishing"})


def user_hunger(user) -> int:
    if "hunger" not in user.keys():
        return 80
    return int(user["hunger"])


def hunger_activity_block(user) -> str | None:
    hunger = user_hunger(user)
    if hunger < HUNGER_CRITICAL_THRESHOLD:
        return (
            f"you're starving (**{hunger}/{HUNGER_MAX}**); eat from `/food` or ask your **alpha** for "
            "`/packlife action:feedall` before ranging out."
        )
    return None


def apply_hunger_bone_penalty(amount: int, hunger: int) -> tuple[int, str]:
    if amount <= 0 or hunger >= HUNGER_LOW_THRESHOLD:
        return amount, ""
    reduced = max(0, int(amount * (100 - HUNGER_HUNT_PENALTY_PCT) / 100))
    note = f"low hunger ({hunger}); −{HUNGER_HUNT_PENALTY_PCT}% bone payout."
    return reduced, note


def meal_hunger_gain(prey_key: str, uses_consumed: int = 1) -> int:
    from engine.prey_items import prey_meta

    meta = prey_meta(prey_key)
    per_use = meta.get("hunger", 18)
    return min(HUNGER_MAX, per_use * uses_consumed)


def format_hunger_line(user) -> str:
    hunger = user_hunger(user)
    if hunger <= 0:
        note = "; **dying**; roll **`/medic action:deathsaves`** or get **`/medic action:stabilize`**."
    elif hunger <= HUNGER_ROLLOVER_DECAY:
        note = "; will **collapse** at next sunrise without food."
    elif hunger < HUNGER_CRITICAL_THRESHOLD:
        note = "; starving; strenuous activity blocked until you eat."
    elif hunger < HUNGER_LOW_THRESHOLD:
        note = (
            f"; low; hunt payouts **−{HUNGER_HUNT_PENALTY_PCT}%**, "
            f"**+{NEEDS_EXHAUSTION_GAIN} exhaustion** each sunrise until fed."
        )
    else:
        note = ""
    return f"**{hunger}/{HUNGER_MAX}**{note}"
