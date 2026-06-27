"""Live sky time helpers; run: python -m tests.test_world_time"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from engine.world import clock_time_of_day, conditions_snippet


def test_evening_is_dusk() -> None:
    evening = datetime(2026, 6, 26, 21, 36, tzinfo=ZoneInfo("America/New_York"))
    assert clock_time_of_day(evening) == "dusk"


def test_conditions_snippet_no_underscores() -> None:
    text = conditions_snippet("dusk", "clear")
    assert "_" not in text
    assert "half-light" in text.lower()
    assert "clear" in text.lower()
