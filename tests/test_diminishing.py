"""Tests for the diminishing-returns engine (replaces once-per-sunrise blocks)."""

from __future__ import annotations

import json

from engine.diminishing import (
    multiplier_for_use,
    use_count_today,
    diminishing_note,
)


class Row(dict):
    def keys(self):
        return super().keys()


def test_multiplier_curve_is_first_full_then_decays():
    # first use of the sunrise is full value
    assert multiplier_for_use(1) == 1.0
    # repeats pay steadily less
    assert multiplier_for_use(2) < 1.0
    assert multiplier_for_use(3) < multiplier_for_use(2)
    # never zero: a repeat is worth something (agency), floored
    assert multiplier_for_use(99) > 0.0


def test_use_count_resets_across_days():
    user = Row(daily_use_log=json.dumps({"forage": [5, 3]}))
    # same day sees the recorded count
    assert use_count_today(user, "forage", 5) == 3
    # a new sunrise resets to zero
    assert use_count_today(user, "forage", 6) == 0
    # unknown activity is zero
    assert use_count_today(user, "hunt", 5) == 0


def test_empty_and_malformed_log_are_safe():
    assert use_count_today(Row(daily_use_log=""), "forage", 1) == 0
    assert use_count_today(Row(daily_use_log="not json"), "forage", 1) == 0
    assert use_count_today(Row(), "forage", 1) == 0


def test_diminishing_note_only_on_repeat():
    assert diminishing_note(1) == ""
    assert diminishing_note(2) != ""


_TESTS = [
    test_multiplier_curve_is_first_full_then_decays,
    test_use_count_resets_across_days,
    test_empty_and_malformed_log_are_safe,
    test_diminishing_note_only_on_repeat,
]


def main() -> None:
    passed = failed = 0
    for fn in _TESTS:
        try:
            fn()
            print(f"  OK  {fn.__name__}")
            passed += 1
        except Exception as exc:
            print(f" FAIL {fn.__name__} — {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
