from datetime import datetime, timedelta, timezone


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def cooldown_remaining(last_action: str | None, cooldown_hours: float) -> timedelta | None:
    last = parse_timestamp(last_action)
    if last is None:
        return None

    ready_at = last + timedelta(hours=cooldown_hours)
    now = datetime.now(timezone.utc)
    if now >= ready_at:
        return None
    return ready_at - now


def format_timedelta(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"
