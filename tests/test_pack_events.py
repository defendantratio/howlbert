"""Pack rollover den event mechanics."""

from __future__ import annotations

import database as db
from engine.pack_events import _apply_pack_event_effect, roll_pack_event_for_rollover


def test_raccoon_event_steals_from_stash():
    db.init_db()
    with db.get_db() as conn:
        pack = conn.execute("SELECT id FROM packs LIMIT 1").fetchone()
        if not pack:
            return
        pack_id = int(pack["id"])
        guild = conn.execute("SELECT guild_id FROM world_state LIMIT 1").fetchone()
        guild_id = int(guild["guild_id"]) if guild else 1
        conn.execute("DELETE FROM pack_prey_stacks WHERE pack_id = ?", (pack_id,))
        cur = conn.execute(
            """
            INSERT INTO pack_prey_stacks
            (pack_id, guild_id, prey_key, uses_left, bone_value, acquired_day)
            VALUES (?, ?, 'vole', 3, 2, 1)
            """,
            (pack_id, guild_id),
        )
        stack_id = cur.lastrowid
        conn.commit()
        suffix = _apply_pack_event_effect(conn, pack_id, "raccoon")
        assert "stole" in suffix.lower()
        row = conn.execute(
            "SELECT uses_left FROM pack_prey_stacks WHERE id = ?",
            (stack_id,),
        ).fetchone()
        assert row and int(row["uses_left"]) == 2


def test_roll_respects_once_per_day():
    db.init_db()
    with db.get_db() as conn:
        pack = conn.execute("SELECT id FROM packs LIMIT 1").fetchone()
        if not pack:
            return
        pack_id = int(pack["id"])
        conn.execute(
            "UPDATE packs SET last_pack_event_day = 99 WHERE id = ?", (pack_id,)
        )
        conn.commit()
    assert roll_pack_event_for_rollover(pack_id, 50) is None


if __name__ == "__main__":
    test_raccoon_event_steals_from_stash()
    test_roll_respects_once_per_day()
    print("test_pack_events: ok")
