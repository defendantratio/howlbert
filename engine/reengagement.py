"""Finds players who've gone quiet in-game, for the manual "your wolf misses
you" re-engagement check-in (docs/GROWTH_IDEAS.md section 18) — the existing
counterpart to the 48-hour lurker dm, for players who already joined and
played, then faded out."""

from __future__ import annotations

import database as db

# same activity columns exhaustion_effects.py uses to decide who's "away";
# reused here so both features agree on what "active" means.
_ACTIVITY_COLUMNS = (
    "last_hunt_day", "last_work_day", "last_socialize_day", "last_explore_day",
    "last_forage_day", "last_groom_day", "last_sniff_day", "last_fishing_day",
    "last_howl_day", "last_sign_day",
)

DEFAULT_QUIET_THRESHOLD_DAYS = 5


def find_quiet_wolves(current_day: int, *, threshold_days: int = DEFAULT_QUIET_THRESHOLD_DAYS) -> list[dict]:
    """Registered, living, non-dormant wolves with no tracked activity in the
    last ``threshold_days`` sunrises. Howlbert's `users` table is a single
    global roster (no per-guild scoping), matching how the rest of the bot
    already treats wolves — see engine/exhaustion_effects.py's identical
    "away" pattern for the same reason."""
    last_seen_expr = "MAX(" + ", ".join(f"COALESCE({c}, 0)" for c in _ACTIVITY_COLUMNS) + ")"
    cutoff = max(0, current_day - threshold_days)
    with db.get_db() as conn:
        rows = conn.execute(
            f"""
            SELECT id, discord_id, wolf_name, last_seen FROM (
                SELECT id, discord_id, wolf_name, {last_seen_expr} AS last_seen
                FROM users
                WHERE condition NOT IN ('dead', 'dying')
                  AND dormant = 0
            )
            WHERE last_seen < ?
            ORDER BY last_seen ASC
            """,
            (cutoff,),
        ).fetchall()
    return [
        {
            "wolf_id": int(r["id"]),
            "discord_id": int(r["discord_id"]),
            "wolf_name": r["wolf_name"],
            "days_quiet": current_day - int(r["last_seen"]),
        }
        for r in rows
    ]
