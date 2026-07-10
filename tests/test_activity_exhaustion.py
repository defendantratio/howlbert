"""Repeated activity exhaustion; run: python -m tests.test_activity_exhaustion"""

from __future__ import annotations

import database as db
from engine.activity_exhaustion import (
    apply_activity_fatigue,
    clear_activity_fatigue,
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


def test_activity_fatigue_no_longer_stacks_on_energy() -> None:
    print("\n=== repeated activity adds no exhaustion (energy is the throttle) ===")
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
    # even an untrained pup hunting repeatedly gains no activity-driven exhaustion;
    # the only exhaustion source from acting is running the energy bar empty.
    for n in (1, 2, 3, 4):
        record_hunt_use(did, wolf_id=user["id"], day=day)
        note = apply_activity_fatigue(db.get_user(did), "hunt", "hunting", day, activity_count=n)
        check(f"hunt #{n} shows no fatigue note", note is None)
    updated = db.get_user(did)
    check("exhaustion unchanged by repeated hunts", int(updated["exhaustion"]) == 0, f"got {updated['exhaustion']}")


def test_manual_long_rest_after_sunrise() -> None:
    print("\n=== manual long rest after sunrise sleep ===")
    db.init_db()
    did = 999300001000000096
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                hunger, thirst, exhaustion, condition, wolf_role, last_rest_day
            ) VALUES (?, 'Sleeper', 1, 'omega', 0, 80, 80, 2, 'healthy', 'hunter', 20)
            """,
            (did,),
        )
    user = db.get_user(did)
    day = 20
    from engine.conditions import manual_long_rest_used_today, mark_manual_long_rest

    check("sunrise rest does not block manual", not manual_long_rest_used_today(user, day))
    mark_manual_long_rest(user, day)
    check("manual long rest marked used", manual_long_rest_used_today(db.get_user(did), day))


def test_short_rest_clears_activity_fatigue() -> None:
    print("\n=== short rest clears fatigue counters ===")
    db.init_db()
    did = 999300001000000097
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                hunger, thirst, exhaustion, condition, wolf_role, skill_proficiencies
            ) VALUES (?, 'Rested', 1, 'omega', 0, 80, 80, 0, 'healthy', 'hunter', '["survival"]')
            """,
            (did,),
        )
    user = db.get_user(did)
    day = 15
    clear_activity_fatigue(user, day)
    note = apply_activity_fatigue(db.get_user(did), "forage", "survival", day)
    check("after short rest first forage has no fatigue note", note is None)


def main() -> None:
    test_activity_fatigue_no_longer_stacks_on_energy()
    test_manual_long_rest_after_sunrise()
    test_short_rest_clears_activity_fatigue()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
