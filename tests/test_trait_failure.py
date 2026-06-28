"""Practice strain on failed skill rolls; run: python -m tests.test_trait_failure"""

from __future__ import annotations

import database as db
from engine.character_traits import (
    adjust_skill_trait_experience,
    compute_failure_strain_gain,
    decay_skill_strain_on_rollover,
    earned_trait_bonus_total,
    maybe_apply_failure_setback,
    maybe_apply_success_recovery,
    parse_character_traits,
    parse_skill_strain_state,
)
from rpg_rules import SKILL_STRAIN_THRESHOLD

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

    did = 993001
    db.register_user(did, "FailWolf", affiliation="lone", wolf_role="scout")
    user = db.get_user(did)
    assert user

    gain, note = compute_failure_strain_gain(
        user, outcome="failure", total=14, dc=15
    )
    check("close miss no strain", gain == 0 and "close call" in note)

    gain2, _ = compute_failure_strain_gain(user, outcome="failure", total=10, dc=15)
    check("clear miss adds strain", gain2 >= 1)

    adjust_skill_trait_experience(user["id"], "tracking", 2)
    user = db.get_user_by_id(user["id"])

    for _ in range(SKILL_STRAIN_THRESHOLD):
        maybe_apply_failure_setback(
            user,
            skill_key="tracking",
            outcome="failure",
            game_day=10,
            total=5,
            dc=15,
        )
        user = db.get_user_by_id(user["id"])

    traits = parse_character_traits(user["character_traits"])
    check("strain converts to lost earned", earned_trait_bonus_total(traits, "tracking") < 2)

    user = db.get_user_by_id(user["id"])
    state = parse_skill_strain_state(user["trait_failure_days"])
    check("some strain may remain", "tracking" in state or earned_trait_bonus_total(traits, "tracking") < 2)

    maybe_apply_success_recovery(user, skill_key="tracking", dc=15)
    user = db.get_user_by_id(user["id"])
    state_after = parse_skill_strain_state(user["trait_failure_days"])
    check(
        "success lowers strain",
        state_after.get("tracking", {}).get("strain", 0)
        <= state.get("tracking", {}).get("strain", 99),
    )

    with db.get_db() as conn:
        conn.execute(
            "UPDATE users SET trait_failure_days = ? WHERE id = ?",
            ('{"tracking": {"strain": 2}}', user["id"]),
        )
    decay_skill_strain_on_rollover()
    user = db.get_user_by_id(user["id"])
    state_rest = parse_skill_strain_state(user["trait_failure_days"])
    check("rollover eases strain", state_rest.get("tracking", {}).get("strain", 0) == 1)

    print(f"\n{_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
