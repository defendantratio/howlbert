"""Wolvden-style biome fishing; pack waters, rarity tiers, turtles, weather/time gates."""

from __future__ import annotations

import random
from typing import Any

# Rarity weights when no time/weather gate applies (common → legendary).
RARITY_BASE_WEIGHT: dict[str, int] = {
    "common": 18,
    "regular": 14,
    "uncommon": 9,
    "rare": 5,
    "legendary": 2,
}

RAIN_WEATHER = frozenset({"rain", "storm", "sleet", "thunderstorm", "hail"})
NIGHT_TIMES = frozenset({"night", "dusk"})
DAWN_DUSK = frozenset({"dawn", "dusk"})
DAY_TIMES = frozenset({"day", "dawn", "dusk"})

FISHING_CATCHES: dict[str, dict[str, Any]] = {
    # --- Generic fallback (any pack) ---
    "fish": {
        "name": "River Fish",
        "label": "a fish",
        "uses": 3,
        "bones": 10,
        "rot_days": 4,
        "rarity": "regular",
        "kind": "fish",
        "flavor": (
            "A silver fish flips in your teeth at the riverbank.",
            "Slow paw, steady catch; the river gives without a chase.",
        ),
    },
    # --- Common / regular river fish ---
    "bluegill": {
        "name": "Bluegill",
        "label": "a bluegill",
        "uses": 2,
        "bones": 6,
        "rot_days": 4,
        "rarity": "common",
        "kind": "fish",
        "flavor": ("A palm-sized **bluegill** wriggles once in the shallows.",),
    },
    "river_chub": {
        "name": "River Chub",
        "label": "a river chub",
        "uses": 2,
        "bones": 7,
        "rot_days": 4,
        "rarity": "common",
        "kind": "fish",
        "flavor": ("A **river chub** darts from under a root; quick jaws end the chase.",),
    },
    "threadfin_shad": {
        "name": "Threadfin Shad",
        "label": "a threadfin shad",
        "uses": 2,
        "bones": 5,
        "rot_days": 3,
        "rarity": "common",
        "kind": "fish",
        "flavor": ("Slender **threadfin shad**; scales like spilled moonlight.",),
    },
    "perch": {
        "name": "Perch",
        "label": "a perch",
        "uses": 3,
        "bones": 10,
        "rot_days": 4,
        "rarity": "regular",
        "kind": "fish",
        "flavor": ("A barred **perch**; honest river meat for the hoard.",),
    },
    "mud_shad": {
        "name": "Mud Shad",
        "label": "a mud shad",
        "uses": 3,
        "bones": 9,
        "rot_days": 4,
        "rarity": "regular",
        "kind": "fish",
        "flavor": ("**Mud shad** from the silty bend; oily and filling.",),
    },
    "spotted_gar": {
        "name": "Spotted Gar",
        "label": "a spotted gar",
        "uses": 3,
        "bones": 12,
        "rot_days": 4,
        "rarity": "regular",
        "kind": "fish",
        "flavor": ("Long jaws; the **spotted gar** fights harder than it looks.",),
    },
    "white_crappie": {
        "name": "White Crappie",
        "label": "a white crappie",
        "uses": 3,
        "bones": 9,
        "rot_days": 4,
        "rarity": "regular",
        "kind": "fish",
        "flavor": ("A pale **white crappie**; easy haul at dusk.",),
    },
    "brook_trout": {
        "name": "Brook Trout",
        "label": "a brook trout",
        "uses": 3,
        "bones": 11,
        "rot_days": 4,
        "rarity": "regular",
        "kind": "fish",
        "flavor": ("Speckled **brook trout** from cold runoff; the mountains approve.",),
    },
    "mountain_whitefish": {
        "name": "Mountain Whitefish",
        "label": "a mountain whitefish",
        "uses": 3,
        "bones": 11,
        "rot_days": 4,
        "rarity": "regular",
        "kind": "fish",
        "flavor": ("A **mountain whitefish**; snowmelt-cold and clean.",),
    },
    "green_sunfish": {
        "name": "Green Sunfish",
        "label": "a green sunfish",
        "uses": 2,
        "bones": 6,
        "rot_days": 4,
        "rarity": "common",
        "kind": "fish",
        "flavor": ("A **green sunfish** from the forest pool; small but sharp.",),
    },
    "northern_sunfish": {
        "name": "Northern Sunfish",
        "label": "a northern sunfish",
        "uses": 2,
        "bones": 6,
        "rot_days": 4,
        "rarity": "common",
        "kind": "fish",
        "flavor": ("Bright **northern sunfish** in the shallows.",),
    },
    "swamp_darter": {
        "name": "Swamp Darter",
        "label": "a swamp darter",
        "uses": 2,
        "bones": 5,
        "rot_days": 3,
        "rarity": "common",
        "kind": "fish",
        "flavor": ("A tiny **swamp darter**; the marsh still counts it as prey.",),
    },
    "flathead_mullet": {
        "name": "Flathead Mullet",
        "label": "a flathead mullet",
        "uses": 3,
        "bones": 11,
        "rot_days": 4,
        "rarity": "regular",
        "kind": "fish",
        "flavor": ("**Flathead mullet** slides through brown water; you slide teeth first.",),
    },
    "largemouth_bass": {
        "name": "Largemouth Bass",
        "label": "a largemouth bass",
        "uses": 4,
        "bones": 16,
        "rot_days": 5,
        "rarity": "uncommon",
        "kind": "fish",
        "flavor": ("A heavy **largemouth bass**; the hoard will notice.",),
    },
    "blue_catfish": {
        "name": "Blue Catfish",
        "label": "a blue catfish",
        "uses": 4,
        "bones": 18,
        "rot_days": 5,
        "rarity": "uncommon",
        "kind": "fish",
        "flavor": ("Whiskers and muscle; **blue catfish** from the deep hole.",),
    },
    "walleye": {
        "name": "Walleye",
        "label": "a walleye",
        "uses": 4,
        "bones": 17,
        "rot_days": 5,
        "rarity": "uncommon",
        "kind": "fish",
        "flavor": ("Glass-eyed **walleye**; night fishing pays.",),
    },
    "carp": {
        "name": "Carp",
        "label": "a carp",
        "uses": 4,
        "bones": 15,
        "rot_days": 5,
        "rarity": "uncommon",
        "kind": "fish",
        "flavor": ("A broad **carp**; muddy fight, honest meat.",),
    },
    "chinook_salmon": {
        "name": "Chinook Salmon",
        "label": "a chinook salmon",
        "uses": 5,
        "bones": 24,
        "rot_days": 5,
        "rarity": "rare",
        "kind": "fish",
        "flavor": ("A **chinook salmon**; mountain river royalty.",),
    },
    "blind_swamp_eel": {
        "name": "Blind Swamp Eel",
        "label": "a blind swamp eel",
        "uses": 3,
        "bones": 14,
        "rot_days": 4,
        "rarity": "rare",
        "kind": "fish",
        "flavor": ("Pale **blind swamp eel** from the peat; unsettling, edible.",),
    },
    "alligator_gar": {
        "name": "Alligator Gar",
        "label": "an alligator gar",
        "uses": 6,
        "bones": 32,
        "rot_days": 6,
        "rarity": "legendary",
        "kind": "fish",
        "flavor": ("Armored **alligator gar**; elders will speak of this haul.",),
    },
    "gulf_sturgeon": {
        "name": "Gulf Sturgeon",
        "label": "a gulf sturgeon",
        "uses": 7,
        "bones": 38,
        "rot_days": 6,
        "rarity": "legendary",
        "kind": "fish",
        "flavor": ("Ancient **gulf sturgeon**; the swamp yields a myth.",),
    },
    "lake_sturgeon": {
        "name": "Lake Sturgeon",
        "label": "a lake sturgeon",
        "uses": 7,
        "bones": 40,
        "rot_days": 6,
        "rarity": "legendary",
        "kind": "fish",
        "flavor": ("A **lake sturgeon** longer than your foreleg; legend made meat.",),
    },
    "shovelnose_sturgeon": {
        "name": "Shovelnose Sturgeon",
        "label": "a shovelnose sturgeon",
        "uses": 5,
        "bones": 26,
        "rot_days": 5,
        "rarity": "legendary",
        "kind": "fish",
        "flavor": ("**Shovelnose sturgeon** from the gravel bar; rare and heavy.",),
    },
    # --- Amphibians (Wolvden bullfrog; separate from marsh hunt frogs) ---
    "bullfrog": {
        "name": "Bullfrog",
        "label": "a bullfrog",
        "uses": 2,
        "bones": 6,
        "rot_days": 3,
        "rarity": "legendary",
        "kind": "amphibian",
        "flavor": ("A bellowing **bullfrog**; amphibian prize from the bank.",),
    },
    # --- Turtles (Wolvden legendary/rare catches) ---
    "painted_turtle": {
        "name": "Painted Turtle",
        "label": "a painted turtle",
        "uses": 3,
        "bones": 8,
        "rot_days": 5,
        "rarity": "rare",
        "kind": "turtle",
        "flavor": ("A **painted turtle** on a log; shell cracks, meat doesn't lie.",),
    },
    "common_snapping_turtle": {
        "name": "Common Snapping Turtle",
        "label": "a common snapping turtle",
        "uses": 6,
        "bones": 30,
        "rot_days": 6,
        "rarity": "legendary",
        "kind": "turtle",
        "flavor": ("A **common snapping turtle**; jaws like stone, haul like a deer.",),
    },
    "northern_red_bellied_cooter": {
        "name": "Northern Red-Bellied Cooter",
        "label": "a northern red-bellied cooter",
        "uses": 5,
        "bones": 22,
        "rot_days": 5,
        "rarity": "legendary",
        "kind": "turtle",
        "flavor": ("**Northern red-bellied cooter**; river legend in a shell.",),
    },
    "alligator_snapping_turtle": {
        "name": "Alligator Snapping Turtle",
        "label": "an alligator snapping turtle",
        "uses": 7,
        "bones": 42,
        "rot_days": 7,
        "rarity": "legendary",
        "kind": "turtle",
        "flavor": ("An **alligator snapping turtle**; moss on its back, death in its beak.",),
    },
    "spotted_turtle": {
        "name": "Spotted Turtle",
        "label": "a spotted turtle",
        "uses": 4,
        "bones": 18,
        "rot_days": 5,
        "rarity": "legendary",
        "kind": "turtle",
        "flavor": ("A **spotted turtle**; small shell, rare find.",),
    },
    "western_pond_turtle": {
        "name": "Western Pond Turtle",
        "label": "a western pond turtle",
        "uses": 4,
        "bones": 20,
        "rot_days": 5,
        "rarity": "legendary",
        "kind": "turtle",
        "flavor": ("**Western pond turtle** from the reed bed; worth the patience.",),
    },
    "wood_turtle": {
        "name": "Wood Turtle",
        "label": "a wood turtle",
        "uses": 4,
        "bones": 19,
        "rot_days": 5,
        "rarity": "legendary",
        "kind": "turtle",
        "flavor": ("A **wood turtle**; forest stream treasure.",),
    },
    "bog_turtle": {
        "name": "Bog Turtle",
        "label": "a bog turtle",
        "uses": 3,
        "bones": 14,
        "rot_days": 4,
        "rarity": "legendary",
        "kind": "turtle",
        "flavor": ("A tiny **bog turtle**; the marsh's smallest legend.",),
    },
}

