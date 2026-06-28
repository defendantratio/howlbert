"""Automatic wolf journal; major life events are logged without player input."""

from __future__ import annotations

import database as db
from config import GREAT_PACKS, LONER_KEY, ROGUE_KEY


def _pack_label(key: str | None) -> str:
    if not key:
        return "no pack"
    if key == LONER_KEY:
        return "lone wolf"
    if key == ROGUE_KEY:
        return "rogue"
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
    conn=None,
) -> None:
    if day is None:
        day = _day_for_wolf(wolf_id, guild_id)
    db.add_wolf_journal_entry(
        wolf_id, event_key, summary, day=day, guild_id=guild_id, conn=conn
    )


def log_registered(wolf_id: int, wolf_name: str, affiliation: str | None) -> None:
    pack = _pack_label(affiliation)
    _write(wolf_id, "registered", f"joined the den as **{wolf_name}** ({pack}).")


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
            f"left **{_pack_label(old_pack)}**.",
            guild_id=guild_id,
        )
        return
    if new_pack and new_pack not in (LONER_KEY,):
        if old_pack in (None, LONER_KEY, ROGUE_KEY):
            _write(
                wolf_id,
                "pack_joined",
                f"joined **{_pack_label(new_pack)}**.",
                guild_id=guild_id,
            )
        else:
            _write(
                wolf_id,
                "pack_joined",
                f"moved from **{_pack_label(old_pack)}** to **{_pack_label(new_pack)}**.",
                guild_id=guild_id,
            )


def log_bonded(wolf_a_id: int, wolf_b_id: int) -> None:
    a = db.get_user_by_id(wolf_a_id)
    b = db.get_user_by_id(wolf_b_id)
    if not a or not b:
        return
    line_a = f"bonded with **{b['wolf_name']}**."
    line_b = f"bonded with **{a['wolf_name']}**."
    _write(wolf_a_id, "bonded", line_a)
    _write(wolf_b_id, "bonded", line_b)


def log_blooded(wolf_id: int, wolf_name: str, *, ceremonial: bool = False) -> None:
    key = "rite_blooding" if ceremonial else "blooded"
    verb = "Received the **blooding rite**" if ceremonial else "Earned **blooding** on first kill"
    _write(wolf_id, key, f"{verb} — **{wolf_name}** is blooded.")


def log_raid(
    wolf_id: int,
    wolf_name: str,
    victim_pack_name: str,
    *,
    stolen: int = 0,
    caught: bool = False,
    guild_id: int | None = None,
    day: int | None = None,
) -> None:
    if caught:
        summary = f"**{wolf_name}** was caught raiding **{victim_pack_name}**'s treasury."
        key = "raid_caught"
    else:
        summary = (
            f"**{wolf_name}** raided **{victim_pack_name}**'s treasury "
            f"(**{stolen}** 🦴 stolen)."
        )
        key = "raid_success"
    _write(wolf_id, key, summary, guild_id=guild_id, day=day)


def log_cast_out(
    wolf_id: int,
    wolf_name: str,
    pack_name: str,
    *,
    guild_id: int | None = None,
    day: int | None = None,
) -> None:
    _write(
        wolf_id,
        "cast_out",
        f"**{wolf_name}** was cast out of **{pack_name}** for low standing.",
        guild_id=guild_id,
        day=day,
    )


def log_died(
    wolf_id: int,
    wolf_name: str,
    cause: str,
    *,
    guild_id: int | None = None,
    day: int | None = None,
    conn=None,
    unnamed_pup: bool = False,
) -> None:
    if unnamed_pup:
        # Lore: pups who die before their naming ceremony are not mourned by
        # name; "wind that never howled." No name, no cause, no record kept.
        _write(
            wolf_id,
            "died",
            "an unnamed pup did not survive the first moon; wind that never howled.",
            guild_id=guild_id,
            day=day,
            conn=conn,
        )
        return
    _write(
        wolf_id,
        "died",
        f"**{wolf_name}** died ({cause}).",
        guild_id=guild_id,
        day=day,
        conn=conn,
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


def format_journal_embed_body(wolf_id: int, *, limit: int = 200) -> str:
    chunks = format_journal_embed_chunks(wolf_id, limit=limit)
    return chunks[0] if chunks else "_no journal entries yet — life events are recorded automatically._"


def _journal_entry_tier(event_key: str) -> int:
    if event_key.startswith("lore:") or event_key in ("born", "adopted"):
        return 2
    return 1


def format_journal_bullet_lines(wolf_id: int, *, limit: int = 200) -> list[str]:
    rows = db.list_wolf_journal(wolf_id, limit=limit, chronological=True)
    if not rows:
        return []
    lines: list[str] = []
    last_tier: int | None = None
    for row in rows:
        tier = _journal_entry_tier(str(row["event_key"]))
        if tier == 2 and last_tier != 2:
            lines.append("_**earlier life — den records on file**_")
        last_tier = tier
        day = row["day"]
        prefix = f"**day {day}** · " if day is not None else ""
        lines.append(f"✦ {prefix}{row['summary']}")
    return lines


def chunk_journal_lines(lines: list[str], *, max_chars: int = 3900) -> list[str]:
    if not lines:
        return ["_no journal entries yet — life events are recorded automatically._"]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in lines:
        line_len = len(line) + 1
        if current and current_len + line_len > max_chars:
            chunks.append("\n".join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len
    if current:
        chunks.append("\n".join(current))
    return chunks


def format_journal_embed_chunks(wolf_id: int, *, limit: int = 200) -> list[str]:
    return chunk_journal_lines(format_journal_bullet_lines(wolf_id, limit=limit))
