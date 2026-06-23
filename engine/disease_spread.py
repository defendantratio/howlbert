"""Pack contagion at sunrise; Wolvden-style rollover spread."""

from __future__ import annotations

import random
import sqlite3

from engine.diseases import contagious_rate, encode_disease, parse_disease, spread_stage_for
from engine.quarantine import is_quarantined


def apply_disease_spread_on_rollover(conn: sqlite3.Connection) -> list[dict]:
    """
    Infected wolves may pass illness to packmates who share a den.
    Returns rollover note dicts for the admin embed.
    """
    rows = conn.execute(
        """
        SELECT * FROM users
        WHERE disease IS NOT NULL AND disease != ''
          AND condition NOT IN ('dead', 'dying')
          AND pack_id IS NOT NULL
        """
    ).fetchall()

    notes: list[dict] = []
    for carrier in rows:
        if is_quarantined(carrier):
            continue
        disease_key, _ = parse_disease(carrier["disease"])
        rate = contagious_rate(disease_key)
        if rate <= 0:
            continue

        packmates = conn.execute(
            """
            SELECT * FROM users
            WHERE pack_id = ? AND id != ?
              AND (disease IS NULL OR disease = '')
              AND condition NOT IN ('dead', 'dying')
              AND (quarantined IS NULL OR quarantined = 0)
            """,
            (carrier["pack_id"], carrier["id"]),
        ).fetchall()

        spread_stage = spread_stage_for(disease_key)
        encoded = encode_disease(disease_key, spread_stage)

        for mate in packmates:
            if random.random() >= rate:
                continue
            conn.execute(
                "UPDATE users SET disease = ? WHERE id = ?",
                (encoded, mate["id"]),
            )
            notes.append(
                {
                    "wolf_name": mate["wolf_name"],
                    "discord_id": mate["discord_id"],
                    "line": (
                        f"caught **{disease_key.replace('_', ' ')}** from den contact "
                        f"(carrier **{carrier['wolf_name']}**)."
                    ),
                }
            )
    return notes
