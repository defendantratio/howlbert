"""Hunger, thirst, and starvation death saves."""

from __future__ import annotations

import sqlite3

from config import NEEDS_SURVIVAL_RESTORE
from engine.death_saves import roll_death_save
from engine.hunger import hunger_activity_block
from engine.thirst import thirst_activity_block


def apply_hp_damage(user, amount: int) -> tuple[int, list[str]]:
    """Reduce HP; at 0 enter dying (death saves) and roll near-death trauma."""
    if not user or amount <= 0:
        return 0, []
    import database as db

    extras: list[str] = []
    cond = user["condition"] if "condition" in user.keys() else "healthy"
    new_hp = max(0, int(user["hp"]) - amount)
    wolf_id = user["id"] if "id" in user.keys() else None
    db.set_user_conditions(user["discord_id"], wolf_id=wolf_id, hp=new_hp)
    if new_hp == 0 and cond not in ("dead", "dying"):
        db.enter_dying_state(user["discord_id"])
        extras.append(
            "You collapse; roll **`/medic action:deathsaves`** "
            "or ask a Medic for **`/medic action:stabilize`**."
        )
        from engine.chronic_conditions import try_near_death_mental_trauma

        fresh = db.get_user_by_id(wolf_id) if wolf_id else db.get_user(user["discord_id"])
        if fresh:
            trauma = try_near_death_mental_trauma(fresh)
            if trauma:
                extras.append(f"**mind fracture:** {trauma}")
    return amount, extras


def vitals_response_footer(user, *, default: str = "") -> str:
    """embed footer after hazard/combat damage; highlights dying state."""
    hp = int(user["hp"]) if user and "hp" in user.keys() else 1
    cond = user["condition"] if user and "condition" in user.keys() else "healthy"
    if hp <= 0 or cond == "dying":
        return (
            "you are **dying** · `/medic action:deathsaves` or medic "
            "`/medic action:stabilize` · `/vitals action:condition`"
        )
    if default:
        return default
    return "/vitals action:condition · `/medic action:treat`"


def living_wolf_block(user) -> str | None:
    cond = user["condition"] if "condition" in user.keys() else "healthy"
    if cond == "dead":
        return (
            "your wolf has died. `/bones action:use item:revive` (same wolf) or "
            "`/bones action:use item:reincarnation new_name:<name>` (new name, same stats) from ko-fi, "
            "or `/switchwolf` / `/register` / `/rpg action:delete confirm:DELETE`."
        )
    if cond == "dying":
        return (
            "you are **dying**; roll **`/medic action:deathsaves`** (con save) or ask a medic for **`/medic action:stabilize`**."
        )
    return None


def vitals_activity_block(user) -> str | None:
    block = living_wolf_block(user)
    if block:
        return block
    from engine.exhaustion_effects import exhaustion_activity_block

    block = exhaustion_activity_block(user)
    if block:
        return block
    block = hunger_activity_block(user)
    if block:
        return block
    return thirst_activity_block(user)


def full_activity_block(user, day: int = 0, *, action: str = "hunt") -> str | None:
    """Vitals (living, exhaustion 5, hunger/thirst crisis) plus critical mood."""
    from engine.injury_effects import bone_rest_activity_block, has_paralysis, hunt_blocked_by_injury
    from engine.mental_effects import field_activity_block, mental_activity_block

    block = mental_activity_block(user)
    if block:
        return block
    from engine.herb_buffs import sedated_blocks_activity

    game_day = day
    rest_day = int(user["last_rest_day"]) if "last_rest_day" in user.keys() else 0
    if sedated_blocks_activity(user, rest_day):
        return (
            "**sedated**; valerian or poppy holds you in deep rest. "
            "no hunting, tracking, or ranging until next sunrise."
        )
    block = bone_rest_activity_block(user, day=rest_day)
    if block:
        return block
    block = field_activity_block(user)
    if block:
        return block
    if has_paralysis(user):
        block = hunt_blocked_by_injury(user)
        if block:
            return block
    block = vitals_activity_block(user)
    if block:
        return block
    from engine.mood import mood_activity_block
    from engine.quarantine import quarantine_activity_block

    block = quarantine_activity_block(user)
    if block:
        return block
    from engine.pregnancy import pregnancy_activity_block

    if game_day > 0:
        block = pregnancy_activity_block(user, action, game_day)
        if block:
            return block
    return mood_activity_block(user)


def _needs_cause(hunger: int, thirst: int) -> str:
    starved = int(hunger) <= 0
    parched = int(thirst) <= 0
    if starved and parched:
        return "starvation and thirst"
    if starved:
        return "starvation"
    return "thirst"


def _stabilize_wolf_conn(conn: sqlite3.Connection, wolf_id: int) -> None:
    conn.execute(
        """
        UPDATE users
        SET hp = 1, condition = 'healthy',
            death_save_round = 0, death_save_fails = 0, death_save_successes = 0,
            hunger = CASE WHEN hunger <= 0 THEN ? ELSE hunger END,
            thirst = CASE WHEN thirst <= 0 THEN ? ELSE thirst END
        WHERE id = ?
        """,
        (NEEDS_SURVIVAL_RESTORE, NEEDS_SURVIVAL_RESTORE, wolf_id),
    )


def _enter_needs_dying_conn(conn: sqlite3.Connection, wolf_id: int) -> None:
    conn.execute(
        """
        UPDATE users
        SET hp = 0, condition = 'dying', death_save_round = 1,
            death_save_fails = 0, death_save_successes = 0
        WHERE id = ?
        """,
        (wolf_id,),
    )


