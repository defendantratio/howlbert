"""Lone wolf loneliness; mood drain at rollover for packless wolves."""

from __future__ import annotations

import sqlite3

LONE_WOLF_MOOD_DRAIN = 3
LONE_WOLF_BONDED_DRAIN = 1
LONE_WOLF_SOCIAL_WINDOW_DAYS = 2


def apply_lone_wolf_loneliness_on_rollover(conn: sqlite3.Connection, day: int) -> list[dict]:
    """Drain mood for wolves with no pack. Wolves who socialized recently feel it less."""
    import database as _db

    rows = conn.execute(
        "SELECT id, discord_id, wolf_name, mood, last_socialize_day "
        f"FROM users WHERE pack_id IS NULL AND condition != 'dead' AND {_db.active_wolf_where(day)}"
    ).fetchall()
    notes: list[dict] = []
    for wolf in rows:
        socialized_recently = int(wolf["last_socialize_day"] or 0) >= day - LONE_WOLF_SOCIAL_WINDOW_DAYS
        drain = LONE_WOLF_BONDED_DRAIN if socialized_recently else LONE_WOLF_MOOD_DRAIN
        old_mood = int(wolf["mood"])
        new_mood = max(0, old_mood - drain)
        if new_mood == old_mood:
            continue
        conn.execute("UPDATE users SET mood = ? WHERE id = ?", (new_mood, wolf["id"]))
        notes.append({
            "wolf_name": wolf["wolf_name"],
            "discord_id": wolf["discord_id"],
            "line": f"lone wolf loneliness; mood **−{drain}** (now **{new_mood}**).",
        })
    return notes
