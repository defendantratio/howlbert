"""Legacy skill rank tests now cover earned trait XP; run: python -m tests.test_skill_ranks"""

from __future__ import annotations

import database as db
from engine.character_traits import adjust_skill_trait_experience, earned_trait_bonus_total, parse_character_traits
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
    db.register_user(999001, "RankWolf", affiliation="lone", wolf_role="hunter")
    wolf = db.get_user(999001)
    assert wolf

    adjust_skill_trait_experience(wolf["id"], "tracking", 2)
    wolf = db.get_user_by_id(wolf["id"])
    traits = parse_character_traits(wolf["character_traits"])
    earned = earned_trait_bonus_total(traits, "tracking")
    check("quest-style rank becomes trait bonus", earned == 2, f"got {earned}")

    user = Row(
        id=wolf["id"],
        discord_id=999001,
        wolf_role="hunter",
        attr_str=6,
        attr_dex=6,
        attr_con=6,
        attr_int=6,
        attr_cha=6,
        attr_wis=6,
        character_traits=wolf["character_traits"],
        exhaustion=0,
        omen_buff="",
    )

    roll = resolve_check(
        user,
        attr_keys=("attr_int",),
        skill="Tracking",
        dc=10,
        proficient=True,
        skill_key="tracking",
    )
    check("traits on dice not proficiency", roll["trait_modifier"] == 2 and roll["proficiency"] == 0)

    check("max earned constant", MAX_EARNED_TRAIT_BONUS >= 1)

    print(f"\n{_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