def _apply_death_save_conn(
    conn: sqlite3.Connection,
    user: sqlite3.Row,
    *,
    cause: str = "failed death saves",
    guild_id: int | None = None,
    day: int | None = None,
) -> str:
    """Run one death save on conn. Returns stabilized | died | continue."""
    import database as db

    result = roll_death_save(user)
    wolf_id = user["id"]
    if result.get("consume_fields"):
        fields = result["consume_fields"]
        if fields:
            sets = ", ".join(f"{k} = ?" for k in fields)
            conn.execute(
                f"update users set {sets} where id = ?",
                (*fields.values(), wolf_id),
            )

    if result.get("nat20"):
        _stabilize_wolf_conn(conn, wolf_id)
        return "stabilized"

    if not result["success"]:
        db.mark_wolf_dead(user["id"], cause, conn=conn, guild_id=guild_id, day=day)
        return "died"

    round_num = int(user["death_save_round"]) if user["death_save_round"] else 1
    if round_num >= 3:
        _stabilize_wolf_conn(conn, wolf_id)
        return "stabilized"

    conn.execute(
        """
        UPDATE users
        SET death_save_round = ?, death_save_successes = ?
        WHERE id = ?
        """,
        (round_num + 1, round_num, wolf_id),
    )
    return "continue"


def apply_needs_exhaustion_on_rollover(conn: sqlite3.Connection) -> list[dict]:
    """
    after hunger/thirst decay: +1 exhaustion per sunrise for each vital below the low threshold.
    long rest (−1 exhaustion) runs before decay, so neglected wolves can still climb the track.
    """
    from config import (
        HUNGER_LOW_THRESHOLD,
        NEEDS_EXHAUSTION_GAIN,
        THIRST_LOW_THRESHOLD,
    )

    rows = conn.execute(
        """
        SELECT id, wolf_name, discord_id, hunger, thirst, exhaustion, condition,
               hunger_exhaustion_skip, march_exhaustion_skip
        FROM users
        WHERE condition NOT IN ('dead', 'dying')
        """
    ).fetchall()

    notes: list[dict] = []
    for row in rows:
        gain = 0
        causes: list[str] = []
        skip_hunger = int(row["hunger_exhaustion_skip"]) if "hunger_exhaustion_skip" in row.keys() else 0
        if int(row["hunger"]) < HUNGER_LOW_THRESHOLD:
            if skip_hunger:
                conn.execute(
                    "UPDATE users SET hunger_exhaustion_skip = 0 WHERE id = ?",
                    (row["id"],),
                )
            else:
                gain += NEEDS_EXHAUSTION_GAIN
                causes.append("hunger")
        if int(row["thirst"]) < THIRST_LOW_THRESHOLD:
            gain += NEEDS_EXHAUSTION_GAIN
            causes.append("thirst")
        if gain:
            from engine.exhaustion_effects import consume_march_exhaustion_skip

            gain, burnet = consume_march_exhaustion_skip(conn, row, gain)
            if burnet and not gain:
                continue
        if not gain:
            continue
        old_ex = int(row["exhaustion"]) if row["exhaustion"] is not None else 0
        new_ex = min(6, old_ex + gain)
        if new_ex == old_ex:
            continue
        conn.execute("UPDATE users SET exhaustion = ? WHERE id = ?", (new_ex, row["id"]))
        cause_label = " and ".join(causes)
        notes.append(
            {
                "wolf_name": row["wolf_name"],
                "discord_id": row["discord_id"],
                "cause": cause_label,
                "old_exhaustion": old_ex,
                "new_exhaustion": new_ex,
            }
        )
    return notes


def apply_needs_crisis_on_rollover(
    conn: sqlite3.Connection,
    *,
    guild_id: int | None = None,
    day: int | None = None,
) -> dict:
    """
    Wolves at 0 hunger or thirst collapse into dying (death saves) instead of instant death.
    Wolves already dying from depleted vitals get one automatic death save each sunrise.
    """
    collapses: list[dict] = []
    deaths: list[dict] = []
    stabilized: list[dict] = []

    already_dying = {
        row["id"]
        for row in conn.execute("SELECT id FROM users WHERE condition = 'dying'").fetchall()
    }

    new_rows = conn.execute(
        """
        SELECT id, discord_id, wolf_name, hunger, thirst
        FROM users
        WHERE condition NOT IN ('dead', 'dying')
          AND (hunger <= 0 OR thirst <= 0)
        """
    ).fetchall()

    just_collapsed: set[int] = set()
    for row in new_rows:
        cause = _needs_cause(row["hunger"], row["thirst"])
        _enter_needs_dying_conn(conn, row["id"])
        just_collapsed.add(row["id"])
        collapses.append(
            {
                "wolf_name": row["wolf_name"],
                "discord_id": row["discord_id"],
                "cause": cause,
            }
        )

    for wolf_id in already_dying:
        if wolf_id in just_collapsed:
            continue
        row = conn.execute("SELECT * FROM users WHERE id = ?", (wolf_id,)).fetchone()
        if not row or row["condition"] != "dying":
            continue
        if int(row["hunger"]) > 0 and int(row["thirst"]) > 0:
            continue
        cause = _needs_cause(row["hunger"], row["thirst"])
        outcome = _apply_death_save_conn(
            conn, row, cause=cause, guild_id=guild_id, day=day
        )
        entry = {
            "wolf_name": row["wolf_name"],
            "discord_id": row["discord_id"],
            "cause": cause,
        }
        if outcome == "died":
            deaths.append(entry)
        elif outcome == "stabilized":
            stabilized.append(entry)

    return {"collapses": collapses, "deaths": deaths, "stabilized": stabilized}


# Legacy name used during migration
apply_needs_deaths_on_rollover = apply_needs_crisis_on_rollover
