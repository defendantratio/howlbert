"""Rite of the Broken Canine; leadership challenge when an Alpha's standing collapses."""

from __future__ import annotations

import json
import random
import sqlite3

from config import WOLF_STANDING_KICK_THRESHOLD
from engine.aging import proficiencies_for_role, sync_role_to_age
from engine.character import attr_modifier, parse_proficiencies
from engine.dice import roll_d20
from engine.pack_leadership import is_pack_alpha, wolf_role_key
from engine.role_restrictions import life_stage
from rpg_rules import ROLE_LABELS

RITE_NAME = "Rite of the Broken Canine"


def _leadership_roll(user) -> tuple[int, dict]:
    from engine.character_traits import trait_check_adjustments

    die = roll_d20()
    mod = attr_modifier(int(user["attr_str"]))
    trait_mod, _ = trait_check_adjustments(
        user, ("attr_cha",), skill_key="intimidation", skill_label="Intimidation"
    )
    total = die + mod + trait_mod
    return total, {"die": die, "mod": mod, "prof": trait_mod, "total": total}


def _resolve_bout(a, b) -> tuple[sqlite3.Row, str]:
    a_total, a_detail = _leadership_roll(a)
    b_total, b_detail = _leadership_roll(b)
    if a_detail["die"] == 20 and b_detail["die"] != 20:
        winner, loser = a, b
        note = " (critical)"
    elif b_detail["die"] == 20 and a_detail["die"] != 20:
        winner, loser = b, a
        note = " (critical)"
    elif a_detail["die"] == 1 and b_detail["die"] != 1:
        winner, loser = b, a
        note = " (fumble)"
    elif b_detail["die"] == 1 and a_detail["die"] != 1:
        winner, loser = a, b
        note = " (fumble)"
    elif a_total >= b_total:
        winner, loser = a, b
        note = ""
    else:
        winner, loser = b, a
        note = ""
    line = (
        f"**{a['wolf_name']}** {a_total} vs **{b['wolf_name']}** {b_total}{note} "
        f"- **{winner['wolf_name']}** advances."
    )
    return winner, line


def is_eligible_challenger(user, *, incumbent_id: int) -> bool:
    if user["condition"] in ("dead", "dying"):
        return False
    if life_stage(user) == "pup" or wolf_role_key(user) == "pup":
        return False
    if int(user["id"]) == incumbent_id:
        return True
    return int(user["standing"]) > WOLF_STANDING_KICK_THRESHOLD


def _single_elimination_bracket(fighters: list) -> tuple[sqlite3.Row, list[str]]:
    logs: list[str] = []
    pool = list(fighters)
    random.shuffle(pool)
    while len(pool) > 1:
        next_round: list = []
        idx = 0
        while idx < len(pool):
            if idx + 1 >= len(pool):
                next_round.append(pool[idx])
                break
            winner, line = _resolve_bout(pool[idx], pool[idx + 1])
            logs.append(line)
            next_round.append(winner)
            idx += 2
        pool = next_round
    return pool[0], logs


def _install_pack_alpha(conn: sqlite3.Connection, wolf_id: int, pack_id: int) -> None:
    user = conn.execute("SELECT * FROM users WHERE id = ?", (wolf_id,)).fetchone()
    if not user:
        return
    for row in conn.execute(
        "SELECT id, age_months, wolf_role FROM users WHERE pack_id = ? AND wolf_role = 'alpha' AND id != ?",
        (pack_id, wolf_id),
    ).fetchall():
        new_role = sync_role_to_age(int(row["age_months"]), "hunter")
        profs = proficiencies_for_role(new_role)
        conn.execute(
            "UPDATE users SET wolf_role = ?, skill_proficiencies = ? WHERE id = ?",
            (new_role, profs, row["id"]),
        )
    age = int(user["age_months"]) if "age_months" in user.keys() else 24
    profs = proficiencies_for_role("alpha")
    conn.execute(
        """
        UPDATE users
        SET wolf_role = 'alpha', skill_proficiencies = ?, standing = 0
        WHERE id = ?
        """,
        (profs, wolf_id),
    )
    conn.execute(
        "UPDATE packs SET alpha_id = ? WHERE id = ?",
        (user["discord_id"], pack_id),
    )


