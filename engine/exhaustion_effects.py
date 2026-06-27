"""Exhaustion tiers; hunt penalties, HP cap, activity blocks, rollover death."""



from __future__ import annotations



import sqlite3



from config import MOOD_LOW_THRESHOLD

from engine.mood import user_mood



EXHAUSTION_MAX = 6





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

    if user_exhaustion(user) >= 4:

        return max(1, base // 2)

    return base





def exhaustion_activity_block(user) -> str | None:

    ex = user_exhaustion(user)

    if ex >= 5:

        return (

            f"**exhaustion {ex}/{EXHAUSTION_MAX}**; you cannot move. "

            "rest, eat, and recover before hunting or ranging out."

        )

    return None





def exhaustion_hunt_multiplier(exhaustion: int) -> float:

    """level 2+: speed halved → reduced hunt payout."""

    if exhaustion >= 2:

        return 0.5

    return 1.0





def apply_exhaustion_hunt_penalty(amount: int, exhaustion: int) -> tuple[int, str]:

    if amount <= 0 or exhaustion < 2:

        return amount, ""

    mult = exhaustion_hunt_multiplier(exhaustion)

    reduced = max(0, int(amount * mult))

    note = f"exhaustion {exhaustion}; speed halved, **−50%** hunt bones."

    return reduced, note





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

    """Exhaustion 6: death at sunrise."""
    import database as db

    rows = conn.execute(

        """

        SELECT id, wolf_name, discord_id, exhaustion

        FROM users

        WHERE condition NOT IN ('dead', 'dying') AND exhaustion >= ?

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

        WHERE condition NOT IN ('dead') AND exhaustion >= 4

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

