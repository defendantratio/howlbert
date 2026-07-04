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
        "effect": "Movement halved. Comfrey + 1 week rest.",
        "treatment": "Comfrey poultice · 1 week rest",
        "heal_days": 7,
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
    "festering_wound": {
        "name": "Festering Wound",
        "effect": (
            "Deep infection: −1 HP and +1 exhaustion each sunrise without a save. "
            "DC 15 to cure (yarrow or goldenrod decoction)."
        ),
        "treatment": "Yarrow decoction · goldenrod decoction · urgent Medic care",
        "permanent": False,
        "infection": True,
        "festering": True,
        "heal_days": 7,
    },
    "scorched_hide": {
        "name": "Scorched Hide",
        "effect": (
            "Burnt skin and fur from fire or boiling liquid: +1 exhaustion each sunrise. "
            "Cannot be treated with herbs; only cobwebs and total rest (7 days)."
        ),
        "treatment": "Cobwebs dressing · 7 days full rest — no herb cure",
        "permanent": False,
        "heat_injury": True,
        "heal_days": 7,
    },
    "bruised_lung": {
        "name": "Bruised Lung",
        "effect": (
            "Develops from a fractured rib left untreated for 2+ sunrises. "
            "Each breath is shallow and laboured: −1 STR and −1 WIS while active. "
            "Surgery only; cannot be cured with herbs."
        ),
        "treatment": "Surgery (set_bone) — no herb cure",
        "permanent": False,
        "heal_days": 14,
        "surgery_only": True,
    },
    "swollen_eye": {
        "name": "Swollen Eye",
        "effect": (
            "Develops from a concussion left untreated for 2+ sunrises. "
            "Vision impaired: disadvantage on all attack rolls while active. "
            "Cured by celandine or feverfew poultice."
        ),
        "treatment": "Celandine or feverfew poultice",
        "permanent": False,
        "heal_days": 5,
        "vision_impaired": True,
    },
    "blood_loss": {
        "name": "Blood Loss",
        "effect": (
            "Wolf ended a fight at ≤2 HP: severe haemorrhage reduces blood volume. "
            "−1 max HP until 3 full rests have passed. Clears automatically."
        ),
        "treatment": "3 full rests — clears automatically",
        "permanent": False,
        "blood_loss": True,
    },
    "snake_venom": {
        "name": "Snake Venom",
        "effect": (
            "venom courses through the body — +1 pain exhaustion and -1 HP each sunrise. "
            "dex -4; con save DC 14 each sunrise or +1 exhaustion. fades after ~5 days if survived."
        ),
        "treatment": "twinflower poultice may slow progression; feverfew reduces fever. no guaranteed cure.",
        "permanent": False,
        "heal_days": 5,
        "snake_venom": True,
    },
    "insect_sting": {
        "name": "Insect Sting",
        "effect": (
            "swollen sting site; -6 mood each sunrise, dex -1 on paw and muzzle checks."
        ),
        "treatment": "dock leaf or burdock poultice reduces swelling. clears in 3 days.",
        "permanent": False,
        "heal_days": 3,
        "insect_sting": True,
    },
}

from engine.diseases import COUGH_STAGES, DISEASES

DISEASE_STAGES = COUGH_STAGES

EXHAUSTION_EFFECTS = {
    1: "Disadvantage on skill checks.",
    2: "Hunt penalty; bone yield reduced.",
    3: "Disadvantage on attack rolls.",
    4: "Disadvantage on Strength and Dexterity checks.",
    5: "Wounds heal slower; body under strain.",
    6: "HP maximum halved.",
    7: "Movement slowed; all physical effort costs double.",
    8: "Strenuous activity blocked; body failing.",
    9: "Barely mobile; collapse imminent.",
    10: "Death.",
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
