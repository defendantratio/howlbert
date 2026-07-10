"""Per-sunrise use counters and the energy piggyback for repeatable actions.

Historically this module also applied *diminishing returns*: each repeat of an
action in the same sunrise paid less (or climbed a dc). That soft throttle has
been fully retired in favour of a single, uniform throttle: **energy** (see
engine.energy). Every recorded use still spends energy, and specialists tire
slower at their signature craft, but payouts no longer shrink and there is no
per-sunrise cap beyond the deliberate long rest and the daily bones stipend.

The payout helpers below are kept as no-ops (returning full value) so existing
call sites keep working unchanged; ``record_use`` / ``use_count_today`` remain
live because they drive the energy spend and a couple of counters.

Counts live in the ``daily_use_log`` JSON column: {activity: [day, count]}.
"""

from __future__ import annotations

import json

import database as db


def _load(user) -> dict:
    raw = user["daily_use_log"] if "daily_use_log" in user.keys() else None
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def use_count_today(user, activity: str, day: int) -> int:
    """How many times ``activity`` has already run this sunrise (not counting now)."""
    entry = _load(user).get(activity)
    if not entry or int(entry[0]) != int(day):
        return 0
    return int(entry[1])


def multiplier_for_use(n: int, activity: str | None = None) -> float:
    """Deprecated no-op: payouts no longer diminish (energy is the throttle).
    Always returns full value; kept so old call sites need no change."""
    return 1.0


def _spend_activity_energy(user, activity: str) -> None:
    """Every recorded action also spends energy; energy is the game-wide throttle
    that replaced the old diminishing-returns/per-sunrise caps."""
    try:
        from engine.energy import spend_energy

        spend_energy(user, activity)
    except Exception:
        # energy is a soft layer; never let it break the underlying action.
        pass


def record_use(user, activity: str, day: int, *, spend_energy: bool = True) -> int:
    """Record one use of ``activity`` today; returns the new count (1-indexed).
    Also spends the activity's energy cost unless ``spend_energy`` is False."""
    log = _load(user)
    entry = log.get(activity)
    count = (int(entry[1]) + 1) if entry and int(entry[0]) == int(day) else 1
    log[activity] = [int(day), count]
    db.update_user(user["discord_id"], wolf_id=user["id"], daily_use_log=json.dumps(log))
    if spend_energy:
        _spend_activity_energy(user, activity)
    return count


def next_use_multiplier(user, activity: str, day: int) -> tuple[float, int]:
    """Record this use (spending energy) and return (1.0, use_count). The payout
    multiplier is always full now; energy is the sole throttle."""
    count = record_use(user, activity, day)
    return 1.0, count


def diminishing_note(count: int) -> str:
    """Deprecated no-op: repeats no longer pay less, so there is no note."""
    return ""
