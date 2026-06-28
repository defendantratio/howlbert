"""Spirit curse tests; run: python -m tests.test_supernatural"""

from __future__ import annotations

import database as db
from engine.long_term_injuries import check_adjustments, format_long_term_injuries
from engine.supernatural import (
    apply_spirit_curse,
    has_spirit_curse,
    lift_spirit_curse,
    spirit_curse_check_adjustment,
)


class Row(dict):
    def keys(self):
        return super().keys()


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


def main() -> None:
    db.init_db()
    db.purge_test_accounts()
    did = 991001
    db.register_user(did, "CursedWolf", affiliation="lone", wolf_role="medic")
    user = db.get_user(did)
    assert user

    ok, msg = apply_spirit_curse(user["id"], source="test")
    check("apply curse", ok, msg)
    user = db.get_user_by_id(user["id"])
    check("has curse", has_spirit_curse(user))
    check("format line", format_long_term_injuries(user) and "spirit curse" in format_long_term_injuries(user))

    mod, note = spirit_curse_check_adjustment(user, attr_keys=("attr_wis",), skill_key="medicine")
    check("wis penalty", mod == -1 and "spirit curse" in note)

    mod, dis, notes = check_adjustments(
        user,
        attr_keys=("attr_wis",),
        skill_key="medicine",
        weather="clear",
        day_number=1,
        first_physical_today=True,
    )
    check("lt adjustments", mod == -1 and "spirit curse" in notes)

    check("lift curse", lift_spirit_curse(user["id"]))
    user = db.get_user_by_id(user["id"])
    check("curse gone", not has_spirit_curse(user))

    ok, msg = apply_spirit_curse(user["id"])
    check("re-apply", ok)
    check("duplicate blocked", not apply_spirit_curse(user["id"])[0])

    print(f"\n{_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
