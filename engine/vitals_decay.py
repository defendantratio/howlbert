"""Lazy intra-day hunger and hydration decay.

Hunger and hydration previously fell only at the sunrise rollover. This applies a
gentle, continuous drain the rest of the day: whenever a wolf checks vitals,
eats, or drinks, we look at how much real time has passed since the last decay
tick and subtract the proportional amount.

The tick timestamp advances only by the time actually "consumed" by whole
points removed, so fractional decay carries forward instead of being lost. A
per-call safety cap prevents a huge catch-up hit after a long absence (the
sunrise rollover already handles overnight depletion).
"""

from __future__ import annotations

import database as db
from engine.time_cooldowns import minutes_since_iso


def apply_time_decay(user) -> tuple[dict, str]:
    """Compute and persist intra-day hunger/thirst decay for ``user``.

    Returns (applied, note) where ``applied`` is {"hunger": pts, "thirst": pts}
    of points actually removed (may be empty) and ``note`` is a short
    player-facing string (or '').
    """
    from config import (
        HUNGER_HOURLY_DECAY,
        THIRST_HOURLY_DECAY,
        VITALS_INTRADAY_DECAY_CAP,
        HUNGER_MIN,
        THIRST_MIN,
    )

    if not user or (user["condition"] if "condition" in user.keys() else "healthy") in ("dead", "dying"):
        return {}, ""

    now = db.utcnow()
    last = user["vitals_decayed_at"] if "vitals_decayed_at" in user.keys() else ""
    if not last:
        # first sighting; start the clock, decay nothing
        db.update_user(user["discord_id"], wolf_id=user["id"], vitals_decayed_at=now)
        return {}, ""

    elapsed_min = minutes_since_iso(last)
    if elapsed_min is None or elapsed_min <= 0:
        return {}, ""
    hours = elapsed_min / 60.0

    hunger = int(user["hunger"]) if "hunger" in user.keys() else HUNGER_MIN
    thirst = int(user["thirst"]) if "thirst" in user.keys() else THIRST_MIN

    hunger_drop = min(int(hours * HUNGER_HOURLY_DECAY), VITALS_INTRADAY_DECAY_CAP)
    thirst_drop = min(int(hours * THIRST_HOURLY_DECAY), VITALS_INTRADAY_DECAY_CAP)
    hunger_drop = min(hunger_drop, max(0, hunger - HUNGER_MIN))
    thirst_drop = min(thirst_drop, max(0, thirst - THIRST_MIN))

    if hunger_drop <= 0 and thirst_drop <= 0:
        # not enough time passed for a whole point on either; leave the clock so
        # the fraction keeps accruing (unless capped-out at the floor)
        if hunger > HUNGER_MIN or thirst > THIRST_MIN:
            return {}, ""

    fields: dict = {"vitals_decayed_at": now}
    applied: dict = {}
    if hunger_drop > 0:
        fields["hunger"] = hunger - hunger_drop
        applied["hunger"] = hunger_drop
    if thirst_drop > 0:
        fields["thirst"] = thirst - thirst_drop
        applied["thirst"] = thirst_drop

    db.update_user(user["discord_id"], wolf_id=user["id"], **fields)

    if not applied:
        return {}, ""
    parts = []
    if applied.get("hunger"):
        parts.append(f"hunger -{applied['hunger']}")
    if applied.get("thirst"):
        parts.append(f"hydration -{applied['thirst']}")
    return applied, "the day wears on; " + ", ".join(parts) + "."
