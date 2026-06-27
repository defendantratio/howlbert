"""Caught cross-pack scandal pressure."""

import database as db
from engine.den_rhythm import apply_bond_relation_pressure


def test_scandal_only_after_caught_recorded():
    with db.get_db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO packs (id, name, treasury, tax_rate, created_at)
            VALUES (501, 'PackA', 100, 10, datetime('now')),
                   (502, 'PackB', 100, 10, datetime('now'))
            """
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO users (
                id, discord_id, wolf_name, pack_id, great_pack, hp, max_hp, mood,
                hunger, thirst, exhaustion, condition, created_at
            ) VALUES
            (5011, 50101, 'WolfA', 501, 'greyspire', 20, 20, 50, 80, 80, 0, 'healthy', datetime('now')),
            (5021, 50201, 'WolfB', 502, 'thistlehide', 20, 20, 50, 80, 80, 0, 'healthy', datetime('now'))
            """
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO wolf_bonds (wolf_a_id, wolf_b_id, bond_type, strength, note, created_day, updated_day)
            VALUES (5011, 5021, 'friendship', 60, '', 1, 1)
            """
        )

    guild_id = 9999
    assert apply_bond_relation_pressure(guild_id, day=14) == []

    db.record_cross_pack_scandal(guild_id, 5011, 5021, caught_day=7)
    notes = apply_bond_relation_pressure(guild_id, day=14)
    assert len(notes) == 1
    assert "scandal" in notes[0].lower()
    assert db.get_pack_relation(guild_id, 501, 502) == 4
    bond = db.get_bond(5011, 5021, "friendship")
    assert bond and int(bond["strength"]) == 57
