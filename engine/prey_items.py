"""Prey carcasses; Wolvden-style hoard food with uses and rot timers."""

from __future__ import annotations

import random

# Rollovers (sunrises) before meat turns rotting; then ROTTEN_GRACE before it spoils.
PREY_FRESH_DAYS = 5
PREY_ROTTEN_GRACE_DAYS = 2
PREY_ROTTING_EAT_DISEASE_CHANCE = 0.25

PREY_CATALOG: dict[str, dict] = {
    "vole": {
        "name": "Vole Carcass",
        "label": "a vole",
        "uses": 2,
        "bones": 6,
        "rot_days": 4,
    },
    "mouse": {
        "name": "Mouse Carcass",
        "label": "a mouse",
        "uses": 1,
        "bones": 3,
        "rot_days": 3,
    },
    "squirrel": {
        "name": "Squirrel Carcass",
        "label": "a squirrel",
        "uses": 2,
        "bones": 7,
        "rot_days": 4,
    },
    "chipmunk": {
        "name": "Chipmunk Carcass",
        "label": "a chipmunk",
        "uses": 1,
        "bones": 4,
        "rot_days": 3,
    },
    "raccoon": {
        "name": "Raccoon Carcass",
        "label": "a raccoon",
        "uses": 3,
        "bones": 9,
        "rot_days": 4,
    },
    "opossum": {
        "name": "Opossum Carcass",
        "label": "an opossum",
        "uses": 2,
        "bones": 8,
        "rot_days": 4,
    },
    "muskrat": {
        "name": "Muskrat Carcass",
        "label": "a muskrat",
        "uses": 2,
        "bones": 7,
        "rot_days": 4,
    },
    "groundhog": {
        "name": "Groundhog Carcass",
        "label": "a groundhog",
        "uses": 3,
        "bones": 9,
        "rot_days": 4,
    },
    "hare": {
        "name": "Hare Carcass",
        "label": "a hare",
        "uses": 4,
        "bones": 12,
        "rot_days": 5,
    },
    "rabbit": {
        "name": "Rabbit Carcass",
        "label": "a rabbit",
        "uses": 4,
        "bones": 10,
        "rot_days": 5,
    },
    "fish": {
        "name": "River Fish",
        "label": "a fish",
        "uses": 3,
        "bones": 10,
        "rot_days": 4,
    },
    "grouse": {
        "name": "Grouse Carcass",
        "label": "a grouse",
        "uses": 4,
        "bones": 16,
        "rot_days": 5,
    },
    "agouti": {
        "name": "Agouti Carcass",
        "label": "an agouti",
        "uses": 4,
        "bones": 14,
        "rot_days": 5,
    },
    "beaver": {
        "name": "Beaver Carcass",
        "label": "a beaver",
        "uses": 6,
        "bones": 28,
        "rot_days": 6,
    },
    "deer": {
        "name": "Deer Carcass",
        "label": "a deer",
        "uses": 8,
        "bones": 50,
        "rot_days": 7,
    },
    "elk": {
        "name": "Elk Carcass",
        "label": "an elk",
        "uses": 10,
        "bones": 70,
        "rot_days": 8,
    },
    "carrion": {
        "name": "Old Carrion",
        "label": "old carrion",
        "uses": 2,
        "bones": 8,
        "rot_days": 3,
    },
    # Combat kills (added to hoard when downed in a fight)
    "coyote": {
        "name": "Coyote Carcass",
        "label": "a coyote",
        "uses": 4,
        "bones": 14,
        "rot_days": 5,
    },
    "fox": {
        "name": "Fox Carcass",
        "label": "a fox",
        "uses": 3,
        "bones": 10,
        "rot_days": 4,
    },
    "badger": {
        "name": "Badger Carcass",
        "label": "a badger",
        "uses": 5,
        "bones": 20,
        "rot_days": 6,
    },
    "wolverine": {
        "name": "Wolverine Carcass",
        "label": "a wolverine",
        "uses": 5,
        "bones": 22,
        "rot_days": 6,
    },
    "cougar": {
        "name": "Cougar Carcass",
        "label": "a cougar",
        "uses": 8,
        "bones": 48,
        "rot_days": 7,
    },
    "black_bear": {
        "name": "Black Bear Carcass",
        "label": "a black bear",
        "uses": 10,
        "bones": 58,
        "rot_days": 8,
    },
    "grizzly_bear": {
        "name": "Grizzly Carcass",
        "label": "a grizzly bear",
        "uses": 12,
        "bones": 85,
        "rot_days": 8,
    },
    "feral_dog": {
        "name": "Feral Hearth-hound Carcass",
        "label": "a feral hearth-hound",
        "uses": 4,
        "bones": 12,
        "rot_days": 5,
    },
    "guard_dog": {
        "name": "Guard Hearth-hound Carcass",
        "label": "a guard hearth-hound",
        "uses": 5,
        "bones": 16,
        "rot_days": 5,
    },
    "hunting_dog": {
        "name": "Hunting Hearth-hound Carcass",
        "label": "a hunting hearth-hound",
        "uses": 4,
        "bones": 14,
        "rot_days": 5,
    },
    "fighting_dog": {
        "name": "Fighting Hearth-hound Carcass",
        "label": "a fighting hearth-hound",
        "uses": 5,
        "bones": 18,
        "rot_days": 5,
    },
    "cat_carcass": {
        "name": "Cat Carcass",
        "label": "a cat",
        "uses": 3,
        "bones": 9,
        "rot_days": 4,
    },
    "kittypet_carcass": {
        "name": "Kittypet Carcass",
        "label": "a kittypet",
        "uses": 2,
        "bones": 6,
        "rot_days": 3,
    },
    "wolf_carcass": {
        "name": "Wolf Carcass",
        "label": "a wolf",
        "uses": 8,
        "bones": 35,
        "rot_days": 6,
        "cannibal": True,
    },
    "frog": {
        "name": "Frog Carcass",
        "label": "a frog",
        "uses": 2,
        "bones": 5,
        "rot_days": 3,
    },
    "snake": {
        "name": "Snake Carcass",
        "label": "a snake",
        "uses": 3,
        "bones": 8,
        "rot_days": 4,
    },
    "lizard": {
        "name": "Lizard Carcass",
        "label": "a lizard",
        "uses": 2,
        "bones": 6,
        "rot_days": 4,
    },
    # Forage food; wolves are facultative carnivores and will eat plant matter to
    # get by. Low bone value (you can't really salvage mush), restores hunger and
    # some thirst, and overripens/rots faster than meat.
"berries": {
        "name": "Mouthful of Berries",
        "label": "a mouthful of berries",
        "uses": 2,
        "bones": 1,
        "hunger": 14,
        "thirst": 12,
        "rot_days": 3,
        "category": "forage",
    },
    "windfall_fruit": {
        "name": "Windfall Fruit",
        "label": "fallen fruit",
        "uses": 3,
        "bones": 2,
        "hunger": 18,
        "thirst": 14,
        "rot_days": 4,
        "category": "forage",
    },
    "roots": {
        "name": "Roots & Tubers",
        "label": "roots",
        "uses": 3,
        "bones": 2,
        "hunger": 20,
        "thirst": 4,
        "rot_days": 9,
        "category": "forage",
    },
    "forage_greens": {
        "name": "Tender Greens",
        "label": "greens",
        "uses": 1,
        "bones": 1,
        "hunger": 8,
        "thirst": 8,
        "rot_days": 2,
        "category": "forage",
    },
}

