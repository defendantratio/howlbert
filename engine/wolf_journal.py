"""Automatic wolf journal; major life events are logged without player input."""

from __future__ import annotations

import database as db
from config import GREAT_PACKS, LONER_KEY, ROGUE_KEY


def _pack_label(key: str | None) -> str:
    if not key:
        return "no pack"
    if key == LONER_KEY:
        return "Lone Wolf"
    if key == ROGUE_KEY:
        return "Rogue"
    if key in GREAT_PACKS:
        return GREAT_PACKS[key]["name"]
    return key.replace("_", " ").title()


def _day_for_wolf(wolf_id: int, guild_id: int | None = None) -> int | None:
    if guild_id:
        world = db.get_world(guild_id)
        if world:
            return int(world["day_number"])
    return None


def _write(
    wolf_id: int,
    event_key: str,
    summary: str,
    *,
    day: int | None = None,
    guild_id: int | None = None,
) -> None:
    if day is None:
        day = _day_for_wolf(wolf_id, guild_id)
    db.add_wolf_journal_entry(wolf_id, event_key, summary, day=day, guild_id=guild_id)


def log_registered(wolf_id: int, wolf_name: str, affiliation: str | None) -> None:
    pack = _pack_label(affiliation)
    _write(wolf_id, "registered", f"Joined the den as **{wolf_name}** ({pack}).")


def log_born(
    pup_id: int,
    pup_name: str,
    *,
    mother_name: str | None = None,
    father_name: str | None = None,
    guild_id: int | None = None,
) -> None:
    parents = " and ".join(p for p in (mother_name, father_name) if p) or "the den"
    _write(
        pup_id,
        "born",
        f"**{pup_name}** was born to {parents}.",
        guild_id=guild_id,
    )


def log_pack_change(
    wolf_id: int,
    wolf_name: str,
    old_pack: str | None,
    new_pack: str | None,
    *,
    guild_id: int | None = None,
) -> None:
    if old_pack == new_pack:
        return
    if new_pack in (None, LONER_KEY) and old_pack not in (None, LONER_KEY, ROGUE_KEY):
        _write(
            wolf_id,
            "pack_left",
            f"Left **{_pack_label(old_pack)}**.",
            guild_id=guild_id,
        )
        return
    if new_pack and new_pack not in (LONER_KEY,):
        if old_pack in (None, LONER_KEY, ROGUE_KEY):
            _write(
                wolf_id,
                "pack_joined",
                f"Joined **{_pack_label(new_pack)}**.",
                guild_id=guild_id,
            )
        else:
            _write(
                wolf_id,
                "pack_joined",
                f"Moved from **{_pack_label(old_pack)}** to **{_pack_label(new_pack)}**.",
                guild_id=guild_id,
            )


def log_bonded(wolf_a_id: int, wolf_b_id: int) -> None:
    a = db.get_user_by_id(wolf_a_id)
    b = db.get_user_by_id(wolf_b_id)
    if not a or not b:
        return
    line_a = f"Bonded with **{b['wolf_name']}**."
    line_b = f"Bonded with **{a['wolf_name']}**."
    _write(wolf_a_id, "bonded", line_a)
    _write(wolf_b_id, "bonded", line_b)


def log_blooded(wolf_id: int, wolf_name: str, *, ceremonial: bool = False) -> None:
    key = "rite_blooding" if ceremonial else "blooded"
    verb = "Received the **blooding rite**" if ceremonial else "Earned **blooding** on first kill"
    _write(wolf_id, key, f"{verb} — **{wolf_name}** is blooded.")


def log_died(wolf_id: int, wolf_name: str, cause: str, *, guild_id: int | None = None) -> None:
    _write(
        wolf_id,
        "died",
        f"**{wolf_name}** died ({cause}).",
        guild_id=guild_id,
    )


def log_rite(
    wolf_id: int,
    rite_key: str,
    summary: str,
    *,
    guild_id: int | None = None,
    day: int | None = None,
) -> None:
    _write(wolf_id, rite_key, summary, guild_id=guild_id, day=day)


def format_journal_embed_body(wolf_id: int, *, limit: int = 20) -> str:
    rows = db.list_wolf_journal(wolf_id, limit=limit)
    if not rows:
        return "_No journal entries yet — life events are recorded automatically._"
    lines: list[str] = []
    for row in rows:
        day = row["day"]
        prefix = f"**Day {day}** · " if day is not None else ""
        lines.append(f"{prefix}{row['summary']}")
    return "\n".join(lines)
