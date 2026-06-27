"""Restricted herb standing penalties; run: python -m tests.test_restricted_herbs"""

from __future__ import annotations

from unittest.mock import patch

import database as db
from config import RESTRICTED_HERB_HOARD_STANDING, RESTRICTED_HERB_MISUSE_STANDING
from engine.restricted_herbs import (
    RESTRICTED_HERBS,
    apply_restricted_hoard_audit_on_rollover,
    is_restricted_herb,
    on_restricted_herb_acquired,
    on_restricted_herb_treat,
    try_catch_restricted_hoarder,
)

_pass = 0
_fail = 0


class Row(dict):
    def keys(self):
        return super().keys()


def check(name: str, cond: bool, detail: str = "") -> None:
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  OK  {name}")
    else:
        _fail += 1
        print(f" FAIL {name}" + (f" - {detail}" if detail else ""))


def test_restricted_set() -> None:
    print("\n=== restricted set ===")
    check("wolfsbane restricted", is_restricted_herb("wolfsbane"))
    check("comfrey not restricted", not is_restricted_herb("comfrey"))
    check("set size", len(RESTRICTED_HERBS) == 10, str(len(RESTRICTED_HERBS)))


def test_standing_hooks() -> None:
    print("\n=== standing hooks ===")
    db.init_db()
    did = 999500001000000001
    with db.get_db() as conn:
        conn.execute("DELETE FROM herb_stacks WHERE wolf_id IN (SELECT id FROM users WHERE discord_id = ?)", (did,))
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at, condition, standing, wolf_role
            ) VALUES (?, 'Poacher', NULL, 'subordinate', 'test', 'healthy', 5, 'hunter')
            """,
            (did,),
        )
    user = db.get_user(did)
    wolf_id = user["id"]
    old = int(user["standing"])

    note = on_restricted_herb_treat(user, "foxglove")
    user = db.get_user_by_id(wolf_id)
    check("misuse standing", int(user["standing"]) == old + RESTRICTED_HERB_MISUSE_STANDING)
    check("misuse note", "Standing" in note)

    old2 = int(user["standing"])
    hoard_note = on_restricted_herb_acquired(user, "bloodroot")
    user = db.get_user_by_id(wolf_id)
    check("acquire no auto penalty", int(user["standing"]) == old2)
    check("acquire warn", "Medic knowledge" in hoard_note and "turnin" in hoard_note.lower())

    db.add_herb_stack(wolf_id, "wolfsbane", guild_id=1, acquired_day=1)
    item = db.get_item_by_key("herb_wolfsbane")
    if item:
        db.grant_item(did, item["id"], quantity=1)
    before_audit = int(db.get_user_by_id(wolf_id)["standing"])

    with patch("engine.restricted_herbs.roll_restricted_hoard_caught", return_value=False):
        with db.get_db() as conn:
            audit_notes = apply_restricted_hoard_audit_on_rollover(conn)
    after_skip = db.get_user_by_id(wolf_id)
    check("rollover not caught", not audit_notes)
    check("rollover skip standing", int(after_skip["standing"]) == before_audit)

    with patch("engine.restricted_herbs.roll_restricted_hoard_caught", return_value=True):
        caught = try_catch_restricted_hoarder(user)
    after_caught = db.get_user_by_id(wolf_id)
    check("caught note", caught and "Caught hoarding" in caught)
    check(
        "caught standing",
        int(after_caught["standing"]) == before_audit + RESTRICTED_HERB_HOARD_STANDING,
    )

    with db.get_db() as conn:
        conn.execute("UPDATE users SET wolf_role = 'medic' WHERE id = ?", (wolf_id,))
    medic = db.get_user_by_id(wolf_id)
    before = int(medic["standing"])
    exempt = on_restricted_herb_acquired(medic, "oleander")
    medic = db.get_user_by_id(wolf_id)
    check("medic hoard exempt", exempt == "" and int(medic["standing"]) == before)

    from engine.pack_herb_store import turnin_restricted_herb

    with db.get_db() as conn:
        conn.execute("UPDATE users SET pack_id = 1 WHERE id = ?", (wolf_id,))
    medic = db.get_user_by_id(wolf_id)
    fox_item = db.get_item_by_key("herb_foxglove")
    if fox_item:
        db.grant_item(medic["discord_id"], fox_item["id"], quantity=1)
    before_turnin = int(db.get_user_by_id(wolf_id)["standing"])
    ok, turn_msg = turnin_restricted_herb(
        medic, "herb_foxglove", pack_id=1, guild_id=1, day=10
    )
    after_turnin = db.get_user_by_id(wolf_id)
    check("turnin ok", ok and "Standing **+1**" in turn_msg)
    check("turnin standing", int(after_turnin["standing"]) == before_turnin + 1)

    with db.get_db() as conn:
        conn.execute("DELETE FROM herb_stacks WHERE wolf_id = ?", (wolf_id,))
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))


def main() -> None:
    test_restricted_set()
    test_standing_hooks()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