# Spoilage wording per food category: meat rots, forage food overripens.
_SPOILAGE_TERMS = {
    "meat": {"fresh": "fresh", "rotting": "rotting", "spoiled": "spoiled"},
    "forage": {"fresh": "ripe", "rotting": "overripe", "spoiled": "rotted to mush"},
}


def prey_category(prey_key: str) -> str:
    """'meat' (default) or 'forage' for berries, fruit, roots, and greens."""
    return prey_meta(prey_key).get("category", "meat")


def is_forage_food(prey_key: str) -> bool:
    return prey_category(prey_key) == "forage"


def spoilage_terms(prey_key: str) -> dict:
    return _SPOILAGE_TERMS.get(prey_category(prey_key), _SPOILAGE_TERMS["meat"])


# What plant food a wolf can turn up while foraging, weighted by season. Returns
# a forage-food key or None (nothing edible found this time).
_SEASON_FORAGE_FOOD: dict[str, list] = {
    # (key_or_None, weight)
    "spring": [("forage_greens", 4), ("roots", 2), ("berries", 1), (None, 3)],
    "summer": [("berries", 5), ("forage_greens", 2), ("windfall_fruit", 1), (None, 2)],
    "autumn": [("windfall_fruit", 4), ("berries", 3), ("roots", 3), (None, 2)],
    "winter": [("roots", 2), (None, 8)],
}


