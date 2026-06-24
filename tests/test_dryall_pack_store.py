"""dryall includes fresh healers' den store stacks."""

from __future__ import annotations

from unittest.mock import patch

import database as db
from engine.herb_preparation import dry_all_fresh_herbs


def test_dryall_dries_fresh_pack_store_stacks():
    db.init_db()
    did = 999500001000000099
    pack_id = 1
    with db.get_db() as conn:
        conn.execute("DELETE FROM pack_herb_stacks WHERE pack_id = ?", (pack_id,))
        conn.execute("DELETE FROM herb_stacks WHERE wolf_id IN (SELECT id FROM users WHERE discord_id = ?)", (did,))
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at, condition, standing, wolf_role
            ) VALUES (?, 'Dryer', ?, 'subordinate', 'test', 'healthy', 5, 'forager')
            """,
            (did, pack_id),
        )
    user = db.get_user(did)
    store_id = db.add_pack_herb_stack(
        pack_id,
        "yarrow",
        form="fresh",
        potency=100,
        quantity=2,
        acquired_day=5,
        guild_id=1,
        deposited_by=user["id"],
    )

    success_roll = {
        "die": 15,
        "first_die": 15,
        "modifier": 2,
        "total": 17,
        "dc": 10,
        "success": True,
        "outcome": "success",
        "attr_label": "WIS",
        "skill": "Herblore",
        "safe_roll_used": False,
    }
    with patch("engine.herb_preparation.resolve_check", return_value=success_roll):
        ok, msg = dry_all_fresh_herbs(user, day=10, guild_id=1, at_den=True)

    assert ok
    assert "den store" in msg.lower()
    stack = db.get_pack_herb_stack(store_id)
    assert stack is not None
    assert stack["form"] == "dried"
    assert int(stack["acquired_day"]) == 10

    with db.get_db() as conn:
        conn.execute("DELETE FROM pack_herb_stacks WHERE id = ?", (store_id,))
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
