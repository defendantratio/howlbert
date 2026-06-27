"""One-shot: full heal all living wolves (illness, injuries, HP, exhaustion)."""
import json
import sys

sys.path.insert(0, ".")

import database as db


def main() -> None:
    db.init_db()
    healed = 0
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, long_term_injuries
            FROM users
            WHERE condition != 'dead'
            """
        ).fetchall()
        for row in rows:
            lt: list = []
            try:
                raw = json.loads(row["long_term_injuries"] or "[]")
                if isinstance(raw, list):
                    lt = [x for x in raw if x != "spirit_curse"]
            except json.JSONDecodeError:
                lt = []
            conn.execute(
                """
                UPDATE users SET
                    hp = max_hp,
                    exhaustion = 0,
                    disease = NULL,
                    quarantined = 0,
                    active_injuries = '[]',
                    condition = 'healthy',
                    bone_rest_until = 0,
                    distressed = 0,
                    long_term_injuries = ?
                WHERE id = ?
                """,
                (json.dumps(lt), row["id"]),
            )
            healed += 1
        dead = conn.execute(
            "SELECT COUNT(id) AS c FROM users WHERE condition = 'dead'"
        ).fetchone()["c"]

    print(f"Healed {healed} living wolves (skipped {dead} dead).")
    with db.get_db() as conn:
        sick = conn.execute(
            """
            SELECT COUNT(id) AS c FROM users
            WHERE condition != 'dead'
              AND (
                hp < max_hp OR exhaustion > 0 OR disease IS NOT NULL
                OR active_injuries != '[]' OR condition != 'healthy'
              )
            """
        ).fetchone()["c"]
    print(f"Remaining non-healthy living wolves: {sick}")


if __name__ == "__main__":
    main()
