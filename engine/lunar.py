"""Real-world lunar phases; birth moons and age-up timing."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger("howlbert")

_UTC_ALIASES = frozenset({"utc", "gmt", "etc/utc", "etc/gmt", "z"})

SYNODIC_MONTH = 29.530588853
# Julian date of a known new moon (2000-01-06 18:14 UTC)
KNOWN_NEW_MOON_JD = 2451549.5
PHASE_WINDOW = 1 / 16  # ~1.8 days each side of new/full/quarter


BIRTH_LUNAR_LABELS = {
    "new_moon": "new moon",
    "half_moon": "half moon",
    "full_moon": "full moon",
}


def _to_julian_day(dt: datetime) -> float:
    year = dt.year
    month = dt.month
    day = dt.day + (dt.hour + dt.minute / 60 + dt.second / 3600) / 24
    if month <= 2:
        year -= 1
        month += 12
    a = int(year / 100)
    b = 2 - a + int(a / 4)
    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5


def moon_phase_fraction(dt: datetime) -> float:
    """0 = new moon, 0.5 = full moon, in [0, 1)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    days = (_to_julian_day(dt) - KNOWN_NEW_MOON_JD) % SYNODIC_MONTH
    return days / SYNODIC_MONTH


def current_lunation_number(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    days = _to_julian_day(dt) - KNOWN_NEW_MOON_JD
    return int(days // SYNODIC_MONTH)


def _distance_on_circle(a: float, b: float) -> float:
    d = abs(a - b)
    return min(d, 1 - d)


def assign_birth_lunar_phase(dt: datetime) -> str:
    """nearest major birth phase for a wolf born at this moment."""
    frac = moon_phase_fraction(dt)
    anchors = {
        "new_moon": 0.0,
        "half_moon": 0.25,
        "full_moon": 0.5,
        "half_moon_alt": 0.75,
    }
    best = "new_moon"
    best_dist = 1.0
    for key, anchor in anchors.items():
        phase = "half_moon" if key == "half_moon_alt" else key
        dist = _distance_on_circle(frac, anchor)
        if dist < best_dist:
            best_dist = dist
            best = phase
    return best


def active_lunar_phase(dt: datetime) -> str | None:
    """
    major phase in the sky tonight, if within the age-up window.
    returns new_moon, half_moon, full_moon, or none (crescent/gibbous nights).
    """
    frac = moon_phase_fraction(dt)
    if frac < PHASE_WINDOW or frac > 1 - PHASE_WINDOW:
        return "new_moon"
    if abs(frac - 0.5) < PHASE_WINDOW:
        return "full_moon"
    if abs(frac - 0.25) < PHASE_WINDOW:
        return "half_moon"
    if abs(frac - 0.75) < PHASE_WINDOW:
        return "half_moon"
    return None


def lunar_phase_label(dt: datetime) -> str:
    """player-facing sky readout for /time."""
    active = active_lunar_phase(dt)
    if active:
        return BIRTH_LUNAR_LABELS[active]
    frac = moon_phase_fraction(dt)
    if frac < 0.5:
        return "waxing moon" if frac < 0.25 else "waxing gibbous"
    return "waning gibbous" if frac < 0.75 else "waning moon"


def wolf_should_age_this_rollover(
    user,
    dt: datetime,
    *,
    lunar_birth_aging: bool,
) -> bool:
    if not lunar_birth_aging:
        return True
    birth_phase = user["birth_lunar_phase"] if "birth_lunar_phase" in user.keys() else None
    if not birth_phase:
        return True
    sky = active_lunar_phase(dt)
    if sky is None or sky != birth_phase:
        return False
    lunation = current_lunation_number(dt)
    last = int(user["last_lunar_aged_lunation"]) if "last_lunar_aged_lunation" in user.keys() else -1
    return lunation > last


def resolve_timezone(name: str):
    """return a tzinfo for rollover scheduling (tzdata required on windows for non-utc zones)."""
    key = (name or "utc").strip()
    if not key or key.casefold() in _UTC_ALIASES:
        return timezone.utc
    try:
        return ZoneInfo(key)
    except ZoneInfoNotFoundError:
        logger.warning(
            "timezone %r not found; install tzdata (pip install tzdata) or use utc. falling back to utc.",
            key,
        )
        return timezone.utc


def rollover_now(timezone_name: str) -> datetime:
    return datetime.now(resolve_timezone(timezone_name))
