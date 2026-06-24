"""apply_pack_tax returns (net, tax) tuple."""

from unittest.mock import patch

import database as db
from utils.hunting import apply_pack_tax, award_bones


class Row(dict):
    def keys(self):
        return super().keys()


def test_apply_pack_tax_returns_tuple():
    net, tax = apply_pack_tax(100, None)
    assert (net, tax) == (100, 0)


def test_apply_pack_tax_with_rate():
    db.init_db()
    with db.get_db() as conn:
        pack = conn.execute("SELECT id, tax_rate FROM packs LIMIT 1").fetchone()
        if not pack:
            return
        old_rate = int(pack["tax_rate"])
        conn.execute("UPDATE packs SET tax_rate = 10 WHERE id = ?", (pack["id"],))
    try:
        net, tax = apply_pack_tax(100, pack["id"])
        assert net == 90
        assert tax == 10
    finally:
        with db.get_db() as conn:
            conn.execute(
                "UPDATE packs SET tax_rate = ? WHERE id = ?",
                (old_rate, pack["id"]),
            )


def test_award_bones_unpacks():
    db.init_db()
    user = db.get_user(1056053114177855548)
    if not user:
        return
    with patch("database.add_bones"), patch("database.increment_quest_progress"):
        result = award_bones(user, 10, "clear", "scavenge", season="newgrowth")
    assert len(result) == 9
