"""Skill rank XP and check bonuses; run: python -m tests.test_skill_ranks"""

from __future__ import annotations

import json

import database as db
from engine.character import get_skill_rank, skill_proficiency_bonus
from engine.dice import resolve_check
from rpg_rules import MAX_SKILL_RANK, PROFICIENCY_BONUS, SKILL_RANK_BONUS

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

    user = Row(
        id=999001,
        discord_id=999001,
        wolf_role="hunter",
        attr_str=6,
        attr_dex=6,
        attr_con=6,
        attr_int=6,
        attr_cha=6,
        attr_wis=6,
        skill_proficiencies=json.dumps(["tracking"]),
        skill_ranks=json.dumps({"tracking": 2}),
        exhaustion=0,
        omen_buff="",
    )

    bonus = skill_proficiency_bonus(user, "tracking", proficient=True)
    expected = PROFICIENCY_BONUS + 2 * SKILL_RANK_BONUS
    check("rank bonus stacks on proficiency", bonus == expected, f"got {bonus}")

    roll = resolve_check(
        user,
        attr_keys=("attr_int",),
        skill="Tracking",
        dc=10,
        proficient=True,
        skill_key="tracking",
    )
    check("resolve_check uses rank bonus", roll["proficiency"] == expected)
    check("roll shows rank_bonus field", roll.get("rank_bonus") == 2 * SKILL_RANK_BONUS)

    check("max skill rank constant", MAX_SKILL_RANK >= 1)

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
