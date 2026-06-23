"""Forager role perk; one common herb per sunrise in pack territory."""

from __future__ import annotations

import random
import sqlite3

import database as db
from engine.role_privileges import is_forager
from herbs import HERBS


def _pick_forager_herb(user) -> str:
    """Mostly common herbs; pack territory adds a fair chance at local species."""
    common = [
        k
        for k, m in HERBS.items()
        if m["rarity"] == "common"
        and not m.get("poison")
        and "wild" in m.get("habitat", ("wild",))
    ]
    pack_key = user["great_pack"] if "great_pack" in user.keys() else None
    if pack_key:
        pack_herbs = [k for k, m in HERBS.items() if pack_key in m.get("packs", ())]
        if pack_herbs and random.random() < 0.4:
            return random.choice(pack_herbs)
    return random.choice(common or list(HERBS.keys()))


def grant_forager_auto_herb(user, *, day: int, guild_id: int) -> str | None:
    """
    Grant one common herb if forager hasn't received today's territory gift.
    Returns herb display name, or None.
    """
    if not is_forager(user):
        return None
    if not (user["pack_id"] if "pack_id" in user.keys() else None):
        return None
    last = int(user["last_forager_gift_day"]) if "last_forager_gift_day" in user.keys() else 0
    if last >= day:
        return None

    herb_key = _pick_forager_herb(user)
    from engine.herb_storage import grant_fresh_herb

    grant_fresh_herb(user["id"], herb_key=herb_key, guild_id=guild_id, day=day, user=user)
    db.update_user(user["discord_id"], wolf_id=user["id"], last_forager_gift_day=day)
    return HERBS[herb_key]["name"]


def apply_forager_daily_herbs_on_rollover(
    conn: sqlite3.Connection, day: int, *, guild_id: int
) -> list[dict]:
    """Auto-find herbs for foragers at sunrise."""
    rows = conn.execute(
        """
        SELECT * FROM users
        WHERE condition NOT IN ('dead', 'dying')
          AND pack_id IS NOT NULL
          AND last_forager_gift_day < ?
        """,
        (day,),
    ).fetchall()

    granted: list[dict] = []
    for user in rows:
        if not is_forager(user):
            continue
        herb_key = _pick_forager_herb(user)
        from engine.herb_storage import grant_fresh_herb

        grant_fresh_herb(user["id"], herb_key=herb_key, guild_id=guild_id, day=day, user=user)
        conn.execute(
            "UPDATE users SET last_forager_gift_day = ? WHERE id = ?",
            (day, user["id"]),
        )
        granted.append(
            {
                "wolf_name": user["wolf_name"],
                "discord_id": user["discord_id"],
                "herb": HERBS[herb_key]["name"],
            }
        )
    return granted
