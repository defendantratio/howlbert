"""Wolvden-style mood; morale affects hunting and activities."""

from __future__ import annotations

from config import (
    MOOD_CRITICAL_THRESHOLD,
    MOOD_HUNT_PENALTY_PCT,
    MOOD_LOW_THRESHOLD,
    MOOD_MAX,
)

HUNT_ACTIVITIES = frozenset({"hunt", "scavenge", "track", "fishing"})


def user_mood(user) -> int:
    if "mood" not in user.keys():
        return 75
    return int(user["mood"])


def mood_activity_block(user) -> str | None:
    """Block gathering activities when morale is critically low."""
    mood = user_mood(user)
    if mood < MOOD_CRITICAL_THRESHOLD:
        return (
            f"Your mood is too low (**{mood}/{MOOD_MAX}**); you can't face the wild today. "
            "Rest, `/playpen`, or `/playpen action:socialize` to lift your spirits."
        )
    return None


def apply_mood_bone_penalty(amount: int, mood: int) -> tuple[int, str]:
    if amount <= 0 or mood >= MOOD_LOW_THRESHOLD:
        return amount, ""
    reduced = max(0, int(amount * (100 - MOOD_HUNT_PENALTY_PCT) / 100))
    note = f"Low mood ({mood}); **−{MOOD_HUNT_PENALTY_PCT}%** bone payout."
    return reduced, note


def format_mood_line(user) -> str:
    mood = user_mood(user)
    if mood < MOOD_CRITICAL_THRESHOLD:
        note = "; critically low; strenuous activity blocked until you recover."
    elif mood < MOOD_LOW_THRESHOLD:
        note = (
            f"; low; hunt payouts **−{MOOD_HUNT_PENALTY_PCT}%**, "
            f"**+1 exhaustion** each sunrise until you recover."
        )
    else:
        note = ""
    return f"**{mood}/{MOOD_MAX}**{note}"
