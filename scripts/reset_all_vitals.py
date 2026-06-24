"""Fill HP, mood, hunger, and thirst for every wolf. Usage: python scripts/reset_all_vitals.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database as db
from config import HUNGER_MAX, MOOD_MAX, THIRST_MAX
from engine.exhaustion_effects import effective_max_hp


def main() -> None:
    db.init_db()
    updated = 0
    with db.get_db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY wolf_name").fetchall()
        for row in rows:
            user = dict(row)
            cap = effective_max_hp(user)
            conn.execute(
                """
                UPDATE users
                SET hp = ?,
                    mood = ?,
                    hunger = ?,
                    thirst = ?,
                    exhaustion = 0
                WHERE id = ?
                """,
                (cap, MOOD_MAX, HUNGER_MAX, THIRST_MAX, user["id"]),
            )
            updated += 1
        conn.commit()
    print(f"Reset vitals for {updated} wolf(s).")
    print(f"  HP -> each wolf's max (exhaustion cleared)")
    print(f"  Mood -> {MOOD_MAX}")
    print(f"  Hunger -> {HUNGER_MAX}")
    print(f"  Thirst -> {THIRST_MAX}")


if __name__ == "__main__":
    main()
