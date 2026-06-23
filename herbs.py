# Herb compendium; Basil rules (foraging & treatment)
from config import SEASON_FORAGE_DC_MOD
from herbs_compendium import HERBS


def herb_inventory_key(herb_key: str) -> str:
    """Inventory item key; stick uses plain ``stick`` (not ``herb_stick``)."""
    if herb_key == "stick":
        return "stick"
    return f"herb_{herb_key}"


FORAGE_RARITY_DC = {
    "common": 8,
    "uncommon": 12,
    "rare": 15,
    "very_rare": 20,
}

# Back-compat alias; prefer SEASON_FORAGE_DC_MOD from config
SEASON_FORAGE_MOD = SEASON_FORAGE_DC_MOD

# Injury table; roll 1d10 on critical hit or dropping to 0 HP
INJURY_TABLE = (
    "broken_tooth",
    "torn_claw",
    "deep_gash",
    "sprained_leg",
    "fractured_rib",
    "concussion",
    "punctured_paw",
    "infected_wound",
    "torn_ear",
    "broken_jaw",
)

INJURIES = {
    "broken_tooth": {
        "name": "Broken Tooth",
        "effect": "Disadvantage on bite attacks. No cure; permanent.",
        "treatment": "Permanent.",
        "permanent": True,
        "roll": 1,
    },
    "torn_claw": {
        "name": "Torn Claw",
        "effect": "−1 to claw damage. Heals in 1 week, or 3 days with horsetail poultice.",
        "treatment": "Horsetail poultice · 1 week natural heal",
        "heal_days": 7,
        "permanent": False,
        "roll": 2,
    },
    "deep_gash": {
        "name": "Deep Gash",
        "effect": "Bleeding: lose 1 HP each sunrise until bandaged.",
        "treatment": "Yarrow + cobwebs (or cattail/oak bark) stops bleeding",
        "permanent": False,
        "bleeding": True,
        "roll": 3,
    },
    "sprained_leg": {
        "name": "Sprained Leg",
        "effect": "Movement halved. Comfrey + 3 days rest.",
        "treatment": "Comfrey poultice · 3 days rest",
        "heal_days": 3,
        "permanent": False,
        "roll": 4,
    },
    "fractured_rib": {
        "name": "Fractured Rib",
        "effect": "Disadvantage on Strength checks; cannot hunt.",
        "treatment": "Comfrey poultice · 2 weeks rest",
        "heal_days": 14,
        "permanent": False,
        "blocks_hunt": True,
        "roll": 5,
    },
    "concussion": {
        "name": "Concussion",
        "effect": "Disadvantage on Intelligence checks; memory loss.",
        "treatment": "Dried skullcap · 1 week sleep",
        "heal_days": 7,
        "permanent": False,
        "roll": 6,
    },
    "punctured_paw": {
        "name": "Punctured Paw",
        "effect": "Disadvantage on Dexterity checks involving running or climbing.",
        "treatment": "Heals in 1 week; oak bark binding halves time",
        "heal_days": 7,
        "permanent": False,
        "roll": 7,
    },
    "infected_wound": {
        "name": "Infected Wound",
        "effect": "Each sunrise: Survival/Constitution save or −1 HP and +1 exhaustion.",
        "treatment": "Yarrow or goldenrod poultice",
        "permanent": False,
        "infection": True,
        "roll": 8,
    },
    "torn_ear": {
        "name": "Torn Ear / Lost Eye",
        "effect": "Permanent −1 to Perception (Wisdom) checks.",
        "treatment": "Torn ear heals cosmetically; penalty remains. Lost eye: no cure.",
        "permanent": True,
        "roll": 9,
    },
    "broken_jaw": {
        "name": "Broken Jaw",
        "effect": "Cannot bite or eat solid food. Liquid diet + 3 weeks rest.",
        "treatment": "Broth/milk · comfrey poultice reduces to 2 weeks",
        "heal_days": 21,
        "permanent": False,
        "blocks_bite": True,
        "roll": 10,
    },
    "spinal_injury": {
        "name": "Spinal Injury",
        "effect": (
            "Hindquarters paralyzed; cannot hunt, patrol, explore, or fight; "
            "comfrey + bindweed splint · ~4 weeks rest."
        ),
        "treatment": "Comfrey poultice · bindweed splint · 28 days rest",
        "heal_days": 28,
        "permanent": False,
        "paralysis": True,
        "blocks_strenuous": True,
    },
    "paralyzed": {
        "name": "Paralyzed (Permanent)",
        "effect": (
            "Spinal cord severed; den-bound; cannot hunt, patrol, explore, combat, or travel."
        ),
        "treatment": "No cure; lifelong den care.",
        "permanent": True,
        "paralysis": True,
        "blocks_strenuous": True,
    },
}

from engine.diseases import COUGH_STAGES, DISEASES

DISEASE_STAGES = COUGH_STAGES

EXHAUSTION_EFFECTS = {
    1: "Disadvantage on skill checks.",
    2: "Speed halved.",
    3: "Disadvantage on attack rolls.",
    4: "HP maximum halved.",
    5: "Speed 0 (cannot move).",
    6: "Death.",
}

PACK_UNITY_EFFECTS = {
    "low": "Unity 1-2: −10% hunt bones.",
    "breaking": "Unity 0: −20% hunt bones; plain howls cannot raise unity.",
    "fracturing": "Unity −1 to −4: −25% hunt bones; need Alpha/Beta (Advisor) to rally.",
    "collapse": "Unity −5: pack dissolves; all members become loners.",
    "high": "Unity ≥ 8: +10% hunt bones.",
}

RIVAL_STANDING_EFFECTS = {
    "friendly": "Standing ≥ 8: may share hunting grounds.",
    "hostile": "Standing ≤ 3: attacks on sight.",
    "war": "Standing 0: constant skirmishes.",
}
