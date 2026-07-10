"""Pregnancy activity gate tests; run: python -m tests.test_pregnancy"""

from __future__ import annotations

from engine.family import GESTATION_DAYS
from engine.pregnancy import (
    LATE_PREGNANCY_SUNRISES,
    in_late_pregnancy,
    pregnancy_activity_block,
    pregnancy_elapsed,
)
from engine.vitals import full_activity_block

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


class FakeUser(dict):
    def keys(self):
        return super().keys()


def _row(**kwargs) -> FakeUser:
    defaults = {
        "id": 1,
        "wolf_name": "Ash",
        "birth_sex": "female",
        "is_pregnant": 1,
        "pregnancy_start_day": 10,
        "last_rest_day": 0,
        "condition": "healthy",
        "hp": 20,
        "hunger": 80,
        "thirst": 80,
        "mood": 50,
        "exhaustion": 0,
    }
    defaults.update(kwargs)
    return FakeUser(defaults)


def main() -> None:
    print("\n=== pregnancy gates ===")
    start = 10
    late_day = start + GESTATION_DAYS - LATE_PREGNANCY_SUNRISES
    early_day = late_day - 1

    user = _row()
    check("early gestation not late", not in_late_pregnancy(user, early_day))
    check("late gestation flagged", in_late_pregnancy(user, late_day))
    check(
        "elapsed days",
        pregnancy_elapsed(user, late_day) == GESTATION_DAYS - LATE_PREGNANCY_SUNRISES,
    )

    block = pregnancy_activity_block(user, "hunt", late_day)
    check("hunt blocked late", block is not None and "late pregnancy" in block.lower())
    check("forage not blocked", pregnancy_activity_block(user, "forage", late_day) is None)

    male = _row(birth_sex="male")
    check("male not blocked", pregnancy_activity_block(male, "hunt", late_day) is None)

    not_preg = _row(is_pregnant=0)
    check("not pregnant", pregnancy_activity_block(not_preg, "hunt", late_day) is None)

    # late pregnancy no longer hard-blocks via full_activity_block; the action
    # proceeds and engine.strenuous_strain applies the yield/miscarriage risk
    # on the allow-path instead (see apply_strenuous_strain).
    vitals = full_activity_block(user, late_day, action="explore")
    check("full_activity_block no longer blocks late pregnancy (soft penalty instead)", vitals is None)

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
