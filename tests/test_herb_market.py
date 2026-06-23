"""Herb market and medic-rounds hoard scans; run: python -m tests.test_herb_market"""

from __future__ import annotations

from unittest.mock import patch

import database as db
from engine.herb_market import forage_herb_sell_price, sell_forage_herb_stack
from engine.restricted_herbs import medic_rounds_scan_hoarders


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


def test_sell_prices() -> None:
    print("\n=== sell prices ===")
    check("chamomile common", forage_herb_sell_price("chamomile", form="fresh", potency=100, spoiling=False) == 4)
    check("restricted zero", forage_herb_sell_price("foxglove", form="fresh", potency=100, spoiling=False) == 0)
    check("spoiling half", forage_herb_sell_price("chamomile", form="fresh", potency=100, spoiling=True) == 2)


def test_medic_rounds_scan() -> None:
    print("\n=== medic rounds scan ===")
    db.init_db()
    did = 999500001000000099
    with db.get_db() as conn:
        conn.execute("DELETE FROM herb_stacks WHERE wolf_id IN (SELECT id FROM users WHERE discord_id = ?)", (did,))
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at, condition, standing, wolf_role
            ) VALUES (?, 'Hoarder', 1, 'subordinate', 'test', 'healthy', 5, 'hunter')
            """,
            (did,),
        )
    user = db.get_user(did)
    wolf_id = user["id"]
    db.add_herb_stack(wolf_id, "wolfsbane", guild_id=1, acquired_day=1)

    with patch("engine.restricted_herbs.roll_restricted_hoard_caught", return_value=False):
        caught, suspicious = medic_rounds_scan_hoarders(1)
    check("not caught", not caught and len(suspicious) >= 1)
    check("standing safe", int(db.get_user_by_id(wolf_id)["standing"]) == 5)

    db.add_herb_stack(wolf_id, "chamomile", guild_id=1, acquired_day=1)
    with patch("engine.restricted_herbs.roll_restricted_hoard_caught", return_value=True):
        caught2, suspicious2 = medic_rounds_scan_hoarders(1)
    check("caught", len(caught2) >= 1)
    check("suspicious cleared", not suspicious2 or len(suspicious2) == 0)

    db.add_herb_stack(wolf_id, "chamomile", guild_id=1, acquired_day=5)
    user = db.get_user_by_id(wolf_id)
    chamomile_stack = next(s for s in db.get_herb_stacks(wolf_id) if s["herb_key"] == "chamomile")
    ok, msg, price = sell_forage_herb_stack(user, chamomile_stack["id"], day=5)
    check("sell chamomile", ok and price == 4)

    with db.get_db() as conn:
        conn.execute("DELETE FROM herb_stacks WHERE wolf_id = ?", (wolf_id,))
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))


def main() -> None:
    test_sell_prices()
    test_medic_rounds_scan()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