def run_broken_canine_rite(
    conn: sqlite3.Connection,
    *,
    pack_id: int,
    incumbent_wolf_id: int,
    triggered_day: int,
) -> dict:
    """
    Run the full rite immediately. Returns summary dict with winner, log lines, and outcome.
    Caller must hold conn; standing for incumbent is already at/below kick threshold.
    """
    import database as db

    incumbent = conn.execute("SELECT * FROM users WHERE id = ?", (incumbent_wolf_id,)).fetchone()
    pack = conn.execute("SELECT * FROM packs WHERE id = ?", (pack_id,)).fetchone()
    if not incumbent or not pack:
        return {"ok": False, "reason": "missing_pack_or_wolf"}

    members = conn.execute(
        """
        SELECT * FROM users
        WHERE pack_id = ? AND condition NOT IN ('dead', 'dying')
        ORDER BY standing DESC, created_at ASC
        """,
        (pack_id,),
    ).fetchall()
    eligible = [m for m in members if is_eligible_challenger(m, incumbent_id=incumbent_wolf_id)]
    logs: list[str] = [
        f"**{RITE_NAME}**; **{incumbent['wolf_name']}**'s standing broke. "
        "The pack gathers for a leadership challenge."
    ]

    if len(eligible) <= 1:
        winner = incumbent
        logs.append("No other eligible wolves; the Alpha keeps the den.")
    else:
        winner, bout_logs = _single_elimination_bracket(eligible)
        logs.extend(bout_logs)

    winner_role = ROLE_LABELS.get(winner["wolf_role"], winner["wolf_role"])
    if int(winner["id"]) == int(incumbent_wolf_id):
        conn.execute("UPDATE users SET standing = 0 WHERE id = ?", (incumbent_wolf_id,))
        logs.append(f"**{winner['wolf_name']}** wins the rite and **keeps the Alpha's seat** (standing restored).")
        outcome = "incumbent_retained"
    else:
        db._expel_wolf_from_pack_conn(conn, incumbent_wolf_id, reset_standing=True)
        _install_pack_alpha(conn, int(winner["id"]), pack_id)
        logs.append(
            f"**{winner['wolf_name']}** ({winner_role}) wins; **new Alpha**. "
            f"**{incumbent['wolf_name']}** is cast out."
        )
        outcome = "new_alpha"

    conn.execute(
        """
        INSERT INTO broken_canine_rites (
            pack_id, incumbent_wolf_id, winner_wolf_id, log_json, outcome, triggered_day, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pack_id,
            incumbent_wolf_id,
            int(winner["id"]),
            json.dumps(logs),
            outcome,
            triggered_day,
            db.utcnow(),
        ),
    )
    return {
        "ok": True,
        "outcome": outcome,
        "winner_name": winner["wolf_name"],
        "incumbent_name": incumbent["wolf_name"],
        "log": logs,
        "pack_name": pack["name"],
    }


def maybe_trigger_broken_canine_rite(
    conn: sqlite3.Connection,
    user: sqlite3.Row,
    *,
    old_standing: int,
    new_standing: int,
    triggered_day: int = 0,
) -> dict | None:
    """If this wolf is the Alpha and would be cast out, run the rite instead."""
    if new_standing > WOLF_STANDING_KICK_THRESHOLD or not user["pack_id"]:
        return None
    pack = conn.execute("SELECT * FROM packs WHERE id = ?", (user["pack_id"],)).fetchone()
    if not pack or not is_pack_alpha(user, pack):
        return None
    if old_standing <= WOLF_STANDING_KICK_THRESHOLD:
        return None
    return run_broken_canine_rite(
        conn,
        pack_id=int(user["pack_id"]),
        incumbent_wolf_id=int(user["id"]),
        triggered_day=triggered_day,
    )


def format_rite_summary(rite: dict) -> str:
    return "\n".join(rite.get("log", []))


def standing_expulsion_note(kick: str, pack_id: int | None) -> str | None:
    """User-facing note when standing adjustment expels or triggers the rite."""
    if kick == "kicked":
        return "**Cast out**; your standing fell too low."
    if kick != "broken_rite" or not pack_id:
        return None
    import json

    import database as db

    row = db.get_latest_broken_canine_rite(pack_id)
    if not row:
        return f"\n\n**{RITE_NAME}**; the pack fought for leadership."
    logs = json.loads(row["log_json"])
    return "\n\n" + "\n".join(logs)
