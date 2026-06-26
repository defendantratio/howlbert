"""Revive every wolf with condition=dead. Usage: python scripts/revive_all_dead.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database as db
from config import MAX_WOLF_AGE_MOONS, NEEDS_SURVIVAL_RESTORE, REVIVE_MOOD_FLOOR, REVIVE_OLD_AGE_RESET


def main() -> None:
    db.init_db()
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, wolf_name, discord_id, age_months
            FROM users WHERE condition = 'dead'
            ORDER BY wolf_name
            """
        ).fetchall()
        if not rows:
            print("No dead wolves found.")
            return
        print(f"Reviving {len(rows)} wolf(s):")
        for row in rows:
            old_age = int(row["age_months"] or 24)
            new_age = REVIVE_OLD_AGE_RESET if old_age >= MAX_WOLF_AGE_MOONS else old_age
            conn.execute(
                """
                UPDATE users
                SET condition = 'healthy',
                    hp = 1,
                    death_save_round = 0,
                    death_save_fails = 0,
                    death_save_successes = 0,
                    cause_of_death = NULL,
                    death_day = NULL,
                    exhaustion = 0,
                    hunger = ?,
                    thirst = ?,
                    mood = MAX(?, mood),
                    age_months = ?
                WHERE id = ?
                """,
                (
                    NEEDS_SURVIVAL_RESTORE,
                    NEEDS_SURVIVAL_RESTORE,
                    REVIVE_MOOD_FLOOR,
                    new_age,
                    row["id"],
                ),
            )
            print(f"  - {row['wolf_name']} (id={row['id']})")
        conn.commit()
        left = conn.execute(
            "SELECT COUNT(*) AS n FROM users WHERE condition = 'dead'"
        ).fetchone()["n"]
        print(f"Done. Still dead: {left}")


if __name__ == "__main__":
    main()
