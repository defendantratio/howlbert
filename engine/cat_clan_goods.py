"""Loot tables and grants for Warrior Cats clan border trade."""

from __future__ import annotations

import random
from typing import Literal

import database as db

LootKind = Literal["prey", "herb", "amusement", "bones"]

# Warrior Cats medicine-cat names for herb loot display (maps to game herb keys).
MEDICINE_HERB_LABELS: dict[str, str] = {
    "cobwebs": "cobweb dressing",
    "chamomile": "marigold (chamomile)",
    "coneflower": "marigold petals",
    "yarrow": "yarrow",
    "comfrey": "comfrey root",
    "goldenrod": "goldenrod",
    "tansy": "tansy",
    "borage": "borage",
    "chervil": "chervil",
    "dock": "dock leaf",
    "catmint": "catmint",
    "juniper_berry": "juniper berries",
    "poppy_seeds": "poppy seeds",
    "parsley": "parsley",
    "sage": "sage",
    "alder_bark": "alder bark",
    "burdock_root": "burdock root",
    "boneset": "boneset",
    "broom": "broom",
    "lambs_ear": "lambs ear (wound pad)",
    "plantain": "plantain leaf",
}

# Shared medicine-cat pantry rolls (receive/barter bias).
MEDICINE_CAT_TABLE: list[tuple[LootKind, str, int]] = [
    ("herb", "cobwebs", 22),
    ("herb", "yarrow", 18),
    ("herb", "chamomile", 16),
    ("herb", "comfrey", 14),
    ("herb", "goldenrod", 12),
    ("herb", "catmint", 10),
    ("herb", "borage", 10),
    ("herb", "dock", 8),
    ("herb", "tansy", 8),
    ("herb", "juniper_berry", 6),
]

# (kind, key, weight) per canon Clan
CLAN_LOOT_TABLES: dict[str, list[tuple[LootKind, str, int]]] = {
    "ThunderClan": [
        ("prey", "vole", 22),
        ("prey", "hare", 16),
        ("prey", "grouse", 10),
        ("herb", "chamomile", 18),
        ("herb", "cobwebs", 16),
        ("herb", "coneflower", 14),
        ("herb", "blackberry", 12),
        ("herb", "beech_leaves", 10),
        ("amusement", "feather", 12),
        ("amusement", "acorn", 8),
    ],
    "ShadowClan": [
        ("prey", "vole", 16),
        ("herb", "burdock_root", 18),
        ("herb", "boneset", 16),
        ("herb", "yarrow", 14),
        ("herb", "tansy", 12),
        ("herb", "dock", 10),
        ("amusement", "bone", 16),
        ("bones", "8", 10),
    ],
    "WindClan": [
        ("prey", "rabbit", 26),
        ("prey", "hare", 18),
        ("herb", "broom", 16),
        ("herb", "borage", 14),
        ("herb", "chervil", 12),
        ("herb", "sage", 10),
        ("amusement", "stick", 12),
    ],
    "RiverClan": [
        ("prey", "fish", 30),
        ("herb", "alder_bark", 18),
        ("herb", "parsley", 14),
        ("herb", "catmint", 14),
        ("herb", "juniper_berry", 10),
        ("herb", "blackberry", 10),
        ("amusement", "shell", 10),
    ],
}

PACT_LOOT_BONUS: dict[str, list[tuple[LootKind, str, int]]] = {
    "truce": [("herb", "cobwebs", 12)],
    "alliance": [("prey", "hare", 12), ("herb", "goldenrod", 10)],
    "hunting_rights": [("prey", "rabbit", 16), ("prey", "fish", 12)],
}

MEDICINE_ROLL_CHANCE = 0.42


def medicine_herb_display(herb_key: str) -> str:
    from herbs import HERBS

    if herb_key in MEDICINE_HERB_LABELS:
        return MEDICINE_HERB_LABELS[herb_key]
    return HERBS.get(herb_key, {}).get("name", herb_key.replace("_", " ").title())


def _pick_entry(table: list[tuple[LootKind, str, int]]) -> tuple[LootKind, str]:
    kinds, keys, weights = zip(*table)
    key = random.choices(keys, weights=weights, k=1)[0]
    idx = keys.index(key)
    return kinds[idx], key


def _clan_table(clan_name: str, pact_type: str) -> list[tuple[LootKind, str, int]]:
    from engine.cat_clans import canon_clan_name

    canon = canon_clan_name(clan_name) or clan_name
    base = list(CLAN_LOOT_TABLES.get(canon, CLAN_LOOT_TABLES["ThunderClan"]))
    base.extend(PACT_LOOT_BONUS.get(pact_type, ()))
    return base


def _roll_single_entry(clan_name: str, pact_type: str) -> tuple[LootKind, str]:
    if random.random() < MEDICINE_ROLL_CHANCE:
        return _pick_entry(MEDICINE_CAT_TABLE)
    return _pick_entry(_clan_table(clan_name, pact_type))


def receive_loot_count(trust: int, pact_type: str) -> int:
    from config import CAT_PACT_RECEIVE_MIN_TRUST, CAT_PACT_TRUST_HIGH

    if trust < CAT_PACT_RECEIVE_MIN_TRUST:
        return 0
    count = 1
    if trust >= CAT_PACT_TRUST_HIGH:
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


def roll_clan_loot(
    clan_name: str,
    *,
    pact_type: str,
    count: int,
) -> list[tuple[LootKind, str]]:
    if count <= 0:
        return []
    return [_roll_single_entry(clan_name, pact_type) for _ in range(count)]


def grant_clan_loot(
    user,
    *,
    guild_id: int,
    day: int,
    entries: list[tuple[LootKind, str]],
) -> list[str]:
    """Apply loot to wolf hoard; return display lines."""
    from engine.amusement_storage import grant_amusement
    from engine.herb_storage import grant_fresh_herb
    from engine.prey_storage import grant_prey_carcass
    from herbs import HERBS

    lines: list[str] = []
    wolf_id = int(user["id"])

    for kind, key in entries:
        if kind == "prey":
            from engine.prey_items import prey_meta

            grant_prey_carcass(wolf_id, key, guild_id=guild_id, acquired_day=day)
            lines.append(f"**{prey_meta(key)['name']}** → `/prey`")
        elif kind == "herb":
            if key not in HERBS:
                continue
            _, hoard_note = grant_fresh_herb(
                wolf_id,
                herb_key=key,
                guild_id=guild_id,
                day=day,
                user=user,
            )
            name = medicine_herb_display(key)
            line = f"**{name}** (medicine cat · fresh) → `/herbs action:bag`"
            if hoard_note:
                line += f" · _{hoard_note}_"
            lines.append(line)
        elif kind == "amusement":
            grant_amusement(wolf_id, key)
            from engine.amusement_items import amusement_meta

            lines.append(f"Toy **{amusement_meta(key)['name']}** → `/playpen action:toys`")
        elif kind == "bones":
            amount = max(1, int(key))
            db.add_bones(user["discord_id"], amount, wolf_id=wolf_id)
            lines.append(f"**+{amount}** 🦴 (cat-scrap trade)")

    return lines
