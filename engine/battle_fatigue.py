"""Battle fatigue; pack-wide war strain from sustained combat."""

from __future__ import annotations

import sqlite3

WAR_STRAIN_MOOD_DRAIN = 2
WAR_STRAIN_MAX = 3


def record_pack_combat_day(pack_id: int, day: int) -> None:
    """Call once per rollover per pack that had any combat encounter that day."""
    import database as db
    with db.get_db() as conn:
        conn.execute(
            "UPDATE packs SET last_combat_day = ? WHERE id = ?",
            (day, pack_id),
        )


def apply_battle_fatigue_on_rollover(conn: sqlite3.Connection, day: int) -> list[dict]:
    """Accumulate or clear war_strain per pack; drain mood for strained wolves."""
    notes: list[dict] = []
    packs = conn.execute(
        "SELECT id, name, war_strain, last_combat_day FROM packs"
    ).fetchall()
    for pack in packs:
        pack_id = int(pack["id"])
        war_strain = int(pack["war_strain"])
        last_combat = int(pack["last_combat_day"] or 0)
        fought_yesterday = (day > 0) and (last_combat == day - 1)
        if fought_yesterday:
            new_strain = min(WAR_STRAIN_MAX, war_strain + 1)
        else:
            new_strain = max(0, war_strain - 1)
        if new_strain != war_strain:
            conn.execute(
                "UPDATE packs SET war_strain = ? WHERE id = ?",
                (new_strain, pack_id),
            )
        if new_strain <= 0:
            continue
        drain = new_strain * WAR_STRAIN_MOOD_DRAIN
        members = conn.execute(
            "SELECT id, wolf_name, discord_id, mood FROM users "
            "WHERE pack_id = ? AND condition NOT IN ('dead', 'dying')",
            (pack_id,),
        ).fetchall()
        for wolf in members:
            old_mood = int(wolf["mood"])
            new_mood = max(0, old_mood - drain)
            if new_mood == old_mood:
                continue
            conn.execute("UPDATE users SET mood = ? WHERE id = ?", (new_mood, wolf["id"]))
        if members:
            notes.append({
                "pack_id": pack_id,
                "line": (
                    f"**{pack['name']}**: war strain **{new_strain}/{WAR_STRAIN_MAX}** — "
                    f"**−{drain} mood** across the den. rest a sunrise to let it ease."
                ),
            })
    return notes
