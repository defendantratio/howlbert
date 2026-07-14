"""Lone wolf hardship at rollover for packless wolves: loneliness, winter cold
without a den to huddle in, and untended wounds with no denmate or healer."""

from __future__ import annotations

import random
import sqlite3

LONE_WOLF_MOOD_DRAIN = 3
LONE_WOLF_BONDED_DRAIN = 1
LONE_WOLF_SOCIAL_WINDOW_DAYS = 2

# bleeding-type injuries that fester faster without a denmate to tend them.
_LONER_BLEED_INJURIES = frozenset({"deep_gash", "torn_claw", "punctured_paw", "infected_wound"})


def apply_lone_wolf_loneliness_on_rollover(conn: sqlite3.Connection, day: int) -> list[dict]:
    """Drain mood for wolves with no pack. Wolves who socialized recently feel it less."""
    import database as _db

    rows = conn.execute(
        "SELECT id, discord_id, wolf_name, mood, last_socialize_day "
        f"FROM users WHERE pack_id IS NULL AND condition != 'dead' AND {_db.active_wolf_where(day)}"
    ).fetchall()
    notes: list[dict] = []
    for wolf in rows:
        socialized_recently = int(wolf["last_socialize_day"] or 0) >= day - LONE_WOLF_SOCIAL_WINDOW_DAYS
        drain = LONE_WOLF_BONDED_DRAIN if socialized_recently else LONE_WOLF_MOOD_DRAIN
        old_mood = int(wolf["mood"])
        new_mood = max(0, old_mood - drain)
        if new_mood == old_mood:
            continue
        conn.execute("UPDATE users SET mood = ? WHERE id = ?", (new_mood, wolf["id"]))
        notes.append({
            "wolf_name": wolf["wolf_name"],
            "discord_id": wolf["discord_id"],
            "line": f"lone wolf loneliness; mood **−{drain}** (now **{new_mood}**).",
        })
    return notes


def apply_loner_winter_cold_on_rollover(conn: sqlite3.Connection, season: str, day: int) -> list[dict]:
    """No pack to huddle with: packless wolves burn extra hunger in winter and may
    tire from the cold. Away/dormant wolves are exempt."""
    if season != "winter":
        return []
    import database as _db
    from config import LONER_WINTER_HUNGER_EXTRA, LONER_WINTER_EXHAUSTION_CHANCE
    from engine.exhaustion_effects import EXHAUSTION_MAX

    rows = conn.execute(
        "SELECT id, discord_id, wolf_name, hunger, exhaustion FROM users "
        f"WHERE pack_id IS NULL AND condition NOT IN ('dead', 'dying') AND {_db.active_wolf_where(day)}"
    ).fetchall()
    notes: list[dict] = []
    for wolf in rows:
        new_hunger = max(0, int(wolf["hunger"] or 0) - LONER_WINTER_HUNGER_EXTRA)
        fields = {"hunger": new_hunger}
        gained = False
        cur_ex = int(wolf["exhaustion"] or 0)
        if random.random() < LONER_WINTER_EXHAUSTION_CHANCE:
            new_ex = min(EXHAUSTION_MAX, cur_ex + 1)
            if new_ex != cur_ex:
                fields["exhaustion"] = new_ex
                gained = True
        sets = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(f"UPDATE users SET {sets} WHERE id = ?", (*fields.values(), wolf["id"]))
        line = f"no den to huddle in; winter cold gnaws (**−{LONER_WINTER_HUNGER_EXTRA} satiety**"
        line += "; **+1 exhaustion**)." if gained else ")."
        notes.append({"wolf_name": wolf["wolf_name"], "discord_id": wolf["discord_id"], "line": line})
    return notes


def apply_loner_untended_wounds_on_rollover(conn: sqlite3.Connection, day: int) -> list[dict]:
    """No denmate or healer: a packless wolf's untended bleeding wounds sometimes
    fester an extra hp (floored at 1, so it never kills outright). Away/dormant
    wolves exempt."""
    import database as _db
    from config import LONER_BLEED_WORSEN_CHANCE
    from engine.conditions import parse_injuries

    rows = conn.execute(
        "SELECT id, discord_id, wolf_name, hp, active_injuries FROM users "
        "WHERE pack_id IS NULL AND condition NOT IN ('dead', 'dying') "
        "AND active_injuries IS NOT NULL AND active_injuries != '' AND active_injuries != '[]' "
        f"AND {_db.active_wolf_where(day)}"
    ).fetchall()
    notes: list[dict] = []
    for wolf in rows:
        injuries = set(parse_injuries(wolf["active_injuries"]))
        if not (injuries & _LONER_BLEED_INJURIES):
            continue
        if random.random() < LONER_BLEED_WORSEN_CHANCE:
            new_hp = max(1, int(wolf["hp"]) - 1)
            if new_hp != int(wolf["hp"]):
                conn.execute("UPDATE users SET hp = ? WHERE id = ?", (new_hp, wolf["id"]))
                notes.append({
                    "wolf_name": wolf["wolf_name"],
                    "discord_id": wolf["discord_id"],
                    "line": "no denmate to tend the wound; it festers untended (**−1 hp**).",
                })
    return notes
