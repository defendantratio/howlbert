"""Seasonal Clan Gathering at Fourtrees (Warrior Cats)."""

from __future__ import annotations

import sqlite3

import database as db
from config import CAT_GATHERING_MOOD, CAT_GATHERING_STANDING, CAT_GATHERING_UNITY

GATHERING_BY_SEASON: dict[str, tuple[str, str]] = {
    "spring": (
        "Newleaf Gathering",
        "The four Clans meet at **Fourtrees** under truce; deputies speak while warriors keep the peace.",
    ),
    "summer": (
        "Greenleaf Gathering",
        "Heat shimmers over **Fourtrees**; leaders share prey news and border warnings.",
    ),
    "autumn": (
        "Leaf-fall Gathering",
        "Leaves rustle at **Fourtrees**; medicine cats trade herb lore across Clan lines.",
    ),
    "winter": (
        "Leaf-bare Gathering",
        "Frost grips **Fourtrees**; Clans declare truce while snow buries the Thunderpath.",
    ),
}


def apply_gathering_on_season_change(
    conn: sqlite3.Connection,
    guild_id: int,
    season: str,
    day: int,
) -> list[str]:
    """On season rollover: announce Gathering; bonus dens with active cat treaties."""
    title, flavor = GATHERING_BY_SEASON.get(
        season,
        ("Clan Gathering", "The four Clans gather at **Fourtrees** under the warrior code."),
    )
    lines = [f"**{title}** — {flavor}"]

    pack_rows = conn.execute(
        """
        SELECT DISTINCT p.id, p.name
        FROM packs p
        JOIN pack_cat_pacts cp ON cp.pack_id = p.id
        WHERE cp.guild_id = ? AND cp.status = 'active'
        """,
        (guild_id,),
    ).fetchall()
    rewarded: list[str] = []
    for pack in pack_rows:
        pack_id = int(pack["id"])
        pacts = db.list_active_cat_pacts(guild_id, pack_id)
        if not pacts:
            continue
        db.adjust_pack_unity(pack_id, CAT_GATHERING_UNITY)
        members = conn.execute(
            """
            SELECT discord_id, id FROM users
            WHERE pack_id = ? AND condition NOT IN ('dead', 'dying')
            """,
            (pack_id,),
        ).fetchall()
        for member in members:
            db.adjust_wolf_standing(int(member["discord_id"]), CAT_GATHERING_STANDING)
            db.adjust_mood(int(member["id"]), CAT_GATHERING_MOOD)
        clans = ", ".join(p["clan_name"] for p in pacts[:2])
        rewarded.append(
            f"**{pack['name']}** observed with **{clans}** "
            f"(+{CAT_GATHERING_UNITY} unity · members +{CAT_GATHERING_STANDING} standing · +{CAT_GATHERING_MOOD} mood)"
        )

    if rewarded:
        lines.extend(rewarded)
    else:
        lines.append(
            "_No wolf dens hold active Clan treaties; the Gathering passes without your pack at Fourtrees._"
        )
    return lines
