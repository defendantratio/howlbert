"""Per-guild season hooks on sunrise; winter hunger stress, food cache meals."""

from __future__ import annotations

import sqlite3

from config import HUNGER_ROLLOVER_DECAY
from engine.hunger import meal_hunger_gain

import database as db


def _rollover_wolf_ids(conn: sqlite3.Connection) -> list[int]:
    """Living wolves for global sunrise season hooks (packs are not per-guild)."""
    rows = conn.execute(
        """
        SELECT id FROM users
        WHERE condition NOT IN ('dead', 'dying')
        """
    ).fetchall()
    return [int(r["id"]) for r in rows]


def apply_winter_hunger_stress(
    conn: sqlite3.Connection, guild_id: int, *, season: str
) -> list[str]:
    """Winter; wolves need ~1.5× food; extra hunger decay at sunrise."""
    del guild_id  # global wolf tick; guild only scopes den-news routing
    if season != "winter":
        return []
    extra = max(1, int(HUNGER_ROLLOVER_DECAY * 0.5))
    rows = conn.execute(
        "SELECT id, ic_location FROM users WHERE condition NOT IN ('dead', 'dying')"
    ).fetchall()
    if not rows:
        return []
    from engine.location_effects import location_winter_hunger_exempt

    ids = [
        int(row["id"])
        for row in rows
        if not location_winter_hunger_exempt(row["ic_location"])
    ]
    if not ids:
        return []
    placeholders = ",".join("?" * len(ids))
    conn.execute(
        f"update users set hunger = max(0, hunger - ?) where id in ({placeholders})",
        (extra, *ids),
    )
    return [f"leaf-bare cold bites; **−{extra}** extra satiety for wolves in winter dens."]


def apply_food_cache_on_rollover(conn: sqlite3.Connection, guild_id: int) -> list[dict]:
    """Spend cached autumn hunt meals (+hunger per cache)."""
    del guild_id
    ids = _rollover_wolf_ids(conn)
    if not ids:
        return []
    notes: list[dict] = []
    gain = meal_hunger_gain("deer")
    for wolf_id in ids:
        row = conn.execute(
            "SELECT wolf_name, food_cache_meals FROM users WHERE id = ?",
            (wolf_id,),
        ).fetchone()
        if not row or int(row["food_cache_meals"] or 0) <= 0:
            continue
        meals = int(row["food_cache_meals"])
        hunger_add = meals * gain
        conn.execute(
            """
            UPDATE users
            SET food_cache_meals = 0,
                hunger = MIN(100, hunger + ?)
            WHERE id = ?
            """,
            (hunger_add, wolf_id),
        )
        notes.append(
            {
                "wolf_name": row["wolf_name"],
                "text": f"ate **{meals}** cached kill(s) (+{hunger_add} satiety)",
            }
        )
    return notes


def apply_season_rollover_effects(
    conn: sqlite3.Connection, guild_id: int, season: str
) -> tuple[list[str], list[dict]]:
    lines = apply_winter_hunger_stress(conn, guild_id, season=season)
    cache_notes = apply_food_cache_on_rollover(conn, guild_id)
    return lines, cache_notes


def try_autumn_hunt_cache(user, *, season: str) -> str | None:
    """on successful hunt in autumn; stash +1 day of food for next sunrise."""
    if season != "autumn" or not user or "id" not in user.keys():
        return None
    with db.get_db() as conn:
        conn.execute(
            "UPDATE users SET food_cache_meals = food_cache_meals + 1 WHERE id = ?",
            (user["id"],),
        )
    return "_autumn cache; +1 day of food stored for next sunrise._"
