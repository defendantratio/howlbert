"""Scent marking on pack borders and rival over-marks."""

from __future__ import annotations

import random

import discord

import database as db
from config import GREAT_PACKS
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from engine.factions import faction_name, is_faction

MARK_REFRESH_FLAVORS = (
    "you drag your scent along the border post; the den's claim reads loud and fresh.",
    "pine sap and wolf musk; your pack's mark renewed for another sunrise.",
    "You circle the stake twice and leave your signature where patrols will read it.",
)

OVER_MARK_FLAVORS = (
    "you spray over **{owner}**'s stale line; a deliberate insult on their ground.",
    "your musk sits atop **{owner}**'s border mark; every scout will smell the challenge.",
    "A fresh over-mark on **{territory}**; **{owner}** will know someone crossed the line.",
)


HOME_TURF_MARK_WINDOW_DAYS = 3
HOME_TURF_HUNT_MULT = 1.10


RAIN_MARK_WASHOUT_WEATHER = frozenset({"rain", "storm", "thunderstorm", "sleet"})


def home_turf_hunt_bonus(
    pack_id: int | None,
    pack_key: str | None,
    guild_id: int | None,
    day: int,
    *,
    weather: str | None = None,
    territory: str | None = None,
) -> tuple[float, str]:
    """
    +10% hunt bones when hunting ground your own pack both owns and has
    freshly marked (within HOME_TURF_MARK_WINDOW_DAYS); rewards holding and
    maintaining territory instead of treating /pack territory as cosmetic.
    Heavy rain washes scent out faster, shrinking that window.
    If `territory` is given, only that specific ground counts (the hunter chose
    where to hunt); otherwise any owned/marked ground qualifies.
    Returns (multiplier, note); multiplier is 1.0 / note is "" when no bonus.
    """
    if not pack_id or not pack_key or not guild_id or day <= 0:
        return 1.0, ""
    territories = db.get_territories(guild_id)
    owned_keys = {t["key"] for t in territories if t["owner_pack_id"] == pack_id}
    if territory:
        owned_keys &= {territory}
    if not owned_keys:
        return 1.0, ""
    window = HOME_TURF_MARK_WINDOW_DAYS
    if weather in RAIN_MARK_WASHOUT_WEATHER:
        window = max(1, window - 1)
    since = max(1, day - window)
    marks = db.get_scent_marks_for_pack(guild_id, pack_key, since_day=since)
    if not any(m["territory_key"] in owned_keys for m in marks):
        return 1.0, ""
    pct = int(round((HOME_TURF_HUNT_MULT - 1.0) * 100))
    return HOME_TURF_HUNT_MULT, f"home turf (fresh mark on owned ground): +{pct}% hunt bones"


ALLIED_TERRITORY_HUNT_MULT = 1.05


def allied_territory_hunt_bonus(
    pack_id: int | None, guild_id: int | None, *, territory: str | None = None
) -> tuple[float, str]:
    """
    +5% hunt bones when your pack holds an active alliance or hunting_rights
    treaty with the pack that owns ground you're hunting on; hunting_rights
    is supposed to mean real access to a rival's territory, not just flavor.
    If `territory` is given, only that specific ground qualifies.
    Returns (multiplier, note); multiplier is 1.0 / note is "" when no bonus.
    """
    if not pack_id or not guild_id:
        return 1.0, ""
    treaties = db.list_active_wolf_treaties(guild_id, pack_id)
    granted_pack_ids = {
        int(t["other_pack_id"]) for t in treaties if t["pact_type"] in ("alliance", "hunting_rights")
    }
    if not granted_pack_ids:
        return 1.0, ""
    territories = db.get_territories(guild_id)
    if territory:
        territories = [t for t in territories if t["key"] == territory]
    if not any(t["owner_pack_id"] in granted_pack_ids for t in territories):
        return 1.0, ""
    pct = int(round((ALLIED_TERRITORY_HUNT_MULT - 1.0) * 100))
    return ALLIED_TERRITORY_HUNT_MULT, f"hunting rights with an ally: +{pct}% hunt bones"


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
        marker_name = row["marker_wolf_name"] if "marker_wolf_name" in row.keys() and row["marker_wolf_name"] else None
        who = f"**{marker_name}** of **{marker_pack}**" if marker_name else f"**{marker_pack}**"
        lines.append(f"{who} on **{terr}** ({age_note})")
    return lines


def mark_territory(
    user,
    guild_id: int,
    day: int,
    territory_key: str,
) -> discord.Embed:
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    if not user["pack_id"]:
        return howlbert_embed(
            "no pack",
            "join a great pack to mark territory.",
            color=ERROR_COLOR,
        )

    pack = db.get_pack(user["pack_id"])
    if not pack:
        return howlbert_embed("pack not found", "that great pack isn't in this den.", color=ERROR_COLOR)

    pack_key = pack["key"] if "key" in pack.keys() and pack["key"] else user["great_pack"]
    if not pack_key or not is_faction(pack_key):
        return howlbert_embed(
            "not a great pack",
            "only the four great packs mark shared borders.",
            color=ERROR_COLOR,
        )

    if int(user["last_mark_day"]) >= day:
        return howlbert_embed(
            "already marked",
            "you've left scent on the border this sunrise.",
            color=ERROR_COLOR,
        )

    terr = db.get_territory_by_key(guild_id, territory_key)
    if not terr:
        return howlbert_embed(
            "unknown territory",
            "pick a key from `/pack territory`.",
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

        relation_note = f"\n\npack standing with **{owner_name}** **−2** (now **{new_standing}/10**)."
        relation_note += format_standing_war_flash(guild_id, pack["id"], int(owner_id), new_standing)
        relation_note += f"\n_{relation_effect_text(new_standing)}_"
        title = "rival over-mark"
    elif not owner_id:
        claimed = db.claim_unowned_territory(int(terr["id"]), int(pack["id"]))
        if claimed:
            body = (
                f"unclaimed ground; your scent is the only claim on **{terr['name']}** now. "
                "it's yours until another pack wins it in a war."
            )
            title = "territory claimed"
        else:
            # lost a race to another wolf claiming it the same moment; just a refresh.
            body = random.choice(MARK_REFRESH_FLAVORS)
            title = "border refreshed"
    else:
        body = random.choice(MARK_REFRESH_FLAVORS)
        title = "border refreshed"

    embed = howlbert_embed(
        title,
        f"**{terr['name']}** (`{terr['key']}`)\n{body}{relation_note}",
        color=SUCCESS_COLOR if not relation_note else ERROR_COLOR,
    )
    embed.set_footer(text=f"{faction_name(pack_key)} scent · sunrise {day}")
    return embed
