"""Automatic wolf journal; major life events are logged without player input."""

from __future__ import annotations

import database as db
from config import GREAT_PACKS, LONER_KEY, ROGUE_KEY
from engine.factions import faction_name, is_faction


def _pack_label(key: str | None) -> str:
    if not key:
        return "no pack"
    if key == LONER_KEY:
        return "lone wolf"
    if key == ROGUE_KEY:
        return "rogue"
    if is_faction(key):
        return faction_name(key)
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


_ARRIVAL_SUMMARIES = {
    "bold_arrival": "strode into the den head-high; the pack took notice.",
    "quiet_arrival": "slipped into the den without a sound; learned the den's rhythms before anyone learned their name.",
    "wary_arrival": "came in half-starved and watchful; carried every scar of the road that led here.",
    "bold_birth": "came into the litter loud and already fighting for space.",
    "quiet_birth": "came into the litter small and still; took the world in before making a sound.",
    "wary_birth": "came into the litter faint-breathed and fragile; survival was the first lesson.",
}


def log_arrival(wolf_id: int, wolf_name: str, arrival_key: str) -> None:
    summary = _ARRIVAL_SUMMARIES.get(arrival_key, f"arrived ({arrival_key}).")
    _write(wolf_id, "arrival", f"**{wolf_name}** {summary}")


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
    _write(wolf_id, key, f"{verb}; **{wolf_name}** is blooded.")


def log_stabilized(wolf_id: int, wolf_name: str) -> None:
    _write(wolf_id, "stabilized", f"**{wolf_name}** clawed back from the brink and stabilized.")


def log_surgery(wolf_id: int, wolf_name: str, procedure: str, *, success: bool) -> None:
    verb = "survived" if success else "did not survive"
    _write(wolf_id, "surgery", f"**{wolf_name}** {verb} a **{procedure}** surgery.")


def log_rivalry_milestone(wolf_id: int, wolf_name: str, rival_name: str, tier_label: str) -> None:
    _write(wolf_id, "rivalry", f"**{wolf_name}**'s feud with **{rival_name}** has become a **{tier_label}**.")


def log_trained(wolf_id: int, wolf_name: str) -> None:
    _write(wolf_id, "trained", f"**{wolf_name}**'s training is complete; the lessons stuck.")


def log_achievement(
    wolf_id: int,
    wolf_name: str,
    title: str,
    *,
    guild_id: int | None = None,
    day: int | None = None,
) -> None:
    _write(
        wolf_id,
        "achievement",
        f"**{wolf_name}** earned the **{title}** trophy.",
        guild_id=guild_id,
        day=day,
    )


def log_quest_complete(
    wolf_id: int, wolf_name: str, title: str, *, reward_bones: int, standing_reward: int
) -> None:
    extra = f" (+{standing_reward} standing)" if standing_reward else ""
    _write(
        wolf_id,
        "quest_complete",
        f"**{wolf_name}** finished **{title}**; +{reward_bones} bones{extra}.",
    )


def log_raid(
    wolf_id: int,
    wolf_name: str,
    victim_pack_name: str,
    *,
    stolen: int = 0,
    caught: bool = False,
    guild_id: int | None = None,
    day: int | None = None,
    loot_label: str | None = None,
) -> None:
    """loot_label overrides the bones-treasury wording for food/herb raids
    (e.g. "a hare carcass" or "3x yarrow") while keeping the same journal key."""
    target = loot_label or "treasury"
    if caught:
        summary = f"**{wolf_name}** was caught raiding **{victim_pack_name}**'s {target}."
        key = "raid_caught"
    elif loot_label:
        summary = f"**{wolf_name}** raided **{victim_pack_name}**'s den reserve ({loot_label})."
        key = "raid_success"
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




def _journal_entry_tier(event_key: str) -> int:
    if event_key.startswith("lore:"):
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
            lines.append("_**earlier life; den records on file**_")
        last_tier = tier
        day = row["day"]
        prefix = f"**day {day}** · " if day is not None else ""
        lines.append(f"✦ {prefix}{row['summary']}")
    return lines


def chunk_journal_lines(lines: list[str], *, max_chars: int = 3900) -> list[str]:
    if not lines:
        return ["_no journal entries yet; life events are recorded automatically._"]
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


def format_notable_lines(wolf_id: int, *, limit: int = 5) -> list[str]:
    """
    A handful of the wolf's own /proxy speech, picked for length (the lines
    that read like they mattered), so the journal reads like a character's
    history instead of only mechanical milestones.
    """
    rows = db.get_proxy_message_log(wolf_id, limit=50)
    if not rows:
        return []
    longest = sorted(rows, key=lambda r: len(r["content"]), reverse=True)[:limit]
    longest.sort(key=lambda r: r["id"])
    lines = []
    for row in longest:
        text = row["content"]
        if len(text) > 200:
            text = text[:197] + "…"
        lines.append(f'_"{text}"_')
    return lines


def format_journal_embed_chunks(wolf_id: int, *, limit: int = 200) -> list[str]:
    lines = format_journal_bullet_lines(wolf_id, limit=limit)
    notable = format_notable_lines(wolf_id)
    if notable:
        lines = lines + ["", "_**in their own words**_"] + notable
    return chunk_journal_lines(lines)
