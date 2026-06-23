"""Real-time cooldown helpers (hourly creek drinks, ambush spacing)."""

from __future__ import annotations

from datetime import datetime, timezone


def minutes_since_iso(iso_ts: str | None) -> float | None:
    if not iso_ts:
        return None
    then = datetime.fromisoformat(iso_ts)
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - then).total_seconds() / 60


def cooldown_minutes_remaining(iso_ts: str | None, cooldown_minutes: int) -> int:
    """Minutes until ready; 0 means ready now."""
    elapsed = minutes_since_iso(iso_ts)
    if elapsed is None:
        return 0
    return max(0, int(cooldown_minutes - elapsed + 0.999))
