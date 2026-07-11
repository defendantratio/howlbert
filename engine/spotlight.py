"""Wolf of the week; picks a noteworthy wolf from recent journal activity for
a den announcement (also postable as social content — see
docs/GROWTH_IDEAS.md section 40)."""

from __future__ import annotations

import database as db

# how interesting each journal event type is, for picking "the" moment of the
# week; higher wins. events not listed here don't count toward the pick.
_EVENT_WEIGHT = {
    "achievement": 100,
    "pack_joined": 80,  # covers founding a pack too; see engine/wolf_journal.log_pack_change
    "rivalry_milestone": 70,
    "raid_success": 60,
    "quest_complete": 50,
    "died": 45,
    "blooded": 40,
    "born": 30,
    "bonded": 25,
    "trained": 20,
}

SPOTLIGHT_WINDOW_DAYS = 7


def pick_wolf_of_the_week(guild_id: int, current_day: int) -> dict | None:
    """Returns {wolf_id, wolf_name, event_key, summary, day} for the most
    noteworthy journal entry in the last SPOTLIGHT_WINDOW_DAYS, or None if
    nothing weighted happened this window."""
    since_day = max(0, current_day - SPOTLIGHT_WINDOW_DAYS)
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT j.wolf_id, j.event_key, j.summary, j.day, u.wolf_name
            FROM wolf_journal_entries j
            JOIN users u ON u.id = j.wolf_id
            WHERE j.guild_id = ? AND j.day IS NOT NULL AND j.day >= ?
            """,
            (guild_id, since_day),
        ).fetchall()

    best = None
    best_score = -1
    for row in rows:
        score = _EVENT_WEIGHT.get(str(row["event_key"]), 0)
        if score > best_score:
            best_score = score
            best = row
    if not best or best_score <= 0:
        return None
    return {
        "wolf_id": int(best["wolf_id"]),
        "wolf_name": best["wolf_name"],
        "event_key": best["event_key"],
        "summary": best["summary"],
        "day": best["day"],
    }


def format_spotlight_post(pick: dict) -> str:
    return (
        f"**wolf of the week: {pick['wolf_name']}**\n"
        f"{pick['summary']}\n\n"
        f"_a highlight from the last {SPOTLIGHT_WINDOW_DAYS} sunrises; check `/journal` for the full story._"
    )
