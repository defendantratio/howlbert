"""Wolvden-style amusement toys; multi-use mood boosters."""

AMUSEMENT_CATALOG: dict[str, dict] = {
    "bone": {
        "name": "Bone",
        "uses": 5,
        "mood": 10,
        "sell_bones": 2,
        "shred_remnants": 2,
        "description": "Gnawed clean; classic pack amusement.",
    },
    "feather": {
        "name": "Feather Bundle",
        "uses": 3,
        "mood": 10,
        "sell_bones": 3,
        "shred_remnants": 2,
        "description": "Soft plumes to bat around the den.",
    },
    "acorn": {
        "name": "Acorn",
        "uses": 2,
        "mood": 8,
        "sell_bones": 1,
        "shred_remnants": 1,
        "description": "A chipmunk's loss is your pup's gain.",
    },
    "shell": {
        "name": "Mollusk Shell",
        "uses": 3,
        "mood": 10,
        "sell_bones": 2,
        "shred_remnants": 2,
        "description": "Clatters nicely on stone; endless entertainment.",
    },
    "talon": {
        "name": "Owl Talon",
        "uses": 4,
        "mood": 12,
        "sell_bones": 4,
        "shred_remnants": 3,
        "description": "Sharp, shiny, forbidden; wolves love it.",
    },
    "stick": {
        "name": "Chew Stick",
        "uses": 4,
        "mood": 9,
        "sell_bones": 2,
        "shred_remnants": 2,
        "description": "Splintered branch from an old den site.",
    },
}


def amusement_meta(key: str) -> dict:
    return AMUSEMENT_CATALOG.get(key, AMUSEMENT_CATALOG["bone"])
