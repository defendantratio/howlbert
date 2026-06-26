"""Hunt outcome rolls and flavor text."""

from __future__ import annotations

import random

from config import HUNT_OUTCOMES
from engine.prey_items import prey_flavor_tier_cap

FLAVOR_TIER_ORDER = ("miss", "small", "solid", "big", "legendary")

HUNT_FLAVOR_MISS = (
    "You picked up a scent trail, but the prey slipped into the underbrush within a hare-hop.",
    "A rival scent spooked your quarry. Empty paws; carrion-breath talk if you return again.",
    "You tracked for tree-lengths through pine and stone, but the forest kept its meal.",
)

GENERIC_HUNT_FLAVOR = {
    "small": (
        "Old scraps near the riverbank. Not glorious, but it counts toward the pile.",
        "A quick kill in the bracken; modest fresh-kill for the hoard.",
    ),
    "solid": (
        "A clean takedown. The pack would approve of this fresh-kill.",
        "Swift chase, sure kill. A hunter's steady night at the cache.",
    ),
    "big": (
        "A clean takedown on serious quarry. A feast for the den.",
        "You brought down heavy prey alone. Word will travel.",
    ),
    "legendary": (
        "The old elk fell after a long chase. Even the elders will speak of this hunt.",
        "A rare pale elk; myth made meat. The forest remembers.",
    ),
}

PREY_HUNT_FLAVOR: dict[str, dict[str, tuple[str, ...]]] = {
    "vole": {
        "small": (
            "A vole wriggles once; then doesn't. Meager, but the belly doesn't argue.",
        ),
    },
    "hare": {
        "small": (
            "You pulled a scrawny hare from the snow. Small, but honest work for the cache.",
        ),
        "solid": (
            "You ran down a hare across open ground; swift and sure within a few pawsteps.",
        ),
    },
    "rabbit": {
        "small": (
            "A lone rabbit; enough fresh-kill to quiet an empty belly.",
        ),
        "solid": (
            "Two rabbits in one sweep. A hunter's steady night at the cache.",
        ),
    },
    "grouse": {
        "solid": (
            "A grouse bursts from cover; you bring it down before it clears the treeline.",
            "You snap up a grouse from the heather. Feathers and fresh-kill.",
        ),
    },
    "agouti": {
        "solid": (
            "You corner an agouti in the roots; quick jaws, quick kill.",
        ),
    },
    "beaver": {
        "solid": (
            "A beaver never hears you over the water; until it's too late.",
        ),
        "big": (
            "You drag a beaver from the bank. Heavy, greasy, worth the haul.",
        ),
    },
    "deer": {
        "solid": (
            "A clean takedown on a young deer. The pack would approve of this fresh-kill.",
        ),
        "big": (
            "A full deer share. Your jaws still ache from the haul.",
        ),
    },
    "elk": {
        "big": (
            "A full elk share. Your jaws still ache from the haul.",
        ),
        "legendary": (
            "The old elk fell after a long chase. Even the elders will speak of this hunt.",
            "A rare pale elk; myth made meat. The forest remembers.",
        ),
    },
    "frog": {
        "small": (
            "A frog vanishes under your paw; quick jaws, muddy bank, honest bite.",
            "Marsh frogs chorus at dusk; you silence one for the hoard.",
        ),
    },
    "snake": {
        "small": (
            "A garter snake never sees the strike; scales and fresh-kill for the cache.",
            "You pin a snake before it slides into the reeds.",
        ),
    },
    "lizard": {
        "small": (
            "A skink warms on stone until your shadow falls; then it doesn't.",
            "Sun-baked lizard; scant meat, but the den won't sniff at it.",
        ),
    },
}


def _hunt_tier(amount: int) -> str:
    if amount <= 0:
        return "miss"
    if amount <= 15:
        return "small"
    if amount <= 35:
        return "solid"
    if amount <= 60:
        return "big"
    return "legendary"


def roll_hunt_amount() -> int:
    outcomes = []
    for min_bones, max_bones, weight in HUNT_OUTCOMES:
        outcomes.extend([(min_bones, max_bones)] * weight)
    min_bones, max_bones = random.choice(outcomes)
    return random.randint(min_bones, max_bones)


def _cap_flavor_tier(tier: str, cap: str) -> str:
    if FLAVOR_TIER_ORDER.index(tier) > FLAVOR_TIER_ORDER.index(cap):
        return cap
    return tier


def hunt_flavor_for_prey(prey_key: str, amount: int) -> str:
    tier = _cap_flavor_tier(_hunt_tier(amount), prey_flavor_tier_cap(prey_key))
    if tier == "miss":
        return random.choice(HUNT_FLAVOR_MISS)
    by_prey = PREY_HUNT_FLAVOR.get(prey_key, {})
    if tier in by_prey:
        return random.choice(by_prey[tier])
    if tier in GENERIC_HUNT_FLAVOR:
        return random.choice(GENERIC_HUNT_FLAVOR[tier])
    return random.choice(GENERIC_HUNT_FLAVOR["solid"])


def pick_hunt_outcome() -> tuple[int, str]:
    """Roll bone payout and matching flavor (legacy helper)."""
    amount = roll_hunt_amount()
    if amount <= 0:
        return amount, hunt_flavor_for_prey("vole", 0)
    from engine.prey_items import prey_key_from_hunt_amount

    prey_key = prey_key_from_hunt_amount(amount)
    return amount, hunt_flavor_for_prey(prey_key, amount)
