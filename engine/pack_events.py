"""Light seasonal den events on rollover; one random note per pack."""

from __future__ import annotations

import random

import database as db

PACK_EVENT_TEMPLATES = [
    "Border tension; scouts report unfamiliar scent on the ridge.",
    "Den warmth; pups and elders sleep closer tonight.",
    "Stash watch; the food reserve draws curious raccoons.",
    "Unity beat; the pack howls together at dusk.",
    "River rise; crossing places run fast after the rain.",
    "Rival wind; scent from a neighboring territory lingers.",
    "Gathering mood; wolves trade stories of last season's hunts.",
    "Thin prey; hunters return early; the den shares smaller meals.",
]


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
        text = random.choice(PACK_EVENT_TEMPLATES)
        conn.execute(
            "UPDATE packs SET last_pack_event_day = ? WHERE id = ?",
            (day_number, pack_id),
        )
        return text


def collect_pack_event_lines(day_number: int) -> list[str]:
    lines: list[str] = []
    with db.get_db() as conn:
        packs = conn.execute("SELECT id, name FROM packs").fetchall()
    for pack in packs:
        event = roll_pack_event_for_rollover(pack["id"], day_number)
        if event:
            lines.append(f"**{pack['name']}**; {event}")
    return lines
