"""Repeated activity exhaustion; run: python -m tests.test_activity_exhaustion"""

from __future__ import annotations

import database as db
from engine.activity_exhaustion import (
    _exhaustion_gain,
    apply_activity_fatigue,
    record_strenuous_activity,
)
from engine.role_privileges import record_hunt_use

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


def test_gain_formula() -> None:
    print("\n=== exhaustion gain formula ===")
    check("proficient 2nd hunt no gain", _exhaustion_gain(2, 2, True, 0) == 0)
    check("untrained 2nd hunt +1", _exhaustion_gain(2, 2, False, 0) == 1)
    check("proficient 3rd hunt +1", _exhaustion_gain(3, 3, True, 0) == 1)
    check("untrained 4th hunt +3", _exhaustion_gain(4, 4, False, 0) == 3)
    check("cross-activity pile at 4 total", _exhaustion_gain(1, 4, True, 0) == 1)
    check("caps at exhaustion room", _exhaustion_gain(5, 5, False, 5) == 1)


def test_hunt_repeat_applies_exhaustion() -> None:
    print("\n=== hunt repeat applies exhaustion ===")
    db.init_db()
    did = 999300001000000099
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                hunger, thirst, exhaustion, condition, wolf_role, skill_proficiencies
            ) VALUES (?, 'Tired', 1, 'omega', 0, 80, 80, 0, 'healthy', 'pup', '[]')
            """,
            (did,),
        )
    user = db.get_user(did)
    day = 42
    record_hunt_use(did, wolf_id=user["id"], day=day)
    note1 = apply_activity_fatigue(db.get_user(did), "hunt", "hunting", day, activity_count=1)
    check("first hunt no fatigue note", note1 is None)
    record_hunt_use(did, wolf_id=user["id"], day=day)
    note2 = apply_activity_fatigue(db.get_user(did), "hunt", "hunting", day, activity_count=2)
    check("second hunt untrained gains note", note2 is not None and "+1 exhaustion" in note2)
    updated = db.get_user(did)
    check("exhaustion increased", int(updated["exhaustion"]) == 1, f"got {updated['exhaustion']}")


def test_record_strenuous_resets_on_new_day() -> None:
    print("\n=== counters reset on new day ===")
    db.init_db()
    did = 999300001000000098
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                hunger, thirst, exhaustion, condition, wolf_role
            ) VALUES (?, 'Fresh', 1, 'omega', 0, 80, 80, 0, 'healthy', 'hunter')
            """,
            (did,),
        )
    user = db.get_user(did)
    c1, t1 = record_strenuous_activity(user, "forage", 10)
    user = db.get_user(did)
    c2, t2 = record_strenuous_activity(user, "forage", 11)
    check("new day resets activity count", c2 == 1, f"got {c2}")
    check("new day resets total", t2 == 1, f"got {t2}")


def main() -> None:
    test_gain_formula()
    test_hunt_repeat_applies_exhaustion()
    test_record_strenuous_resets_on_new_day()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
