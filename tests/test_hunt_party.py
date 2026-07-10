"""Pack hunt chemistry tests; run: python -m tests.test_hunt_party"""

from __future__ import annotations

import database as db
from unittest.mock import patch
from engine.hunt_party import collab_hunt_bond_modifiers

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


def _user(wolf_id: int, name: str) -> FakeUser:
    return FakeUser({"id": wolf_id, "wolf_name": name})


def main() -> None:
    print("\n=== hunt party chemistry ===")
    db.init_db()

    bonus, note = collab_hunt_bond_modifiers([])
    check("solo party no bonus", bonus == 0 and note == "")

    a_id, b_id = 88001, 88002
    with db.get_db() as conn:
        conn.execute("DELETE FROM wolf_bonds WHERE wolf_a_id IN (?, ?)", (a_id, b_id))
    db.set_bond(a_id, b_id, "friendship", strength=45, day=1)
    users = [_user(a_id, "A"), _user(b_id, "B")]
    bonus, note = collab_hunt_bond_modifiers(users)
    check("moderate friendship +4%", bonus == 4)
    check("friendship note", "chemistry" in note.lower())

    db.set_bond(a_id, b_id, "friendship", strength=90, day=1)
    bonus, _ = collab_hunt_bond_modifiers(users)
    check("strong friendship +8%", bonus == 8)

    db.set_bond(a_id, b_id, "rivalry", strength=65, day=1)
    with patch("engine.hunt_party.random.random", return_value=0.0):
        bonus, note = collab_hunt_bond_modifiers(users)
    check("heated rivalry can fail hunt", bonus == -100 and "rivalry" in note.lower())

    from engine.role_privileges import hunts_left_footer, hunts_used_today, record_hunt_use

    did = 88099
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                hp, max_hp, hunger, thirst, exhaustion, condition, wolf_role
            ) VALUES (?, 'Counter', 1, 'hunter', 0, 20, 20, 80, 80, 0, 'healthy', 'hunter')
            """,
            (did,),
        )
    user = db.get_user(did)
    day = 77
    record_hunt_use(did, wolf_id=user["id"], day=day)
    user = db.get_user(did)
    check("hunt use increments same sunrise", hunts_used_today(user, day) == 1)
    check("hunt footer shows energy", hunts_left_footer(user, day).startswith("hunter: energy "))

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