def seasonal_forage_food(season: str | None) -> str | None:
    """Pick a plant food appropriate to the season, or None for a lean find."""
    table = _SEASON_FORAGE_FOOD.get((season or "spring").lower(), _SEASON_FORAGE_FOOD["spring"])
    keys = [k for k, _ in table]
    weights = [w for _, w in table]
    return random.choices(keys, weights=weights, k=1)[0]

# Each sniff flavor carries a "kind" that decides its mechanical payoff ; 
# no flavor-only text. "gather" flavors grant the hunt/track/scavenge/fish
# bones bonus (sniff_bonus_day); "water" flavors restore a little thirst
# from working close to the river; "alert" flavors raise this sniff's
# encounter odds instead of granting a buff, since you just smelled a
# rival nearby.
SNIFF_FLAVORS: tuple[dict, ...] = (
    {"text": "you nose the wind; rabbit somewhere east of the creek.", "kind": "gather"},
    {"text": "old blood on stone. something was dragged through the bracken recently.", "kind": "gather"},
    {"text": "pine and prey-scent tangled; a trail worth following at dawn.", "kind": "gather"},
    {"text": "the ground holds a warm track; small game, not far.", "kind": "gather"},
    {"text": "fish-oil and mud: the river bend was busy last night.", "kind": "water"},
    {"text": "a rival's mark on the border post; fresh, angry, close.", "kind": "alert"},
)

# Max hunt flavor tier per carcass type (stops "heavy prey" text on grouse, etc.)
PREY_FLAVOR_TIER_CAP: dict[str, str] = {
    "vole": "small",
    "hare": "small",
    "rabbit": "solid",
    "fish": "solid",
    "frog": "small",
    "snake": "small",
    "lizard": "small",
    "grouse": "solid",
    "agouti": "solid",
    "beaver": "big",
    "deer": "big",
    "elk": "legendary",
    "carrion": "small",
    "mouse": "small",
    "squirrel": "small",
    "chipmunk": "small",
    "raccoon": "small",
    "opossum": "small",
    "muskrat": "small",
    "groundhog": "small",
}


def prey_flavor_tier_cap(prey_key: str) -> str:
    return PREY_FLAVOR_TIER_CAP.get(prey_key, "solid")


def prey_meta(key: str) -> dict:
    from engine.fishing import FISHING_CATCHES

    if key in PREY_CATALOG:
        return PREY_CATALOG[key]
    if key in FISHING_CATCHES:
        return FISHING_CATCHES[key]
    return PREY_CATALOG["hare"]


