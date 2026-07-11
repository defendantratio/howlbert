# exhaustion_effects.py
"""Exhaustion tiers; hunt penalties, HP cap, activity blocks, rollover death."""

from __future__ import annotations

import sqlite3

from config import MOOD_LOW_THRESHOLD


EXHAUSTION_MAX = 10

# Impairment line: at/above this, effective max HP halves (see effective_max_hp);
# can't-move is 8, death at sunrise is EXHAUSTION_MAX (10). Repeated field
# activity alone must never push a wolf past this line in a single application —
# crossing further toward death has to come from other sources.
EXHAUSTION_ACTIVITY_CAP = 6

# Pain exhaustion is a separate 0 to 5 pool from painful injuries and diseases;
# at the cap it overflows into main exhaustion.
PAIN_EXHAUSTION_MAX = 5


def user_pain_exhaustion(user) -> int:
    if not user or "pain_exhaustion" not in user.keys():
        return 0
    try:
        return int(user["pain_exhaustion"] or 0)
    except (TypeError, ValueError):
        return 0


def pain_exhaustion_check_adjustments(user, attr_keys: tuple[str, ...]) -> tuple[int, bool]:
    """Accumulated physical pain impairs checks. Returns (flat_penalty, disadvantage).

    Only physical attributes (str/dex/con) are dulled by pain; a wolf can still
    think and read the pack through it. 3+ pain is a flat penalty; the full pool
    also imposes disadvantage.
    """
    pe = user_pain_exhaustion(user)
    if pe <= 0:
        return 0, False
    if not (set(attr_keys) & {"attr_str", "attr_dex", "attr_con"}):
        return 0, False
    penalty = -1 if pe >= 3 else 0
    if pe >= PAIN_EXHAUSTION_MAX:
        penalty -= 1
    disadvantage = pe >= PAIN_EXHAUSTION_MAX
    return penalty, disadvantage


def pain_exhaustion_hunt_multiplier(user) -> tuple[float, str]:
    """Pain drags on field yield: ~5% per point of pain exhaustion, up to 25%."""
    pe = user_pain_exhaustion(user)
    if pe <= 0:
        return 1.0, ""
    mult = max(0.75, 1.0 - 0.05 * pe)
    pct = int(round((1.0 - mult) * 100))
    return mult, f"pain exhaustion {pe}; the ache slows the hunt (**-{pct}%**)"


def consume_pain_exhaustion_skip(
    conn: sqlite3.Connection, user_row: sqlite3.Row, exhaustion_gain: int
) -> tuple[int, bool]:
    """Meadowsweet; skip the first +1 exhaustion from disease pain this sunrise."""
    if exhaustion_gain <= 0:
        return 0, False
    from engine.herb_buffs import buffs_json, get_buffs

    buffs = get_buffs(user_row)
    if not buffs.pop("pain_exhaustion_skip", None):
        return exhaustion_gain, False
    conn.execute(
        "UPDATE users SET herb_buffs = ? WHERE id = ?",
        (buffs_json(buffs), user_row["id"]),
    )
    return max(0, exhaustion_gain - 1), True


def consume_march_exhaustion_skip(
    conn: sqlite3.Connection, user_row: sqlite3.Row, exhaustion_gain: int
) -> tuple[int, bool]:
    """Burnet; skip the first +1 exhaustion from rollover strain."""
    if exhaustion_gain <= 0:
        return 0, False
    skip = (
        int(user_row["march_exhaustion_skip"])
        if "march_exhaustion_skip" in user_row.keys()
        else 0
    )
    if not skip:
        return exhaustion_gain, False
    conn.execute(
        "UPDATE users SET march_exhaustion_skip = 0 WHERE id = ?",
        (user_row["id"],),
    )
    return max(0, exhaustion_gain - 1), True


def user_exhaustion(user) -> int:
    if not user or "exhaustion" not in user.keys():
        return 0
    return int(user["exhaustion"])


