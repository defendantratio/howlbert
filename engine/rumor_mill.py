"""
Delayed scandal reveal. Caught secrets don't land on the den the instant
they happen — they spread over a few sunrises, the way real gossip does —
so there's a window where the truth is still just a rumor, not a verdict.
"""

from __future__ import annotations

import database as db

RUMOR_REVEAL_DELAY_DAYS = 2


def queue_rumor(
    *,
    guild_id: int,
    wolf_a_id: int,
    wolf_b_id: int | None,
    kind: str,
    standing_delta: int,
    flavor_text: str,
    queued_day: int,
    delay_days: int = RUMOR_REVEAL_DELAY_DAYS,
) -> None:
    db.queue_pending_rumor(
        guild_id=guild_id,
        wolf_a_id=wolf_a_id,
        wolf_b_id=wolf_b_id,
        kind=kind,
        standing_delta=standing_delta,
        flavor_text=flavor_text,
        queued_day=queued_day,
        reveal_day=queued_day + delay_days,
    )


def reveal_due_rumors(guild_id: int, day: int) -> list[str]:
    """Apply standing penalties and return den-news lines for rumors whose reveal day has arrived."""
    due = db.get_due_rumors(guild_id, day)
    lines: list[str] = []
    for rumor in due:
        if rumor["standing_delta"]:
            db.adjust_wolf_standing_by_id(int(rumor["wolf_a_id"]), int(rumor["standing_delta"]))
            if rumor["wolf_b_id"]:
                db.adjust_wolf_standing_by_id(int(rumor["wolf_b_id"]), int(rumor["standing_delta"]))
        lines.append(rumor["flavor_text"])
        db.mark_rumor_revealed(int(rumor["id"]))
    return lines
