"""Diminishing returns for repeatable actions.

Replaces hard "already did this this sunrise" blocks with soft diminishing
returns: a wolf may repeat an action as often as it likes, but each repeat in
the same sunrise pays less. Respects player agency while keeping spam from being
free. The only actions still hard-capped are the long rest (deliberate) and the
definitionally-daily bones stipend.

Usage per site:
    from engine.diminishing import next_use_multiplier
    mult, count = next_use_multiplier(user, "forage", day)   # records the use
    reward = max(1, int(base_reward * mult))                 # scale the payout
    note = diminishing_note(count)                            # optional flavor

Counts live in the ``daily_use_log`` JSON column: {activity: [day, count]}.
"""

from __future__ import annotations

import json

import database as db

# multiplier for the Nth use of an action in one sunrise (1st, 2nd, 3rd, ...)
# geometric-ish decay, floored so a repeat is never worthless (agency), never full
_MULTIPLIERS = (1.0, 0.6, 0.4, 0.25, 0.15)
_FLOOR = 0.1


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


def multiplier_for_use(n: int) -> float:
    """Payout multiplier for the (1-indexed) n-th use in a sunrise."""
    if n <= 0:
        return 1.0
    if n <= len(_MULTIPLIERS):
        return _MULTIPLIERS[n - 1]
    return _FLOOR


def record_use(user, activity: str, day: int) -> int:
    """Record one use of ``activity`` today; returns the new count (1-indexed)."""
    log = _load(user)
    entry = log.get(activity)
    count = (int(entry[1]) + 1) if entry and int(entry[0]) == int(day) else 1
    log[activity] = [int(day), count]
    db.update_user(user["discord_id"], wolf_id=user["id"], daily_use_log=json.dumps(log))
    return count


def next_use_multiplier(user, activity: str, day: int) -> tuple[float, int]:
    """Record this use and return (payout_multiplier, use_count). Use count is
    1 for the first use of the sunrise."""
    count = record_use(user, activity, day)
    return multiplier_for_use(count), count


def diminishing_note(count: int) -> str:
    """Player-facing note when a repeat pays less; empty for the first use."""
    if count <= 1:
        return ""
    return "you have already done this today; the tired repeat yields less."
