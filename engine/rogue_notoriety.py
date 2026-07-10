"""Rogue notoriety: repeat border-raiders get hunted.

Each successful raid/crime raises a rogue's notoriety with the packs. High
notoriety cuts both ways:
  * packs hunt you: more frequent patrol ambushes and a higher chance of being
    caught mid-crime, and
  * packs fear you: at/above the fear threshold you fight and parley from a
    position of dread (advantage on intimidation).
Notoriety cools by a point each sunrise you lie low (no fresh crime).
"""

from __future__ import annotations

import database as db
from config import (
    ROGUE_NOTORIETY_AMBUSH_PER_POINT,
    ROGUE_NOTORIETY_DECAY_PER_SUNRISE,
    ROGUE_NOTORIETY_FEAR_THRESHOLD,
    ROGUE_NOTORIETY_MAX,
    ROGUE_NOTORIETY_PER_RAID,
)


def notoriety(user) -> int:
    if not user:
        return 0
    return int(user["rogue_notoriety"] if "rogue_notoriety" in user.keys() and user["rogue_notoriety"] is not None else 0)


def gain_notoriety(user, amount: int = ROGUE_NOTORIETY_PER_RAID) -> int:
    """Raise notoriety (capped). Returns the new value."""
    new = min(ROGUE_NOTORIETY_MAX, notoriety(user) + amount)
    db.update_user(user["discord_id"], wolf_id=user["id"], rogue_notoriety=new)
    return new


def notoriety_ambush_bonus(user) -> float:
    """Extra percentage points of patrol-ambush chance from being hunted."""
    return notoriety(user) * ROGUE_NOTORIETY_AMBUSH_PER_POINT * 100.0


def has_fear_reputation(user) -> bool:
    return notoriety(user) >= ROGUE_NOTORIETY_FEAR_THRESHOLD


def notoriety_note(user) -> str:
    n = notoriety(user)
    if n <= 0:
        return ""
    tail = "; packs **fear** you (intimidation edge), but hunt you harder" if has_fear_reputation(user) else "; packs are watching"
    return f"notoriety **{n}/{ROGUE_NOTORIETY_MAX}**{tail}"


def decay_notoriety_on_rollover(conn, day: int) -> None:
    """Notoriety cools for any rogue who didn't raid recently (lying low)."""
    conn.execute(
        "UPDATE users SET rogue_notoriety = MAX(0, rogue_notoriety - ?) "
        "WHERE rogue_notoriety > 0",
        (ROGUE_NOTORIETY_DECAY_PER_SUNRISE,),
    )
