"""Light seasonal den events on rollover; one random note per pack."""

from __future__ import annotations

import random

import database as db

# (flavor line, optional mechanical effect key)
PACK_EVENT_SPECS: list[tuple[str, str | None]] = [
    ("Border tension; scouts report unfamiliar scent on the ridge.", None),
    ("Den warmth; pups and elders sleep closer tonight.", None),
    ("Stash watch; the food reserve draws curious raccoons.", "raccoon"),
    ("Unity beat; the pack howls together at dusk.", "unity"),
    ("River rise; crossing places run fast after the rain.", None),
    ("Rival wind; scent from a neighboring territory lingers.", None),
    ("Gathering mood; wolves trade stories of last season's hunts.", None),
    ("Thin prey; hunters return early; the den shares smaller meals.", "thin_prey"),
]


def _apply_pack_event_effect(conn, pack_id: int, effect: str | None) -> str:
    """Apply a light mechanical bite; return suffix for den news."""
    if not effect:
        return ""

    if effect == "raccoon":
        row = conn.execute(
            """
            SELECT id, prey_key, uses_left FROM pack_prey_stacks
            WHERE pack_id = ? AND uses_left > 0
            ORDER BY RANDOM() LIMIT 1
            """,
            (pack_id,),
        ).fetchone()
        if not row:
            return " guards held the line; **no theft**."
        from engine.prey_items import prey_meta

        name = prey_meta(row["prey_key"])["name"]
        uses = int(row["uses_left"])
        if uses <= 1:
            conn.execute("DELETE FROM pack_prey_stacks WHERE id = ?", (row["id"],))
        else:
            conn.execute(
                "UPDATE pack_prey_stacks SET uses_left = uses_left - 1 WHERE id = ?",
                (row["id"],),
            )
        return f" a raccoon **stole** a bite of reserve **{name}** (`/pack stash`)."

    if effect == "unity":
        outcome = db.adjust_pack_unity(pack_id, 1)
        if outcome == "dissolved":
            return " the dusk howl couldn't hold the fractured den."
        return " dusk howl; **+1 unity**."

    if effect == "thin_prey":
        row = conn.execute("SELECT treasury FROM packs WHERE id = ?", (pack_id,)).fetchone()
        if not row:
            return ""
        treasury = int(row["treasury"])
        if treasury < 3:
            return ""
        loss = min(8, max(3, treasury // 10))
        if not db.deduct_pack_treasury(pack_id, loss):
            return ""
        return f" shared rations; treasury **−{loss}** bones."

    return ""


def roll_pack_event_for_rollover(pack_id: int, day_number: int) -> str | None:
    """~25% chance per pack per rollover; store last event day to avoid spam."""
    with db.get_db() as conn:
        pack = conn.execute("SELECT * FROM packs WHERE id = ?", (pack_id,)).fetchone()
        if not pack:
            return None
        last = int(pack["last_pack_event_day"]) if "last_pack_event_day" in pack.keys() else 0
        if last >= day_number:
            return None
        if random.random() > 0.25:
            return None
        text, effect = random.choice(PACK_EVENT_SPECS)
        suffix = _apply_pack_event_effect(conn, pack_id, effect)
        conn.execute(
            "UPDATE packs SET last_pack_event_day = ? WHERE id = ?",
            (day_number, pack_id),
        )
        return f"{text}{suffix}"


def collect_pack_event_lines(day_number: int) -> list[str]:
    lines: list[str] = []
    with db.get_db() as conn:
        packs = conn.execute("SELECT id, name FROM packs").fetchall()
    for pack in packs:
        event = roll_pack_event_for_rollover(pack["id"], day_number)
        if event:
            lines.append(f"**{pack['name']}**; {event}")
    return lines