def effective_max_hp(user) -> int:
    base = int(user["max_hp"]) if user and "max_hp" in user.keys() else 11
    if user_exhaustion(user) >= 6:
        return max(1, base // 2)
    return base


def exhaustion_activity_block(user) -> str | None:
    ex = user_exhaustion(user)
    if ex >= 8:
        return (
            f"**exhaustion {ex}/{EXHAUSTION_MAX}**; you cannot move. "
            "rest, eat, and recover before hunting or ranging out."
        )
    return None






def apply_mood_exhaustion_on_rollover(conn: sqlite3.Connection) -> list[dict]:
    from config import NEEDS_EXHAUSTION_GAIN

    rows = conn.execute(
        """
        SELECT id, wolf_name, discord_id, mood, exhaustion, condition, march_exhaustion_skip
        FROM users
        WHERE condition NOT IN ('dead', 'dying')
        """
    ).fetchall()

    notes: list[dict] = []
    for row in rows:
        if int(row["mood"]) >= MOOD_LOW_THRESHOLD:
            continue
        gain = NEEDS_EXHAUSTION_GAIN
        gain, _ = consume_march_exhaustion_skip(conn, row, gain)
        if not gain:
            continue
        old_ex = int(row["exhaustion"]) if row["exhaustion"] is not None else 0
        new_ex = min(EXHAUSTION_MAX, old_ex + gain)
        if new_ex == old_ex:
            continue
        conn.execute("UPDATE users SET exhaustion = ? WHERE id = ?", (new_ex, row["id"]))
        notes.append(
            {
                "wolf_name": row["wolf_name"],
                "discord_id": row["discord_id"],
                "cause": "low mood",
                "old_exhaustion": old_ex,
                "new_exhaustion": new_ex,
            }
        )
    return notes


def apply_exhaustion_death_on_rollover(
    conn: sqlite3.Connection,
    *,
    guild_id: int | None = None,
    day: int | None = None,
) -> list[dict]:
    """Exhaustion at EXHAUSTION_MAX (10): death at sunrise. Dormant (admin-held)
    and inactive wolves are 'away' and exempt, matching the vitals-decay and
    needs-crisis exemptions."""
    import database as db
    from config import AUTO_DORMANT_INACTIVE_DAYS

    _act_cols = (
        "last_hunt_day", "last_work_day", "last_socialize_day", "last_explore_day",
        "last_forage_day", "last_groom_day", "last_sniff_day", "last_fishing_day",
        "last_howl_day", "last_sign_day",
    )
    _last_seen = "MAX(" + ", ".join(f"COALESCE({c}, 0)" for c in _act_cols) + ")"
    if day is not None:
        _active_since = max(0, int(day) - AUTO_DORMANT_INACTIVE_DAYS)
        away_clause = f"AND dormant = 0 AND ({_last_seen} >= {_active_since} OR {int(day)} <= 1)"
    else:
        away_clause = "AND dormant = 0"

    rows = conn.execute(
        f"""
        SELECT id, wolf_name, discord_id, exhaustion
        FROM users
        WHERE condition NOT IN ('dead', 'dying') AND exhaustion >= ?
          {away_clause}
        """,
        (EXHAUSTION_MAX,),
    ).fetchall()

    deaths: list[dict] = []
    for row in rows:
        grief = db.mark_wolf_dead(
            row["id"], "exhaustion", conn=conn, guild_id=guild_id, day=day
        )
        deaths.append(
            {
                "wolf_id": row["id"],
                "wolf_name": row["wolf_name"],
                "discord_id": row["discord_id"],
                "cause": "exhaustion",
                "mate_grief": grief,
            }
        )
    return deaths


def clamp_hp_for_exhaustion_on_rollover(conn: sqlite3.connection) -> None:
    """level 4+ halves effective max hp; clamp current hp if needed."""
    rows = conn.execute(
        """
        SELECT id, hp, max_hp, exhaustion
        FROM users
        WHERE condition NOT IN ('dead') AND exhaustion >= 6
        """
    ).fetchall()
    for row in rows:
        cap = max(1, int(row["max_hp"]) // 2)
        if int(row["hp"]) > cap:
            conn.execute("UPDATE users SET hp = ? WHERE id = ?", (cap, row["id"]))


def reduce_exhaustion(user, amount: int = 1) -> int:
    """Return new exhaustion level."""
    old = user_exhaustion(user)
    return max(0, old - amount)