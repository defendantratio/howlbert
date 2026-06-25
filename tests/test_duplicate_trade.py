"""Duplicate hoard trade tests."""

from __future__ import annotations

import database as db
from engine.cat_clans import KNOWN_CAT_CLANS, validate_clan_name
from engine.duplicate_trade import collect_duplicates, duplicate_trust_gain


def test_canon_clans():
    assert "ThunderClan" in KNOWN_CAT_CLANS
    assert "ShadowClan" in KNOWN_CAT_CLANS
    name, err = validate_clan_name("windclan")
    assert name == "WindClan" and not err


def test_collect_inventory_duplicates():
    db.init_db()
    db.register_user(88100, "DupTrader", affiliation="greyspire")
    user = db.get_user(88100)
    assert user
    item = db.get_item_by_key("bone")
    if not item:
        return
    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO inventory (wolf_id, item_id, quantity) VALUES (?, ?, 4) "
            "ON CONFLICT(wolf_id, item_id) DO UPDATE SET quantity = 4",
            (user["id"], item["id"]),
        )
    bundle = collect_duplicates(user["id"])
    assert bundle.total_items >= 3
    assert duplicate_trust_gain(bundle) >= 2


if __name__ == "__main__":
    test_canon_clans()
    test_collect_inventory_duplicates()
    print("test_duplicate_trade: ok")