def prey_key_from_label(label: str | None) -> str | None:
    """reverse lookup for prey-pile and legacy labels (incl. large-prey flavor text)."""
    if not label:
        return None
    low = label.lower().strip()
    # Large-prey / hunt flavor labels (cornered deer, fighting elk, desperate stag, …)
    if "elk" in low or "stag" in low:
        return "elk"
    if "deer" in low:
        return "deer"
    if "fish" in low:
        return "fish"
    if "hare" in low or "rabbit" in low:
        return "hare" if "hare" in low else "rabbit"
    from engine.fishing import FISHING_CATCHES

    for catalog in (PREY_CATALOG, FISHING_CATCHES):
        for key, meta in catalog.items():
            if meta.get("label") == label:
                return key
    for catalog in (PREY_CATALOG, FISHING_CATCHES):
        for key, meta in catalog.items():
            cat_label = meta.get("label", "")
            if cat_label and cat_label in low:
                return key
    return None


def canonical_prey_bones(prey_key: str) -> int:
    """standard bone value for a carcass type (eating, salvage, pile display)."""
    return int(prey_meta(prey_key)["bones"])


def is_cannibal_prey(prey_key: str) -> bool:
    return bool(prey_meta(prey_key).get("cannibal"))


def prey_key_from_hunt_amount(
    amount: int,
    *,
    great_pack: str | None = None,
    season: str | None = None,
) -> str:
    if amount <= 0:
        return "vole"
    season = season or "spring"
    if amount <= 8:
        if great_pack in ("mistmoor", "silverrush") and random.random() < 0.35:
            return random.choice(["frog", "vole"])
        if great_pack == "thistlehide" and random.random() < 0.22:
            return random.choice(["lizard", "vole"])
        if season == "summer" and random.random() < 0.2:
            return "hare"
        if random.random() < 0.25:
            return random.choice(["mouse", "chipmunk"])
        return "vole"
    if amount <= 15:
        if great_pack in ("mistmoor", "silverrush") and random.random() < 0.28:
            return "frog"
        if season == "summer" and random.random() < 0.35:
            return random.choice(["hare", "rabbit", "vole"])
        if season == "winter" and random.random() < 0.3:
            return "vole"
        if random.random() < 0.2:
            return random.choice(["squirrel", "raccoon", "opossum", "muskrat", "groundhog"])
        return random.choice(["hare", "rabbit"])
    if amount <= 22:
        if season == "winter" and random.random() < 0.4:
            return random.choice(["hare", "rabbit"])
        return random.choice(["grouse", "agouti"])
    if amount <= 28:
        if season == "autumn" and random.random() < 0.35:
            return "deer"
        return random.choice(["rabbit", "grouse"])
    if amount <= 35:
        if season == "winter" and random.random() < 0.45:
            return "beaver"
        return "beaver"
    if amount <= 60:
        if season == "autumn" and random.random() < 0.5:
            return "deer"
        if season == "winter" and random.random() < 0.25:
            return "beaver"
        return "deer"
    if season == "autumn":
        return "elk" if random.random() < 0.4 else "deer"
    return "elk"


def freshness_label(acquired_day: int, current_day: int, prey_key: str, *, rotting: bool) -> str:
    meta = prey_meta(prey_key)
    rot_days = meta.get("rot_days", PREY_FRESH_DAYS)
    terms = spoilage_terms(prey_key)
    age = max(0, current_day - acquired_day)
    if rotting:
        left = max(0, PREY_ROTTEN_GRACE_DAYS - (age - rot_days))
        if left <= 0:
            return f"**{terms['spoiled']}** (cleared next sunrise)"
        return f"**{terms['rotting']}** ({left}d until {terms['spoiled']})"
    left = max(0, rot_days - age)
    if left <= 1:
        return f"{terms['fresh']} (**{terms['rotting']} soon**; {left}d)"
    return f"{terms['fresh']} ({left}d)"


def salvage_bones(prey_key: str, uses_left: int, bone_value: int) -> int:
    meta = prey_meta(prey_key)
    full_uses = max(1, meta["uses"])
    portion = max(1, uses_left) / full_uses
    return max(1, int(bone_value * portion * 0.5))
