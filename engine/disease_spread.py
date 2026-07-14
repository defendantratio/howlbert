# disease_spread.py
"""Pack contagion at sunrise; Wolvden-style rollover spread."""

from __future__ import annotations

import random
import sqlite3

from engine.diseases import contagious_rate, encode_disease, parse_disease, spread_stage_for
from engine.quarantine import is_quarantined

# Wolves who were out in the field (hunted, patrolled, scouted) breathed fresh air all day.
# Respiratory diseases spread less to them; contact diseases still reach them via shared kills.
_FIELD_COLS = ("last_hunt_day", "last_patrol_day", "last_scout_day", "last_track_day")
_FIELD_RESP_REDUCTION = 0.50   # respiratory: half rate for field wolves
_FIELD_CONTACT_REDUCTION = 0.25  # contact/other: quarter reduction for field wolves


def _was_in_field(wolf, day: int) -> bool:
    """True if the wolf did any field activity on this rollover day."""
    if day <= 0:
        return False
    for col in _FIELD_COLS:
        if col in wolf.keys() and int(wolf[col] or 0) >= day:
            return True
    return False


def apply_disease_spread_on_rollover(
    conn: sqlite3.Connection, *, weather: str | None = None, day: int = 0, season: str | None = None
) -> list[dict]:
    """
    Infected wolves may pass illness to packmates who share a den.
    Wolves who spent the day in the field have reduced exposure to den-borne illness.
    Returns rollover note dicts for the admin embed.
    """
    rows = conn.execute(
        """
        SELECT * FROM users
        WHERE disease IS NOT NULL AND disease != ''
          AND condition NOT IN ('dead', 'dying')
          AND pack_id IS NOT NULL
          AND dormant = 0
        """
    ).fetchall()

    from engine.diseases import DISEASES
    from engine.humidity import humidity_disease_spread_mult

    notes: list[dict] = []
    for carrier in rows:
        if is_quarantined(carrier):
            continue
        disease_key, _ = parse_disease(carrier["disease"])
        rate = contagious_rate(disease_key)
        if rate <= 0:
            continue
        carrier_pack = carrier["great_pack"] if "great_pack" in carrier.keys() else None
        rate = min(1.0, rate * humidity_disease_spread_mult(carrier_pack, weather))
        is_respiratory = bool(DISEASES.get(disease_key, {}).get("respiratory"))
        # cold, denbound winters push respiratory illness through a pack faster
        if is_respiratory and season == "winter":
            rate = min(1.0, rate * 1.3)

        import database as _db

        packmates = conn.execute(
            f"""
            SELECT * FROM users
            WHERE pack_id = ? AND id != ?
              AND (disease IS NULL OR disease = '')
              AND condition NOT IN ('dead', 'dying')
              AND (quarantined IS NULL OR quarantined = 0)
              AND {_db.active_wolf_where(day)}
            """,
            (carrier["pack_id"], carrier["id"]),
        ).fetchall()

        spread_stage = spread_stage_for(disease_key)
        encoded = encode_disease(disease_key, spread_stage)

        for mate in packmates:
            effective_rate = rate
            if day > 0 and _was_in_field(mate, day):
                reduction = _FIELD_RESP_REDUCTION if is_respiratory else _FIELD_CONTACT_REDUCTION
                effective_rate = rate * (1.0 - reduction)
            if random.random() >= effective_rate:
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