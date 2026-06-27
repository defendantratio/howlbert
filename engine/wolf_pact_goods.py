"""Border gifts and barter loot from allied Great Wolf packs."""

from __future__ import annotations

import random

import database as db
from config import GREAT_PACKS

LootKind = str  # prey | herb | amusement | bones

WOLF_PACT_LOOT_BONUS: dict[str, list[tuple[str, str, int]]] = {
    "truce": [("herb", "comfrey", 12), ("bones", "6", 8)],
    "alliance": [("prey", "hare", 14), ("prey", "rabbit", 12)],
    "hunting_rights": [("prey", "fish", 16), ("prey", "vole", 12)],
}

TERRAIN_PREY: dict[str, list[tuple[str, int]]] = {
    "Mountain": [("marmot", 18), ("snowshoe_hare", 16), ("grouse", 10)],
    "Swamp": [("frog", 16), ("vole", 14), ("fish", 12)],
    "Forest": [("vole", 20), ("hare", 16), ("rabbit", 12)],
    "River": [("fish", 24), ("vole", 14), ("frog", 10)],
}


def _pack_table(pack_key: str, pact_type: str) -> list[tuple[str, str, int]]:
    info = GREAT_PACKS.get(pack_key, {})
    table: list[tuple[str, str, int]] = []
    for prey_key, weight in TERRAIN_PREY.get(info.get("terrain", "Forest"), TERRAIN_PREY["Forest"]):
        table.append(("prey", prey_key, weight))
    for herb_key in info.get("starting_herbs", ()):
        table.append(("herb", herb_key, 14))
    table.extend(WOLF_PACT_LOOT_BONUS.get(pact_type, ()))
    return table or [("prey", "vole", 10)]


def receive_loot_count(standing: int, pact_type: str) -> int:
    from config import WOLF_PACT_RECEIVE_MIN_STANDING

    if standing < WOLF_PACT_RECEIVE_MIN_STANDING:
        return 0
    count = 1
    if standing >= 9:
        count += 1
    if pact_type == "alliance":
        count += 1
    if pact_type == "hunting_rights":
        count += 1
    return min(count, 4)


def barter_loot_count(duplicate_items: int) -> int:
    from config import CAT_PACT_BARTER_LOOT_MAX, CAT_PACT_BARTER_PER_DUPES

    if duplicate_items <= 0:
        return 0
    return max(1, min(CAT_PACT_BARTER_LOOT_MAX, duplicate_items // CAT_PACT_BARTER_PER_DUPES))


def roll_wolf_pact_loot(pack_key: str, *, pact_type: str, count: int) -> list[tuple[str, str]]:
    if count <= 0:
        return []
    table = _pack_table(pack_key, pact_type)
    keys = [e[1] for e in table]
    weights = [e[2] for e in table]
    kinds = [e[0] for e in table]
    out: list[tuple[str, str]] = []
    for _ in range(count):
        key = random.choices(keys, weights=weights, k=1)[0]
        idx = keys.index(key)
        out.append((kinds[idx], key))
    return out


def grant_wolf_pact_loot(
    user,
    *,
    guild_id: int,
    day: int,
    entries: list[tuple[str, str]],
) -> list[str]:
    from engine.amusement_storage import grant_amusement
    from engine.herb_storage import grant_fresh_herb
    from engine.prey_storage import grant_prey_carcass
    from herbs import HERBS

    lines: list[str] = []
    for kind, key in entries:
        if kind == "prey":
            grant_prey_carcass(user["id"], key, guild_id=guild_id, acquired_day=day)
            from engine.prey_items import prey_meta

            lines.append(f"**{prey_meta(key)['name']}** → `/food`")
        elif kind == "herb" and key in HERBS:
            item_key, _note = grant_fresh_herb(
                user["id"], herb_key=key, guild_id=guild_id, day=day, user=user
            )
            lines.append(f"**{HERBS[key]['name']}** → `/bones action:inventory` (`{item_key}`)")
        elif kind == "amusement":
            grant_amusement(user["id"], key)
            lines.append(f"toy **{key}** → `/playpen action:toys`")
        elif kind == "bones":
            amount = int(key)
            db.add_bones(user["discord_id"], amount, wolf_id=user["id"])
            lines.append(f"**+{amount}🦴**")
    return lines
