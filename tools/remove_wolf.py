"""Remove LockTest (or any wolf by name) from the database."""
import sys

sys.path.insert(0, ".")

import database as db


def remove_wolf_by_name(name: str) -> None:
    db.init_db()
    with db.get_db() as conn:
        rows = conn.execute(
            "SELECT id, discord_id, wolf_name FROM users WHERE wolf_name = ? COLLATE NOCASE",
            (name,),
        ).fetchall()
        if not rows:
            print(f"No wolf named {name!r}.")
            return
        for row in rows:
            wid = int(row["id"])
            did = int(row["discord_id"])
            print(f"Removing {row['wolf_name']} (id={wid}, discord_id={did})")
            conn.execute("UPDATE users SET bonded_mate_id = NULL WHERE bonded_mate_id = ?", (wid,))
            conn.execute("DELETE FROM inventory WHERE wolf_id = ?", (wid,))
            conn.execute("DELETE FROM herb_stacks WHERE wolf_id = ?", (wid,))
            conn.execute("DELETE FROM prey_stacks WHERE wolf_id = ?", (wid,))
            conn.execute("DELETE FROM amusement_stacks WHERE wolf_id = ?", (wid,))
            conn.execute(
                "DELETE FROM user_quests WHERE wolf_id = ? OR (wolf_id IS NULL AND discord_id = ?)",
                (wid, did),
            )
            conn.execute("DELETE FROM wolf_death_log WHERE wolf_id = ?", (wid,))
            conn.execute("DELETE FROM users WHERE id = ?", (wid,))
            remaining = conn.execute(
                "SELECT id FROM users WHERE discord_id = ? ORDER BY id ASC LIMIT 1",
                (did,),
            ).fetchone()
            if remaining:
                conn.execute(
                    "UPDATE account_progress SET active_wolf_id = ? WHERE discord_id = ?",
                    (remaining["id"], did),
                )
            else:
                conn.execute("DELETE FROM account_progress WHERE discord_id = ?", (did,))
                conn.execute("DELETE FROM retired_wolves WHERE discord_id = ?", (did,))
                conn.execute("DELETE FROM chat_xp_claims WHERE discord_id = ?", (did,))
    with db.get_db() as conn:
        check = conn.execute(
            "SELECT id FROM users WHERE wolf_name = ? COLLATE NOCASE", (name,)
        ).fetchone()
    print("Removed." if not check else "Still present — check failed.")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "LockTest"
    remove_wolf_by_name(target)
