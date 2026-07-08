"""Forage role perks and roll routing; run: python -m tests.test_forage_privileges"""

from __future__ import annotations

from engine.role_privileges import (
    forage_check_params,
    forage_sunrise_footer,
    is_full_forager,
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


def _user(**kwargs):
    base = {"wolf_role": "hunter", "last_forage_day": 5}
    base.update(kwargs)
    return base


def test_forage_check_params() -> None:
    print("\n=== forage_check_params ===")
    attrs, skill, key, prof = forage_check_params(_user(wolf_role="forager"), [])
    check("forager uses Herblore", skill == "Herblore" and key == "herblore" and prof)
    check("forager INT/WIS", attrs == ("attr_int", "attr_wis"))

    attrs, skill, key, prof = forage_check_params(_user(wolf_role="hunter"), ["survival"])
    check("survival hunter uses Survival", skill == "Survival" and key == "survival" and prof)
    check("survival hunter CON/STR", attrs == ("attr_con", "attr_str"))

    attrs, skill, key, prof = forage_check_params(_user(wolf_role="hunter"), ["herblore"])
    check("herblore prof uses Herblore", skill == "Herblore" and key == "herblore" and prof)

    attrs, skill, key, prof = forage_check_params(_user(wolf_role="hunter"), [])
    check("untrained uses Survival", skill == "Survival" and not prof)


def test_forage_sunrise_footer() -> None:
    print("\n=== forage_sunrise_footer ===")
    full = _user(wolf_role="forager")
    check(
        "full forager fail footer mentions again",
        "forage again this sunrise" in forage_sunrise_footer(full),
    )
    check(
        "full forager not spent",
        "spent" not in forage_sunrise_footer(full).lower(),
    )
    check(
        "hunter fail footer spent",
        "spent" in forage_sunrise_footer(_user(wolf_role="hunter")).lower(),
    )
    check(
        "full forager success hint",
        "inventory" in forage_sunrise_footer(full, success_hint=True)
        and "forage again" in forage_sunrise_footer(full, success_hint=True),
    )
    check("is_full_forager", is_full_forager(full))
    check("apprentice not full", not is_full_forager(_user(wolf_role="forager_apprentice")))


def main() -> None:
    global _pass, _fail
    test_forage_check_params()
    test_forage_sunrise_footer()
    print(f"\n=== {_pass} passed, {_fail} failed ===")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