# (prey_key, weight_multiplier, optional gates dict)
# Gates: times=tuple, weather_any=tuple, weather_rain=True (rain/sleet/storm)
_PACK_POOLS: dict[str, tuple[tuple, ...]] = {
    "silverrush": (
        ("bluegill", 1, {}),
        ("river_chub", 1, {}),
        ("threadfin_shad", 1, {}),
        ("perch", 1, {}),
        ("mud_shad", 1, {}),
        ("spotted_gar", 1, {}),
        ("white_crappie", 1, {}),
        ("blue_catfish", 1, {}),
        ("walleye", 1, {"times": NIGHT_TIMES}),
        ("painted_turtle", 1, {"times": DAY_TIMES, "weather_rain": True}),
        ("common_snapping_turtle", 1, {"times": DAY_TIMES}),
        ("northern_red_bellied_cooter", 1, {"times": DAWN_DUSK}),
        ("shovelnose_sturgeon", 1, {"weather_rain": True}),
        ("western_pond_turtle", 1, {"weather_rain": True}),
        ("spotted_turtle", 1, {"times": DAWN_DUSK}),
        ("bullfrog", 1, {"weather_rain": True}),
    ),
    "mistmoor": (
        ("swamp_darter", 1, {}),
        ("flathead_mullet", 1, {}),
        ("mud_shad", 1, {}),
        ("spotted_gar", 1, {}),
        ("largemouth_bass", 1, {}),
        ("blind_swamp_eel", 1, {}),
        ("alligator_gar", 1, {"times": NIGHT_TIMES}),
        ("gulf_sturgeon", 1, {"times": DAWN_DUSK}),
        ("bog_turtle", 1, {"times": DAY_TIMES}),
        ("alligator_snapping_turtle", 1, {"times": DAY_TIMES}),
        ("painted_turtle", 1, {"weather_rain": True}),
        ("bullfrog", 1, {"weather_rain": True}),
    ),
    "thistlehide": (
        ("green_sunfish", 1, {}),
        ("northern_sunfish", 1, {}),
        ("perch", 1, {}),
        ("mud_shad", 1, {}),
        ("spotted_gar", 1, {}),
        ("carp", 1, {}),
        ("white_crappie", 1, {}),
        ("lake_sturgeon", 1, {"times": DAY_TIMES}),
        ("wood_turtle", 1, {"times": DAWN_DUSK}),
        ("painted_turtle", 1, {}),
        ("bullfrog", 1, {"weather_rain": True}),
        ("common_snapping_turtle", 1, {"times": DAY_TIMES}),
    ),
    "greyspire": (
        ("brook_trout", 1, {}),
        ("mountain_whitefish", 1, {}),
        ("river_chub", 1, {}),
        ("chinook_salmon", 1, {"times": DAY_TIMES}),
        ("walleye", 1, {"times": NIGHT_TIMES}),
        ("spotted_gar", 1, {}),
        ("wood_turtle", 1, {"times": DAWN_DUSK}),
        ("shovelnose_sturgeon", 1, {"weather_rain": True}),
        ("bullfrog", 1, {"weather_rain": True}),
    ),
}

