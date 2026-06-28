"""Auto-rollover catch-up after downtime; run: python -m tests.test_rollover_catchup"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import database as db
from config import ROLLOVER_HOUR, ROLLOVER_MINUTE, ROLLOVER_TIMEZONE
from engine.lunar import resolve_timezone
from engine.rollover_announce import (
    _rollover_moment,
    guild_due_for_rollover,
    missed_rollover_count,
    within_startup_den_news_dm_window,
)

TEST_GUILD = 1516980863911329803

_pass = 0
_fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  OK  {name}")
    else:
        _fail += 1
        print(f" FAIL {name}" + (f" - {detail}" if detail else ""))


def _set_last_rollover(when: datetime) -> None:
    with db.get_db() as conn:
        conn.execute(
            "UPDATE world_state SET last_rollover = ? WHERE guild_id = ?",
            (when.isoformat(), TEST_GUILD),
        )


def _ensure_world() -> None:
    db.get_world(TEST_GUILD)


def main() -> None:
    db.init_db()
    _ensure_world()
    tz = resolve_timezone(ROLLOVER_TIMEZONE)

    base_day = datetime(2026, 3, 10, ROLLOVER_HOUR, ROLLOVER_MINUTE, tzinfo=tz)
    after_first = base_day + timedelta(minutes=5)
    _set_last_rollover(after_first)

    same_day = base_day + timedelta(hours=2)
    check("not due same day after rollover", missed_rollover_count(TEST_GUILD, same_day) == 0)
    check("guild not due same day", not guild_due_for_rollover(TEST_GUILD, same_day))

    next_day = base_day + timedelta(days=1, hours=1)
    check("one missed after 1 day down", missed_rollover_count(TEST_GUILD, next_day) == 1)
    check("guild due after 1 day", guild_due_for_rollover(TEST_GUILD, next_day))

    three_days = base_day + timedelta(days=3, hours=1)
    check("three missed after 3 days down", missed_rollover_count(TEST_GUILD, three_days) == 3)

    before_today_roll = base_day + timedelta(days=1, minutes=-10)
    if ROLLOVER_MINUTE >= 10:
        check(
            "not due before today's rollover hour",
            missed_rollover_count(TEST_GUILD, before_today_roll) == 0,
        )

    old = datetime(2020, 1, 1, ROLLOVER_HOUR, ROLLOVER_MINUTE, tzinfo=tz)
    _set_last_rollover(old)
    due_moment = _rollover_moment(datetime(2026, 6, 22, tzinfo=tz).date(), tz)
    after_due = due_moment + timedelta(minutes=1)
    check("stale last counts missed sunrises", missed_rollover_count(TEST_GUILD, after_due) >= 1)

    in_window = after_due + timedelta(hours=2)
    check("startup DM window after rollover", within_startup_den_news_dm_window(in_window))
    before_roll = base_day - timedelta(minutes=30)
    check("startup DM window before rollover", not within_startup_den_news_dm_window(before_roll))

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
