"""Lunar phase tests; run: python -m tests.test_lunar"""

from __future__ import annotations

from datetime import datetime, timezone

from engine.lunar import (
    active_lunar_phase,
    assign_birth_lunar_phase,
    current_lunation_number,
    moon_phase_fraction,
    wolf_should_age_this_rollover,
)

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


class Row(dict):
    def keys(self):
        return super().keys()


def main() -> None:
    # Known new moon vicinity: 2000-01-06 UTC
    new_moon = datetime(2000, 1, 6, 12, 0, tzinfo=timezone.utc)
    check("new moon phase detected", active_lunar_phase(new_moon) == "new_moon")

    full_moon = datetime(2000, 1, 21, 12, 0, tzinfo=timezone.utc)
    check("full moon phase detected", active_lunar_phase(full_moon) == "full_moon")

    half = datetime(2000, 1, 13, 12, 0, tzinfo=timezone.utc)
    check("half moon phase detected", active_lunar_phase(half) == "half_moon")

    gibbous = datetime(2000, 1, 10, 12, 0, tzinfo=timezone.utc)
    check("gibbous has no age-up phase", active_lunar_phase(gibbous) is None)

    birth = assign_birth_lunar_phase(new_moon)
    check("assign birth near new", birth == "new_moon")

    user = Row(
        birth_lunar_phase="full_moon",
        last_lunar_aged_lunation=100,
    )
    check(
        "no age on wrong phase",
        not wolf_should_age_this_rollover(user, new_moon, lunar_birth_aging=True),
    )
    user_match = Row(
        birth_lunar_phase="new_moon",
        last_lunar_aged_lunation=current_lunation_number(new_moon) - 1,
    )
    check(
        "age on matching phase",
        wolf_should_age_this_rollover(user_match, new_moon, lunar_birth_aging=True),
    )
    check(
        "legacy always ages when lunar off",
        wolf_should_age_this_rollover(user, gibbous, lunar_birth_aging=False),
    )

    frac = moon_phase_fraction(new_moon)
    check("phase fraction near zero at new", frac < 0.05 or frac > 0.95)

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
