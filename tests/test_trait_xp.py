"""Earned trait XP on skills; run: python -m tests.test_trait_xp"""

from __future__ import annotations

import database as db
from engine.character_traits import (
    adjust_skill_trait_experience,
    earned_trait_bonus_total,
    trait_check_adjustments,
)
from engine.dice import resolve_check
from rpg_rules import MAX_EARNED_TRAIT_BONUS

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
    db.init_db()
    db.purge_test_accounts()

    did = 992001
    db.register_user(did, "TraitWolf", affiliation="lone", wolf_role="hunter")
    user = db.get_user(did)
    assert user

    ok, msg = adjust_skill_trait_experience(user["id"], "tracking", 1)
    check("add earned trait", ok, msg)
    user = db.get_user_by_id(user["id"])
    traits = user["character_traits"]
    check("traits stored", traits and "experience" in traits)

    mod, names = trait_check_adjustments(user, ("attr_int",), skill_key="tracking")
    check("trait on check", mod == 1 and names, f"mod={mod} names={names}")

    roll = resolve_check(
        user,
        attr_keys=("attr_int",),
        skill="Tracking",
        dc=10,
        proficient=True,
        skill_key="tracking",
    )
    check("no proficiency on dice", roll["proficiency"] == 0)
    check("trait in roll total", roll["trait_modifier"] == 1)

    for _ in range(MAX_EARNED_TRAIT_BONUS - 1):
        adjust_skill_trait_experience(user["id"], "tracking", 1)
    user = db.get_user_by_id(user["id"])
    from engine.character_traits import parse_character_traits

    parsed = parse_character_traits(user["character_traits"])
    check("max earned", earned_trait_bonus_total(parsed, "tracking") == MAX_EARNED_TRAIT_BONUS)

    ok, _ = adjust_skill_trait_experience(user["id"], "tracking", 1)
    check("cannot exceed max", not ok)

    adjust_skill_trait_experience(user["id"], "tracking", -1)
    user = db.get_user_by_id(user["id"])
    parsed = parse_character_traits(user["character_traits"])
    check("negative peels bonus", earned_trait_bonus_total(parsed, "tracking") == MAX_EARNED_TRAIT_BONUS - 1)

    adjust_skill_trait_experience(user["id"], "tracking", -MAX_EARNED_TRAIT_BONUS)
    user = db.get_user_by_id(user["id"])
    parsed = parse_character_traits(user["character_traits"])
    from engine.character_traits import earned_trait_setback_total

    check("setback after bonus gone", earned_trait_bonus_total(parsed, "tracking") == 0)
    check("setback recorded", earned_trait_setback_total(parsed, "tracking") >= 1)

    print(f"\n{_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
