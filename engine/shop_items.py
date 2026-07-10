"""Mechanical effects for trading-post items."""

import random

import database as db

LUCKY_TOOTH_HUNT_BONUS_PCT = 15
RABBIT_PELT_GIFT_BONES = 10
RABBIT_PELT_STANDING = 2
RAVEN_COMPANION_SCAVENGE_BONUS_PCT = 20
RAVEN_COMPANION_TRACK_BONUS_PCT = 10

USABLE_ITEM_KEYS = frozenset(
    {"herb_bundle", "prey_bundle", "den_charm", "rabbit_pelt", "revive", "reincarnation"}
)


def has_item(discord_id: int, key: str) -> bool:
    item = db.get_item_by_key(key)
    if not item:
        return False
    return db.get_inventory_quantity(discord_id, item["id"]) > 0


def consume_item_by_key(discord_id: int, key: str) -> bool:
    item = db.get_item_by_key(key)
    if not item:
        return False
    return db.consume_item(discord_id, item["id"])


def lucky_tooth_hunt_bonus(discord_id: int, amount: int) -> tuple[int, int]:
    """Return (new_amount, bonus_added) for hunt payouts."""
    if amount <= 0 or not has_item(discord_id, "lucky_tooth"):
        return amount, 0
    bonus = max(1, int(amount * LUCKY_TOOTH_HUNT_BONUS_PCT / 100))
    return amount + bonus, bonus


def raven_companion_scavenge_bonus(discord_id: int, amount: int) -> tuple[int, int]:
    """Return (new_amount, bonus_added) for scavenge payouts."""
    if amount <= 0 or not has_item(discord_id, "raven_companion"):
        return amount, 0
    bonus = max(1, int(amount * RAVEN_COMPANION_SCAVENGE_BONUS_PCT / 100))
    return amount + bonus, bonus


def raven_companion_track_bonus(discord_id: int, amount: int) -> tuple[int, int]:
    """Return (new_amount, bonus_added) for track payouts."""
    if amount <= 0 or not has_item(discord_id, "raven_companion"):
        return amount, 0
    bonus = max(1, int(amount * RAVEN_COMPANION_TRACK_BONUS_PCT / 100))
    return amount + bonus, bonus


def roll_herb_bundle_heal() -> int:
    return random.randint(1, 4) + 1


def roll_herb_bundle_grants() -> list[tuple[str, str]]:
    """return [(herb_key, display_name), ...] for a random herb bundle."""
    from herbs_compendium import HERBS

    count = random.randint(2, 4)
    pool = [k for k, meta in HERBS.items() if not meta.get("poison")]
    if not pool:
        return []
    picks = random.choices(pool, k=count)
    return [(key, HERBS[key]["name"]) for key in picks]


def grant_herb_bundle(discord_id: int) -> tuple[list[str], str]:
    """Grant random herbs to inventory. Returns (item keys, summary line)."""
    from herbs import herb_inventory_key

    grants = roll_herb_bundle_grants()
    if not grants:
        return [], "the bundle was empty."
    lines: list[str] = []
    for key, name in grants:
        item = db.get_item_by_key(herb_inventory_key(key))
        if not item:
            continue
        db.grant_item(discord_id, item["id"])
        lines.append(f"**{name}** (`{herb_inventory_key(key)}`)")
    if not lines:
        return [], "the bundle was empty."
    return [herb_inventory_key(k) for k, _ in grants], " · ".join(lines)


def use_herb_bundle(user, discord_id: int) -> tuple[bool, str, dict]:
    """
    Open a herb bundle: random herbs plus 1d4+1 HP (Ko-fi / shop consumable).
    Returns (success, message, db_fields for caller to apply).
    """
    from engine.exhaustion_effects import effective_max_hp

    keys, summary = grant_herb_bundle(discord_id)
    if not keys:
        return False, summary, {}
    heal = roll_herb_bundle_heal()
    cap = effective_max_hp(user)
    new_hp = min(cap, int(user["hp"]) + heal)
    msg = f"bundle salve eases old aches (**+{heal} hp**). {summary}"
    return True, msg, {"hp": new_hp}


def roll_prey_bundle_grants() -> list[str]:
    """random prey keys for a prey bundle; mostly small game."""

    count = random.randint(2, 3)
    small = ("vole", "hare", "rabbit", "fish", "grouse", "agouti")
    medium = ("beaver", "deer")
    pool = list(small) * 4 + list(medium)
    return random.choices(pool, k=count)


def grant_prey_bundle(wolf_id: int, *, guild_id: int, day: int) -> tuple[list[str], str]:
    from engine.prey_storage import grant_prey_carcass
    from engine.prey_items import prey_meta

    keys = roll_prey_bundle_grants()
    lines: list[str] = []
    for key in keys:
        grant_prey_carcass(wolf_id, key, guild_id=guild_id, acquired_day=day)
        lines.append(f"**{prey_meta(key)['name']}**")
    return keys, " · ".join(lines)
