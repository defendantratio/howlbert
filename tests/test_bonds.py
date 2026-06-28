"""Bond tracker tests; run: python -m tests.test_bonds"""

from __future__ import annotations

import database as db
from engine.bonds import apply_socialize_bonds, format_bonds_embed_body, strength_tier

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

    db.register_user(770001, "BondWolfA", affiliation="lone", wolf_role="omega")
    db.register_user(770002, "BondWolfB", affiliation="lone", wolf_role="omega")
    a = db.get_user(770001)
    b = db.get_user(770002)
    assert a and b

    row = db.set_bond(a["id"], b["id"], "friendship", strength=55, note="packmate", day=10)
    check("set friendship", row is not None and row["strength"] == 55)
    check("canonical pair", row["wolf_a_id"] < row["wolf_b_id"])

    bumped = db.adjust_bond_strength(a["id"], b["id"], "friendship", 10, day=11)
    check("adjust friendship", bumped is not None and bumped["strength"] == 65)

    rivalry = db.adjust_bond_strength(a["id"], b["id"], "rivalry", 20, day=11)
    check("create rivalry", rivalry is not None and rivalry["strength"] == 60)

    note = apply_socialize_bonds(a, b, "warm", day=12)
    check("socialize warm note", note is not None and "Bond" in note)

    body = format_bonds_embed_body(a)
    check("format body has friendship", "friendship" in body and "BondWolfB" in body)
    check("strength tier close", strength_tier(65) == "close")

    family, err = db.create_wolf_family(a["id"], f"The Howlers {a['id']}", day=12)
    check("create family", family is not None and not err, err or "")
    joined, jerr = db.join_wolf_family(b["id"], f"The Howlers {a['id']}", role="sibling", day=12)
    check("join family", joined is not None and not jerr, jerr or "")
    members = db.get_family_members(family["id"])
    check("two members", len(members) == 2)

    left, lerr = db.leave_wolf_family(b["id"])
    check("leave family", left and not lerr)
    check("still one member", len(db.get_family_members(family["id"])) == 1)

    cleared = db.clear_bond(a["id"], b["id"], "friendship")
    check("clear bond", cleared and db.get_bond(a["id"], b["id"], "friendship") is None)

    print(f"\n{_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