_DEFAULT_POOL = (
    ("bluegill", 1, {}),
    ("river_chub", 1, {}),
    ("perch", 1, {}),
    ("mud_shad", 1, {}),
    ("northern_sunfish", 1, {}),
    ("spotted_gar", 1, {}),
    ("painted_turtle", 1, {}),
    ("common_snapping_turtle", 1, {"times": DAY_TIMES}),
    ("shovelnose_sturgeon", 1, {"weather_rain": True}),
)


def _gates_ok(gates: dict, time_of_day: str, weather: str) -> bool:
    if not gates:
        return True
    tod = (time_of_day or "day").lower()
    wx = (weather or "clear").lower()
    if gates.get("times") and tod not in gates["times"]:
        return False
    if gates.get("weather_rain") and wx not in RAIN_WEATHER:
        return False
    if gates.get("weather_any") and wx not in gates["weather_any"]:
        return False
    return True


def _pool_for_pack(great_pack: str | None) -> tuple[tuple, ...]:
    if great_pack and great_pack in _PACK_POOLS:
        return _PACK_POOLS[great_pack]
    return _DEFAULT_POOL


def pick_fishing_catch(
    *,
    great_pack: str | None,
    time_of_day: str,
    weather: str,
) -> dict[str, Any]:
    """
    Roll a Wolvden-style catch for the wolf's pack waters.
    Always returns a fish-category prey (never replaces fish with frogs outright).
    """
    pool = _pool_for_pack(great_pack)
    weighted: list[tuple[str, int]] = []
    for entry in pool:
        key, mult, gates = entry[0], entry[1], entry[2] if len(entry) > 2 else {}
        if key not in FISHING_CATCHES:
            continue
        if not _gates_ok(gates, time_of_day, weather):
            continue
        rarity = FISHING_CATCHES[key]["rarity"]
        weight = RARITY_BASE_WEIGHT.get(rarity, 10) * mult
        weighted.append((key, weight))

    if not weighted:
        key = "fish"
    else:
        keys, weights = zip(*weighted)
        key = random.choices(keys, weights=weights, k=1)[0]

    meta = FISHING_CATCHES[key]
    flavor = random.choice(meta.get("flavor", ("You land a catch.",)))
    rarity = meta["rarity"]
    tag = ""
    if rarity in ("rare", "legendary"):
        tag = f"\n\n_**{rarity.title()}** catch!_"
    if meta.get("kind") == "turtle":
        tag += "\n_Shell and meat; Wolvden-style turtle haul._"

    return {
        "prey_key": key,
        "name": meta["name"],
        "label": meta["label"],
        "flavor": flavor + tag,
        "rarity": rarity,
        "kind": meta.get("kind", "fish"),
    }


def fishing_catch_meta(prey_key: str) -> dict | None:
    return FISHING_CATCHES.get(prey_key)


def is_fishing_prey(prey_key: str) -> bool:
    return prey_key in FISHING_CATCHES
