"""Scent marking on pack borders and rival over-marks."""

from __future__ import annotations

import random

import discord

import database as db
from config import GREAT_PACKS
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed

MARK_REFRESH_FLAVORS = (
    "You drag your scent along the border post; the den's claim reads loud and fresh.",
    "Pine sap and wolf musk; your pack's mark renewed for another sunrise.",
    "You circle the stake twice and leave your signature where patrols will read it.",
)

OVER_MARK_FLAVORS = (
    "You spray over **{owner}**'s stale line; a deliberate insult on their ground.",
    "Your musk sits atop **{owner}**'s border mark; every scout will smell the challenge.",
    "A fresh over-mark on **{territory}**; **{owner}** will know someone crossed the line.",
)


def read_marks_for_sniff(pack_key: str, *, guild_id: int, day: int, lookback_days: int = 3) -> list[str]:
    """Recent scent marks readable on the wind for a Great Pack key."""
    since = max(1, day - lookback_days)
    rows = db.get_scent_marks_for_pack(guild_id, pack_key, since_day=since)
    lines: list[str] = []
    for row in rows:
        terr = row["territory_name"] or row["territory_key"]
        age = day - int(row["marked_day"])
        if age <= 0:
            age_note = "fresh this sunrise"
        elif age == 1:
            age_note = "yesterday"
        else:
            age_note = f"{age} sunrises ago"
        marker_pack = GREAT_PACKS.get(row["pack_key"], {}).get("name", row["pack_key"])
        lines.append(f"**{marker_pack}** on **{terr}** ({age_note})")
    return lines


def mark_territory(
    user,
    guild_id: int,
    day: int,
    territory_key: str,
) -> discord.Embed:
    if not user:
        return howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
    if not user["pack_id"]:
        return howlbert_embed(
            "No Pack",
            "Join a Great Pack to mark territory.",
            color=ERROR_COLOR,
        )

    pack = db.get_pack(user["pack_id"])
    if not pack:
        return howlbert_embed("Pack Not Found", "That Great Pack isn't in this den.", color=ERROR_COLOR)

    pack_key = pack["key"] if "key" in pack.keys() and pack["key"] else user["great_pack"]
    if not pack_key or pack_key not in GREAT_PACKS:
        return howlbert_embed(
            "Not a Great Pack",
            "Only the four Great Packs mark shared borders.",
            color=ERROR_COLOR,
        )

    if int(user["last_mark_day"]) >= day:
        return howlbert_embed(
            "Already Marked",
            "You've left scent on the border this sunrise.",
            color=ERROR_COLOR,
        )

    terr = db.get_territory_by_key(guild_id, territory_key)
    if not terr:
        return howlbert_embed(
            "Unknown Territory",
            "Pick a key from `/pack territory`.",
            color=ERROR_COLOR,
        )

    db.update_user(user["discord_id"], last_mark_day=day, wolf_id=user["id"])
    db.upsert_scent_mark(
        guild_id,
        terr["key"],
        pack_key,
        user["id"],
        day,
    )

    owner_id = terr["owner_pack_id"]
    relation_note = ""
    if owner_id and int(owner_id) != int(pack["id"]):
        owner = db.get_pack(int(owner_id))
        owner_name = owner["name"] if owner else "the holder"
        new_standing = db.adjust_pack_relation(guild_id, pack["id"], int(owner_id), -2)
        body = random.choice(OVER_MARK_FLAVORS).format(
            owner=owner_name,
            territory=terr["name"],
        )
        from engine.pack_relations import format_standing_war_flash, relation_effect_text

        relation_note = f"\n\nPack standing with **{owner_name}** **−2** (now **{new_standing}/10**)."
        relation_note += format_standing_war_flash(guild_id, pack["id"], int(owner_id), new_standing)
        relation_note += f"\n_{relation_effect_text(new_standing)}_"
        title = "Rival Over-Mark"
    else:
        body = random.choice(MARK_REFRESH_FLAVORS)
        title = "Border Refreshed"

    embed = howlbert_embed(
        title,
        f"**{terr['name']}** (`{terr['key']}`)\n{body}{relation_note}",
        color=SUCCESS_COLOR if not relation_note else ERROR_COLOR,
    )
    embed.set_footer(text=f"{GREAT_PACKS[pack_key]['name']} scent · sunrise {day}")
    return embed
