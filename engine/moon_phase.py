"""Real lunar phase derived from the calendar date; a second ambient cycle
on top of real_world_season, with its own small mechanical hooks (no
flavor-only moon talk)."""

from __future__ import annotations

from datetime import datetime, timezone

SYNODIC_MONTH_DAYS = 29.530588853
# A known new moon (UTC) to anchor the cycle against.
_REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

PHASE_NAMES = (
    "new moon",
    "waxing crescent",
    "first quarter",
    "waxing gibbous",
    "full moon",
    "waning gibbous",
    "last quarter",
    "waning crescent",
)


def moon_phase(dt: datetime | None = None) -> str:
    """One of PHASE_NAMES for the given (or current UTC) date."""
    dt = dt or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    days = (dt - _REFERENCE_NEW_MOON).total_seconds() / 86400.0
    age = days % SYNODIC_MONTH_DAYS
    index = int((age / SYNODIC_MONTH_DAYS) * 8 + 0.5) % 8
    return PHASE_NAMES[index]


def is_full_moon(dt: datetime | None = None) -> bool:
    return moon_phase(dt) == "full moon"


def is_new_moon(dt: datetime | None = None) -> bool:
    return moon_phase(dt) == "new moon"


def full_moon_rally_unity_bonus() -> int:
    """Extra den unity on /sign rally and /howl under a full moon; the call carries further."""
    return 1 if is_full_moon() else 0


def new_moon_stealth_dc_mod() -> int:
    """DC reduction for sniff/scout-survey under a new moon; no moonlight to give you away."""
    return -2 if is_new_moon() else 0


def moon_flavor_note() -> str:
    phase = moon_phase()
    if phase == "full moon":
        return "full moon: howls and rallies carry further (+1 unity)."
    if phase == "new moon":
        return "new moon: no light to betray you (-2 dc on sniff/scout survey)."
    return ""
