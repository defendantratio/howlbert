"""
FULL HERBAL MEDICINE SYSTEM – DISCORD BOT READY
=================================================
This module provides:
  - Research‑backed disease definitions (Warrior Cats‑inspired names)
  - Full herb compendium with preparation methods, cures, and side effects
  - Preparation logic with Medicine skill checks
  - Administration logic with stage‑specific cures and side‑effect application
  - Discord slash command stubs (commented out – integrate with your bot)

All text is lowercase and uses hyphens for readability.
"""

from __future__ import annotations

import json
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# 1. DISEASE DEFINITIONS (Warrior Cats‑inspired, research‑backed)
# ============================================================================

COUGH_STAGES = {
    "mild": {
        "name": "whitecough (mild)",
        "dc": 12,
        "next": "severe",
        "effect": (
            "mild chest infection from damp or cold; a dry rasp at the back of the throat; "
            "disadvantage on Dexterity checks."
        ),
    },
    "severe": {
        "name": "greencough (severe)",
        "dc": 15,
        "next": "deadly",
        "effect": "green phlegm and fever; disadvantage on Dexterity and Strength; speed -1/4.",
    },
    "deadly": {
        "name": "blackcough (deadly)",
        "dc": 18,
        "next": None,
        "effect": "lungs fill with fluid; disadvantage on all physical checks; lose 1 HP each sunrise.",
        "hp_loss": 1,
    },
}

DISEASES: Dict[str, Dict] = {
    # ----- RESPIRATORY -----
    "cough": {
        "label": "cough",
        "contagious": 0.14,
        "respiratory": True,
        "spread_stage": "mild",
        "stages": COUGH_STAGES,
    },
    "leafbare_cough": {
        "label": "leaf-bare cough",
        "contagious": 0.22,
        "respiratory": True,
        "spread_stage": "chill",
        "stages": {
            "chill": {
                "name": "leaf-bare cough (chill)",
                "dc": 11,
                "next": "hacking",
                "effect": "cold air bites deep; a dry rasp at the throat; -4 mood each sunrise.",
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "hacking": {
                "name": "leaf-bare cough (hacking)",
                "dc": 13,
                "next": "congestion",
                "effect": "the cough turns bark-deep; -6 mood, -15% hunt.",
                "mood_loss": 6,
                "hunt_mult": 0.85,
            },
            "congestion": {
                "name": "leaf-bare cough (congestion)",
                "dc": 15,
                "next": None,
                "effect": "chest fills; fever climbs; +1 exhaustion, -1 HP each sunrise; lethal without catmint/mullein/lungwort.",
                "exhaustion_gain": 1,
                "hp_loss": 1,
                "mood_loss": 4,
                "hunt_mult": 0.75,
                "lethal": True,
            },
        },
    },
    "yellowcough": {
        "label": "yellowcough",
        "contagious": 0.45,
        "respiratory": True,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "yellowcough",
                "dc": 17,
                "next": None,
                "effect": (
                    "labored breathing, high fever, bright yellow phlegm; "
                    "-12 hunger, +1 exhaustion, -6 mood, -1 HP each sunrise; "
                    "fatal without mullein or lungwort."
                ),
                "hunger_loss": 12,
                "exhaustion_gain": 1,
                "mood_loss": 6,
                "hp_loss": 1,
                "hunt_mult": 0.55,
                "lethal": True,
            },
        },
    },
    "pupcough": {
        "label": "pupcough",
        "contagious": 0.10,
        "respiratory": True,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "pupcough",
                "dc": 10,
                "next": "weak_lungs",
                "effect": "harsh cough in weak pups; usually harmless.",
            },
            "weak_lungs": {
                "name": "pupcough (weak lungs)",
                "dc": 12,
                "next": None,
                "effect": "lungs never fully strengthen; -1 on Constitution saves.",
            },
        },
    },
    "hard_paw": {
        "label": "weeping-scale",
        "contagious": 0.30,
        "respiratory": True,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "weeping-scale",
                "dc": 16,
                "next": None,
                "effect": "weeping eyes and nose, hardened cracked pads, fever, tremors; -2 HP/sunrise, -25% hunt; often fatal in pups.",
                "hp_loss": 2,
                "hunt_mult": 0.75,
                "lethal": True,
            },
        },
    },
    "adenovirus": {
        "label": "yellow-fever",
        "contagious": 0.30,
        "respiratory": True,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "yellow-fever",
                "dc": 14,
                "next": None,
                "effect": "liver inflammation, jaundice; -8 hunger, +1 exhaustion.",
                "hunger_loss": 8,
                "exhaustion_gain": 1,
                "cure_on_save": True,
            },
        },
    },
    "herpesvirus": {
        "label": "whelp-sickness",
        "contagious": 0.25,
        "respiratory": True,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "whelp-sickness",
                "dc": 15,
                "next": None,
                "effect": "dangerous to pups; stillbirths; adults are carriers. -1 HP/sunrise to pups.",
                "hp_loss": 1,
                "juvenile_hp_loss": 4,
                "lethal": True,
            },
        },
    },
    "papillomatosis": {
        "label": "wart-mouth",
        "contagious": 0.10,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "wart-mouth",
                "dc": 10,
                "next": None,
                "effect": "warts on mouth; -4 hunger; usually clears.",
                "hunger_loss": 4,
                "cure_on_save": True,
            },
        },
    },
    "pseudorabies": {
        "label": "frenzy-virus",
        "contagious": 0.15,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "frenzy-virus",
                "dc": 16,
                "next": None,
                "effect": "severe itching, fever, neurological signs; often fatal; -8 mood, -1 HP.",
                "mood_loss": 8,
                "hp_loss": 1,
                "lethal": True,
            },
        },
    },
    "coronavirus": {
        "label": "gut-rot",
        "contagious": 0.20,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "gut-rot",
                "dc": 12,
                "next": None,
                "effect": "diarrhea and vomiting; -10 hunger, -8 thirst.",
                "hunger_loss": 10,
                "thirst_loss": 8,
                "cure_on_save": True,
            },
        },
    },
    "rot_lung": {
        "label": "rot-lung",
        "contagious": 0.42,
        "respiratory": True,
        "spread_stage": "fever",
        "stages": {
            "fever": {
                "name": "rot-lung (fever)",
                "dc": 13,
                "next": "wheeze",
                "effect": "marsh lung-fever; +1 exhaustion, -8 hunger.",
                "exhaustion_gain": 1,
                "hunger_loss": 8,
            },
            "wheeze": {
                "name": "rot-lung (wheeze)",
                "dc": 15,
                "next": "necrosis",
                "effect": "wheezing lung-rot; -1 HP/sunrise, -25% hunt.",
                "hp_loss": 1,
                "juvenile_hp_loss": 2,
                "hunt_mult": 0.75,
            },
            "necrosis": {
                "name": "rot-lung (necrosis)",
                "dc": 17,
                "next": None,
                "effect": "tissue blackens; -2 HP/sunrise; fatal without marsh-mallow, feverfew, mullein, or lungwort.",
                "hp_loss": 2,
                "juvenile_hp_loss": 4,
                "lethal": True,
            },
        },
    },

    # ----- BACTERIAL / VIRAL (incl. rabies) -----
    "rabies": {
        "label": "cloudmouth",
        "contagious": 0.0,
        "chronic": True,
        "spread_stage": "incubation",
        "stages": {
            "incubation": {
                "name": "cloudmouth (incubation)",
                "dc": 14,
                "next": "prodrome",
                "effect": "bite wound festers; anxiety, light sensitivity; no herb cures, but boneset/goldenrod may slow.",
                "mood_loss": 4,
            },
            "prodrome": {
                "name": "cloudmouth (prodrome)",
                "dc": 16,
                "next": "frenzy",
                "effect": "agitation and confusion; disadvantage on Int/Wis.",
                "mood_loss": 6,
                "exhaustion_gain": 1,
            },
            "frenzy": {
                "name": "cloudmouth (frenzy)",
                "dc": 18,
                "next": "terminal",
                "effect": "hydrophobia and rage; disadvantage on attacks and social.",
                "exhaustion_gain": 1,
                "blocks_conception": True,
                "lethal": True,
            },
            "terminal": {
                "name": "cloudmouth (terminal)",
                "dc": 20,
                "next": None,
                "effect": "paralysis and organ failure; lose 2 HP each sunrise.",
                "hp_loss": 2,
                "lethal": True,
            },
        },
    },
    "brucellosis": {
        "label": "bone-fever",
        "contagious": 0.0,
        "mating_contagious": 0.30,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "bone-fever",
                "dc": 15,
                "next": None,
                "effect": "causes stillbirths, weak pups; blocks conception; -1 HP to pups.",
                "hp_loss": 1,
                "blocks_conception": True,
                "juvenile_hp_loss": 3,
                "lethal": True,
            },
        },
    },
    "lyme": {
        "label": "tick-fever",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "tick-fever",
                "dc": 13,
                "next": None,
                "effect": "joint pain, fatigue, lethargy; -6 mood, -20% hunt.",
                "mood_loss": 6,
                "hunt_mult": 0.80,
                "cure_on_save": True,
            },
        },
    },
    "leptospirosis": {
        "label": "marsh-sickness",
        "contagious": 0.12,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "marsh-sickness",
                "dc": 14,
                "next": None,
                "effect": "kidney/liver damage; -12 thirst, +1 exhaustion.",
                "thirst_loss": 12,
                "exhaustion_gain": 1,
                "cure_on_save": True,
            },
        },
    },
    "tularemia": {
        "label": "rabbit-fever",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "rabbit-fever",
                "dc": 14,
                "next": None,
                "effect": "fever, swollen nodes, weakness; -6 mood, +1 exhaustion.",
                "mood_loss": 6,
                "exhaustion_gain": 1,
                "cure_on_save": True,
            },
        },
    },
    "tuberculosis": {
        "label": "consumption",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "consumption",
                "dc": 16,
                "next": None,
                "effect": "weight loss, coughing, weakness; -12 hunger, -1 HP.",
                "hunger_loss": 12,
                "hp_loss": 1,
                "lethal": True,
            },
        },
    },
    "anthrax": {
        "label": "black-death",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "black-death",
                "dc": 17,
                "next": None,
                "effect": "rapid fever, organ failure; -2 HP/sunrise.",
                "hp_loss": 2,
                "lethal": True,
            },
        },
    },
    "anaplasmosis": {
        "label": "blood-fever",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "blood-fever",
                "dc": 13,
                "next": None,
                "effect": "tick-borne fever; -6 mood, -10% hunt.",
                "mood_loss": 6,
                "hunt_mult": 0.90,
                "cure_on_save": True,
            },
        },
    },
    "ehrlichiosis": {
        "label": "tick-sickness",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "tick-sickness",
                "dc": 14,
                "next": None,
                "effect": "fever, bleeding; -6 mood, -1 HP.",
                "hp_loss": 1,
                "mood_loss": 6,
                "cure_on_save": True,
            },
        },
    },
    "salmonellosis": {
        "label": "sour-gut",
        "contagious": 0.15,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "sour-gut",
                "dc": 12,
                "next": None,
                "effect": "severe diarrhea, vomiting; -12 hunger, -10 thirst.",
                "hunger_loss": 12,
                "thirst_loss": 10,
                "cure_on_save": True,
            },
        },
    },

    # ----- PARASITIC -----
    "mange": {
        "label": "scabies-mange",
        "contagious": 0.36,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "scabies-mange",
                "dc": 14,
                "next": None,
                "effect": "intense itching, hair loss; -8 mood, -25% hunt.",
                "mood_loss": 8,
                "hunt_mult": 0.75,
                "cure_on_save": True,
            },
        },
    },
    "fleas": {
        "label": "fleas",
        "contagious": 0.36,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "fleas",
                "dc": 12,
                "next": None,
                "effect": "itching misery; -8 mood each sunrise.",
                "mood_loss": 8,
                "cure_on_save": True,
            },
        },
    },
    "heartworm": {
        "label": "heart-worm",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "heart-worm",
                "dc": 15,
                "next": "severe",
                "effect": "worms in heart/lungs; cough, fatigue; -15% hunt, -1 HP.",
                "hunt_mult": 0.85,
                "hp_loss": 1,
            },
            "severe": {
                "name": "heart-worm (severe)",
                "dc": 17,
                "next": None,
                "effect": "heart failure; -2 HP/sunrise; lethal.",
                "hp_loss": 2,
                "hunt_mult": 0.6,
                "lethal": True,
            },
        },
    },
    "hookworm": {
        "label": "blood-worm",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "blood-worm",
                "dc": 12,
                "next": None,
                "effect": "blood loss, anemia; -8 hunger, -1 HP.",
                "hunger_loss": 8,
                "hp_loss": 1,
                "cure_on_save": True,
            },
        },
    },
    "roundworm": {
        "label": "gut-worm",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "gut-worm",
                "dc": 10,
                "next": None,
                "effect": "weight loss, pot-belly; -8 hunger.",
                "hunger_loss": 8,
                "cure_on_save": True,
            },
        },
    },
    "tapeworm": {
        "label": "tape-worm",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "tape-worm",
                "dc": 11,
                "next": None,
                "effect": "weight loss, digestive issues; -10 hunger.",
                "hunger_loss": 10,
                "cure_on_save": True,
            },
        },
    },
    "whipworm": {
        "label": "whip-worm",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "whip-worm",
                "dc": 11,
                "next": None,
                "effect": "bloody diarrhea, weight loss; -8 hunger.",
                "hunger_loss": 8,
                "cure_on_save": True,
            },
        },
    },
    "parasites": {
        "label": "belly-worm",
        "contagious": 0.08,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "belly-worm",
                "dc": 11,
                "next": None,
                "effect": "internal parasites drain nutrition; -10 hunger.",
                "hunger_loss": 10,
                "cure_on_save": True,
            },
        },
    },
    "giardia": {
        "label": "beaver-fever",
        "contagious": 0.20,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "beaver-fever",
                "dc": 12,
                "next": None,
                "effect": "diarrhea, dehydration; -10 hunger, -12 thirst.",
                "hunger_loss": 10,
                "thirst_loss": 12,
                "cure_on_save": True,
            },
        },
    },
    "cryptosporidium": {
        "label": "water-sickness",
        "contagious": 0.15,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "water-sickness",
                "dc": 13,
                "next": None,
                "effect": "watery diarrhea; -8 hunger, -10 thirst.",
                "hunger_loss": 8,
                "thirst_loss": 10,
                "cure_on_save": True,
            },
        },
    },
    "toxoplasmosis": {
        "label": "mind-worm",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "mind-worm",
                "dc": 12,
                "next": None,
                "effect": "subtle behavior changes; -2 mood.",
                "mood_loss": 2,
                "cure_on_save": True,
            },
        },
    },
    "neosporosis": {
        "label": "whelp-fever",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "whelp-fever",
                "dc": 14,
                "next": None,
                "effect": "stillbirths, pup neurological issues; blocks conception.",
                "blocks_conception": True,
                "juvenile_hp_loss": 3,
                "cure_on_save": True,
            },
        },
    },
    "trichinosis": {
        "label": "flesh-worm",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "flesh-worm",
                "dc": 13,
                "next": None,
                "effect": "muscle pain, fever; -6 mood, -15% hunt.",
                "mood_loss": 6,
                "hunt_mult": 0.85,
                "cure_on_save": True,
            },
        },
    },
    "babesiosis": {
        "label": "blood-sickness",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "blood-sickness",
                "dc": 14,
                "next": None,
                "effect": "fever, anemia; -6 mood, -1 HP.",
                "hp_loss": 1,
                "mood_loss": 6,
                "cure_on_save": True,
            },
        },
    },

    # ----- VENOM / RASH -----
    "mild_poison": {
        "label": "mild venom",
        "contagious": 0.0,
        "spread_stage": "stung",
        "stages": {
            "stung": {
                "name": "insect sting",
                "dc": 11,
                "next": None,
                "effect": "swollen muzzle/paw; -6 mood.",
                "mood_loss": 6,
                "cure_on_save": True,
            },
            "venom": {
                "name": "snake venom",
                "dc": 14,
                "next": None,
                "effect": "venom burn, limb swelling; -8 mood, -1 HP.",
                "mood_loss": 8,
                "hp_loss": 1,
                "cure_on_save": True,
            },
        },
    },
    "poison_ivy": {
        "label": "poison ivy",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "poison ivy rash",
                "dc": 12,
                "next": None,
                "effect": "itching contact rash; -4 mood.",
                "mood_loss": 4,
                "cure_on_save": True,
            },
        },
    },

    # ----- ORGAN / SYSTEMIC -----
    "hepatitis": {
        "label": "liver-fire",
        "contagious": 0.18,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "liver-fire",
                "dc": 14,
                "next": None,
                "effect": "liver fever; -10 thirst.",
                "thirst_loss": 10,
                "cure_on_save": True,
            },
        },
    },
    "urinary_infection": {
        "label": "stone-water",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "stone-water",
                "dc": 11,
                "next": None,
                "effect": "painful urination; -10 thirst.",
                "thirst_loss": 10,
                "cure_on_save": True,
            },
        },
    },
    "redscratch": {
        "label": "redscratch",
        "contagious": 0.0,
        "mating_contagious": 0.45,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "redscratch",
                "dc": 14,
                "next": None,
                "effect": "itching sores, chills; -6 mood, +1 exhaustion, blocks conception.",
                "mood_loss": 6,
                "exhaustion_gain": 1,
                "thirst_loss": 8,
                "blocks_conception": True,
                "cure_on_save": True,
            },
        },
    },
    "pox": {
        "label": "pox",
        "contagious": 0.18,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "pox",
                "dc": 15,
                "next": None,
                "effect": "sores and fever; adults -1 HP, pups -3 HP.",
                "hp_loss": 1,
                "juvenile_hp_loss": 3,
                "lethal": True,
            },
        },
    },
    "shaking_sickness": {
        "label": "shaking-sickness",
        "contagious": 0.15,
        "spread_stage": "shaking",
        "stages": {
            "shaking": {
                "name": "shaking-sickness",
                "dc": 12,
                "next": "hemorrhage",
                "effect": "tremors; disadvantage on Dexterity; -6 mood.",
                "mood_loss": 6,
                "cure_on_save": True,
            },
            "hemorrhage": {
                "name": "shaking-sickness (hemorrhage)",
                "dc": 15,
                "next": None,
                "effect": "internal bleeding; -1 HP/sunrise; treat with yarrow or cobwebs.",
                "hp_loss": 1,
                "lethal": True,
            },
        },
    },
    "milk_fever": {
        "label": "milk-fever",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "milk-fever",
                "dc": 14,
                "next": None,
                "effect": "eclampsia; +1 exhaustion, -6 mood, -1 HP; treat with parsley, saffron, or feverfew.",
                "thirst_loss": 4,
                "hp_loss": 1,
                "exhaustion_gain": 1,
                "mood_loss": 6,
                "lethal": True,
            },
        },
    },

    # ----- PHYSICAL INJURIES / CHRONIC -----
    "tooth_infection": {
        "label": "tooth-rot",
        "contagious": 0.0,
        "stages": {
            "active": {
                "name": "tooth-rot",
                "dc": 12,
                "next": None,
                "effect": "painful tooth/gum; -6 hunger, -4 mood.",
                "hunger_loss": 6,
                "mood_loss": 4,
                "cure_on_save": True,
            },
        },
    },
    "arthritis": {
        "label": "joint-ache",
        "contagious": 0.0,
        "chronic": True,
        "stages": {
            "active": {
                "name": "joint-ache",
                "dc": 14,
                "next": None,
                "effect": "aching joints; -15% hunt, disadvantage on Dexterity.",
                "hunt_mult": 0.85,
                "cure_on_save": True,
            },
        },
    },
    "internal_bleeding": {
        "label": "hidden-bleed",
        "contagious": 0.0,
        "stages": {
            "active": {
                "name": "hidden-bleed",
                "dc": 16,
                "next": None,
                "effect": "internal bleeding; -2 HP/sunrise, +1 exhaustion.",
                "hp_loss": 2,
                "exhaustion_gain": 1,
                "lethal": True,
                "cure_on_save": True,
            },
        },
    },
    "heart_disease": {
        "label": "heart-weak",
        "contagious": 0.0,
        "chronic": True,
        "stages": {
            "active": {
                "name": "heart-weak",
                "dc": 16,
                "next": None,
                "effect": "weak heart; -1 HP/sunrise, disadvantage on strenuous checks.",
                "hp_loss": 1,
                "lethal": True,
                "cure_on_save": True,
            },
        },
    },
    "cancer": {
        "label": "growth-sickness",
        "contagious": 0.0,
        "chronic": True,
        "spread_stage": "lump",
        "stages": {
            "lump": {
                "name": "growth-sickness (lump)",
                "dc": 16,
                "next": "spreading",
                "effect": "deep swelling; -6 mood.",
                "mood_loss": 6,
            },
            "spreading": {
                "name": "growth-sickness (spreading)",
                "dc": 17,
                "next": "terminal",
                "effect": "growth spreads; -1 HP/sunrise, -30% hunt.",
                "hp_loss": 1,
                "hunt_mult": 0.7,
            },
            "terminal": {
                "name": "growth-sickness (terminal)",
                "dc": 19,
                "next": None,
                "effect": "body fails; lose 2 HP each sunrise.",
                "hp_loss": 2,
                "lethal": True,
            },
        },
    },
    "diabetes": {
        "label": "sugar-sickness",
        "contagious": 0.0,
        "stages": {
            "active": {
                "name": "sugar-sickness",
                "dc": 14,
                "next": None,
                "effect": "high blood sugar; +1 exhaustion/sunrise.",
                "exhaustion_gain": 1,
                "cure_on_save": True,
            },
        },
    },
    "kidney_stones": {
        "label": "stone-bladder",
        "contagious": 0.0,
        "stages": {
            "active": {
                "name": "stone-bladder",
                "dc": 15,
                "next": None,
                "effect": "sharp pain during urination; -4 mood, -8 thirst.",
                "mood_loss": 4,
                "thirst_loss": 8,
                "cure_on_save": True,
            },
        },
    },
    "burn": {
        "label": "fire-scorch",
        "contagious": 0.0,
        "stages": {
            "active": {
                "name": "fire-scorch",
                "dc": 12,
                "next": None,
                "effect": "skin damage from fire/heat; treat with cooling herbs.",
                "cure_on_save": True,
            },
        },
    },
    "abrasion": {
        "label": "scrape",
        "contagious": 0.0,
        "stages": {
            "active": {
                "name": "scrape",
                "dc": 8,
                "next": None,
                "effect": "superficial wound; clean and bandage.",
                "cure_on_save": True,
            },
        },
    },
    "asthma": {
        "label": "chestbind",
        "contagious": 0.0,
        "respiratory": True,
        "chronic": True,
        "spread_stage": "tight",
        "stages": {
            "tight": {
                "name": "chestbind (tight)",
                "dc": 12,
                "next": "wheeze",
                "effect": "airways clench; -15% hunt.",
                "hunt_mult": 0.85,
                "cure_on_save": True,
            },
            "wheeze": {
                "name": "chestbind (wheeze)",
                "dc": 14,
                "next": "attack",
                "effect": "relentless wheezing; -25% hunt.",
                "hunt_mult": 0.75,
                "mood_loss": 4,
            },
            "attack": {
                "name": "chestbind (attack)",
                "dc": 16,
                "next": None,
                "effect": "airway seizure; -1 HP; lethal.",
                "hp_loss": 1,
                "lethal": True,
            },
        },
    },
    "epilepsy": {
        "label": "shudderfit",
        "contagious": 0.0,
        "chronic": True,
        "spread_stage": "tremor",
        "stages": {
            "tremor": {
                "name": "shudderfit (tremor)",
                "dc": 12,
                "next": "convulsion",
                "effect": "muscle twitches; disadvantage on Dexterity.",
                "cure_on_save": True,
            },
            "convulsion": {
                "name": "shudderfit (convulsion)",
                "dc": 15,
                "next": "crisis",
                "effect": "full seizure; blocks field work; -8 mood.",
                "mood_loss": 8,
                "blocks_field": True,
            },
            "crisis": {
                "name": "shudderfit (crisis)",
                "dc": 17,
                "next": None,
                "effect": "seizures do not stop; -1 HP; lethal.",
                "hp_loss": 1,
                "lethal": True,
            },
        },
    },
    "bloat": {
        "label": "gutknot",
        "contagious": 0.0,
        "spread_stage": "swelling",
        "stages": {
            "swelling": {
                "name": "gutknot (swelling)",
                "dc": 13,
                "next": "torsion",
                "effect": "belly swells; -6 hunger.",
                "hunger_loss": 6,
                "cure_on_save": True,
            },
            "torsion": {
                "name": "gutknot (torsion)",
                "dc": 16,
                "next": "failure",
                "effect": "gut twists; -1 HP, -10 hunger; blocks field work.",
                "hp_loss": 1,
                "hunger_loss": 10,
                "blocks_field": True,
            },
            "failure": {
                "name": "gutknot (organ failure)",
                "dc": 18,
                "next": None,
                "effect": "organ shutdown; -2 HP; lethal.",
                "hp_loss": 2,
                "lethal": True,
            },
        },
    },

    # ----- MENTAL / BEHAVIORAL -----
    "shock_emotional": {
        "label": "grief-shock",
        "contagious": 0.0,
        "mental": True,
        "stages": {
            "active": {
                "name": "grief-shock",
                "dc": 12,
                "next": None,
                "effect": "numbness, denial; -8 mood.",
                "mood_loss": 8,
                "cure_on_save": True,
            },
        },
    },
    "shock_physical": {
        "label": "blood-shock",
        "contagious": 0.0,
        "stages": {
            "active": {
                "name": "blood-shock",
                "dc": 14,
                "next": None,
                "effect": "blood loss; chills, weakness; lethal.",
                "hp_loss": 1,
                "lethal": True,
            },
        },
    },
    "anxiety": {
        "label": "dread-sickness",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "uneasy",
        "stages": {
            "uneasy": {
                "name": "dread-sickness (uneasy)",
                "dc": 11,
                "next": "anxious",
                "effect": "every sound threatens; -4 mood.",
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "anxious": {
                "name": "dread-sickness (anxious)",
                "dc": 13,
                "next": "panic_prone",
                "effect": "heart hammers; -6 mood, disadvantage on Wisdom saves.",
                "mood_loss": 6,
            },
            "panic_prone": {
                "name": "dread-sickness (panic)",
                "dc": 15,
                "next": None,
                "effect": "panic attacks; -8 mood, +1 exhaustion; blocks courtship.",
                "mood_loss": 8,
                "exhaustion_gain": 1,
                "blocks_social": True,
            },
        },
    },
    "depression": {
        "label": "grief-sickness",
        "contagious": 0.0,
        "mental": True,
        "stages": {
            "active": {
                "name": "grief-sickness",
                "dc": 13,
                "next": None,
                "effect": "persistent sadness; -8 mood, -10 hunger.",
                "mood_loss": 8,
                "hunger_loss": 10,
                "cure_on_save": True,
            },
        },
    },
    "grief_melancholy": {
        "label": "melancholy",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "mourning",
        "stages": {
            "mourning": {
                "name": "melancholy (mourning)",
                "dc": 12,
                "next": "melancholy",
                "effect": "loss sits heavy; -6 mood.",
                "mood_loss": 6,
                "cure_on_save": True,
            },
            "melancholy": {
                "name": "melancholy (deep)",
                "dc": 14,
                "next": "hollow",
                "effect": "joy feels far; -8 mood, -10 hunger.",
                "mood_loss": 8,
                "hunger_loss": 10,
            },
            "hollow": {
                "name": "melancholy (hollow)",
                "dc": 16,
                "next": None,
                "effect": "empty; blocks socialize.",
                "mood_loss": 6,
                "blocks_social": True,
            },
        },
    },
    "insomnia": {
        "label": "sleeplessness",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "restless",
        "stages": {
            "restless": {
                "name": "sleeplessness (restless)",
                "dc": 11,
                "next": "sleepless",
                "effect": "sleep won't come; -4 mood.",
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "sleepless": {
                "name": "sleeplessness (sleepless)",
                "dc": 13,
                "next": "exhaustion_cascade",
                "effect": "days blur; +1 exhaustion, -6 mood.",
                "mood_loss": 6,
                "exhaustion_gain": 1,
            },
            "exhaustion_cascade": {
                "name": "sleeplessness (exhaustion drain)",
                "dc": 15,
                "next": None,
                "effect": "body on fumes; +1 exhaustion, -8 mood, -15% hunt.",
                "mood_loss": 8,
                "exhaustion_gain": 1,
                "hunt_mult": 0.85,
            },
        },
    },
    "night_terrors": {
        "label": "night-terrors",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "restless_nights",
        "stages": {
            "restless_nights": {
                "name": "night-terrors (restless)",
                "dc": 11,
                "next": "screaming_dreams",
                "effect": "sleep shatters; -4 mood.",
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "screaming_dreams": {
                "name": "night-terrors (screaming dreams)",
                "dc": 13,
                "next": "sleep_panic",
                "effect": "cries at night; -6 mood, +1 exhaustion.",
                "mood_loss": 6,
                "exhaustion_gain": 1,
            },
            "sleep_panic": {
                "name": "night-terrors (sleep panic)",
                "dc": 15,
                "next": None,
                "effect": "fear of sleep; -8 mood, blocks field work.",
                "mood_loss": 8,
                "blocks_field": True,
            },
        },
    },
    "dementia": {
        "label": "mind-fade",
        "contagious": 0.0,
        "chronic": True,
        "mental": True,
        "spread_stage": "forgetful",
        "stages": {
            "forgetful": {
                "name": "mind-fade (forgetful)",
                "dc": 14,
                "next": "confused",
                "effect": "names/trails slip; disadvantage on Intelligence.",
            },
            "confused": {
                "name": "mind-fade (confused)",
                "dc": 16,
                "next": "lost",
                "effect": "time blurs; -8 mood.",
                "mood_loss": 8,
            },
            "lost": {
                "name": "mind-fade (lost)",
                "dc": 18,
                "next": None,
                "effect": "pack faces strangers; blocks socialize.",
                "mood_loss": 6,
                "blocks_social": True,
            },
        },
    },
    "delirium": {
        "label": "fever-dream",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "feverish",
        "stages": {
            "feverish": {
                "name": "fever-dream (feverish)",
                "dc": 12,
                "next": "wandering",
                "effect": "fever dreams; -4 mood.",
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "wandering": {
                "name": "fever-dream (wandering)",
                "dc": 14,
                "next": "incoherent",
                "effect": "disadvantage on Intelligence; -6 mood.",
                "mood_loss": 6,
            },
            "incoherent": {
                "name": "fever-dream (incoherent)",
                "dc": 16,
                "next": None,
                "effect": "speech broken; blocks field work.",
                "mood_loss": 8,
                "blocks_field": True,
            },
        },
    },
    "obsession": {
        "label": "fixation",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "fixated",
        "stages": {
            "fixated": {
                "name": "fixation (fixated)",
                "dc": 12,
                "next": "compulsive",
                "effect": "one thought won't leave; -4 mood.",
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "compulsive": {
                "name": "fixation (compulsive)",
                "dc": 14,
                "next": "tunnel_vision",
                "effect": "rituals take over; -6 mood, -15% hunt.",
                "mood_loss": 6,
                "hunt_mult": 0.85,
            },
            "tunnel_vision": {
                "name": "fixation (tunnel vision)",
                "dc": 16,
                "next": None,
                "effect": "blocks socialize.",
                "mood_loss": 8,
                "blocks_social": True,
            },
        },
    },
    "pack_madness": {
        "label": "pack-madness",
        "contagious": 0.08,
        "mental": True,
        "spread_stage": "wary",
        "stages": {
            "wary": {
                "name": "pack-madness (wary)",
                "dc": 12,
                "next": "paranoid",
                "effect": "eyes everywhere; -4 mood.",
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "paranoid": {
                "name": "pack-madness (paranoid)",
                "dc": 14,
                "next": "break",
                "effect": "packmates seem enemies; -8 mood.",
                "mood_loss": 8,
            },
            "break": {
                "name": "pack-madness (break)",
                "dc": 16,
                "next": None,
                "effect": "mind turns on den; blocks social.",
                "mood_loss": 6,
                "blocks_social": True,
            },
        },
    },
    "chronic_stress": {
        "label": "tension-sickness",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "tense",
        "stages": {
            "tense": {
                "name": "tension-sickness (tense)",
                "dc": 11,
                "next": "strained",
                "effect": "shoulders never drop; -4 mood.",
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "strained": {
                "name": "tension-sickness (strained)",
                "dc": 13,
                "next": "frayed",
                "effect": "tasks feel heavy; -6 mood.",
                "mood_loss": 6,
            },
            "frayed": {
                "name": "tension-sickness (frayed)",
                "dc": 15,
                "next": None,
                "effect": "one more will snap; -8 mood, +1 exhaustion, -20% hunt.",
                "mood_loss": 8,
                "exhaustion_gain": 1,
                "hunt_mult": 0.8,
            },
        },
    },
    "eating_distress": {
        "label": "food-refusal",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "picky",
        "stages": {
            "picky": {
                "name": "food-refusal (picky)",
                "dc": 11,
                "next": "refusing",
                "effect": "food turns to ash; -6 hunger, -4 mood.",
                "hunger_loss": 6,
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "refusing": {
                "name": "food-refusal (refusing)",
                "dc": 13,
                "next": "wasting",
                "effect": "won't keep meals; -10 hunger, -6 mood.",
                "hunger_loss": 10,
                "mood_loss": 6,
            },
            "wasting": {
                "name": "food-refusal (wasting)",
                "dc": 15,
                "next": None,
                "effect": "body thins; -12 hunger, -1 HP.",
                "hunger_loss": 12,
                "hp_loss": 1,
                "mood_loss": 6,
            },
        },
    },
    "feral_shift": {
        "label": "feral-shift",
        "contagious": 0.0,
        "chronic": True,
        "mental": True,
        "spread_stage": "restless",
        "stages": {
            "restless": {
                "name": "feral-shift (restless)",
                "dc": 13,
                "next": "feral",
                "effect": "mind skitters to wild; -6 mood.",
                "mood_loss": 6,
            },
            "feral": {
                "name": "feral-shift (feral)",
                "dc": 15,
                "next": "unsentient",
                "effect": "speech frays; blocks social.",
                "mood_loss": 8,
                "blocks_social": True,
                "hunt_mult": 0.9,
            },
            "unsentient": {
                "name": "mind-fracture (unsentient)",
                "dc": 17,
                "next": None,
                "effect": "lost to instinct; cannot hunt, patrol, explore, court, or socialize.",
                "blocks_social": True,
                "blocks_field": True,
                "hunt_mult": 0.5,
                "mood_loss": 6,
            },
        },
    },

    # ----- DIGESTIVE / METABOLIC -----
    "diarrhea": {
        "label": "belly-rot",
        "contagious": 0.0,
        "mating_contagious": 0.12,
        "stages": {
            "active": {
                "name": "belly-rot",
                "dc": 11,
                "next": None,
                "effect": "gut sickness; -8 hunger.",
                "hunger_loss": 8,
                "cure_on_save": True,
            },
        },
    },
    "constipation": {
        "label": "block-belly",
        "contagious": 0.0,
        "stages": {
            "active": {
                "name": "block-belly",
                "dc": 10,
                "next": None,
                "effect": "blocked bowels; -4 mood, -10% hunt.",
                "mood_loss": 4,
                "hunt_mult": 0.9,
                "cure_on_save": True,
            },
        },
    },
    "wasting_sickness": {
        "label": "wasting-ill",
        "contagious": 0.0,
        "chronic": True,
        "spread_stage": "waning",
        "stages": {
            "waning": {
                "name": "wasting-ill (waning)",
                "dc": 14,
                "next": "emaciated",
                "effect": "body sheds weight; -12 hunger, -15% hunt.",
                "hunger_loss": 12,
                "hunt_mult": 0.85,
            },
            "emaciated": {
                "name": "wasting-ill (emaciated)",
                "dc": 16,
                "next": "cachectic",
                "effect": "muscle wastes; -1 HP, -15 hunger.",
                "hunger_loss": 15,
                "hp_loss": 1,
                "hunt_mult": 0.7,
            },
            "cachectic": {
                "name": "wasting-ill (cachectic)",
                "dc": 18,
                "next": None,
                "effect": "final wasting; lose 2 HP/sunrise.",
                "hp_loss": 2,
                "lethal": True,
            },
        },
    },

    # ----- ENVIRONMENTAL -----
    "river_rot": {
        "label": "river-rot",
        "contagious": 0.0,
        "chronic": True,
        "spread_stage": "fouled",
        "stages": {
            "fouled": {
                "name": "river-rot (fouled gut)",
                "dc": 13,
                "next": "bloody_flux",
                "effect": "sewage-tainted water; -10 hunger, -6 thirst.",
                "hunger_loss": 10,
                "thirst_loss": 6,
            },
            "bloody_flux": {
                "name": "river-rot (bloody flux)",
                "dc": 17,
                "next": "failing",
                "effect": "bowels turn; -1 HP, -14 hunger, -12 thirst.",
                "hp_loss": 1,
                "hunger_loss": 14,
                "thirst_loss": 12,
            },
            "failing": {
                "name": "river-rot (failing)",
                "dc": 20,
                "next": None,
                "effect": "can't keep water; -3 HP/sunrise.",
                "hp_loss": 3,
                "lethal": True,
            },
        },
    },
}

# Helper functions for disease parsing
DISEASE_STAGES = COUGH_STAGES
LEGACY_COUGH_STAGES = frozenset(COUGH_STAGES.keys())

MULTI_STAGE_DISEASES = frozenset({
    "rabies", "wasting_sickness", "river_rot", "cancer", "dementia",
    "feral_shift", "insomnia", "anxiety", "grief_melancholy", "delirium",
    "pack_madness", "obsession", "night_terrors", "chronic_stress",
    "eating_distress", "heartworm", "pupcough", "leafbare_cough",
    "mild_poison", "shaking_sickness", "rot_lung", "asthma",
    "epilepsy", "bloat",
})

MENTAL_DISEASES = frozenset({
    "shock_emotional", "anxiety", "depression", "grief_melancholy",
    "insomnia", "night_terrors", "dementia", "delirium", "obsession",
    "pack_madness", "chronic_stress", "eating_distress", "feral_shift",
})

HERB_CURE_STAGES: Dict[str, frozenset[str]] = {
    "wasting_sickness": frozenset({"waning", "emaciated"}),
    "cancer": frozenset({"lump", "spreading"}),
    "dementia": frozenset({"forgetful", "confused"}),
    "feral_shift": frozenset({"restless", "feral"}),
    "insomnia": frozenset({"restless", "sleepless"}),
    "anxiety": frozenset({"uneasy", "anxious", "panic_prone"}),
    "grief_melancholy": frozenset({"mourning", "melancholy"}),
    "delirium": frozenset({"feverish", "wandering"}),
    "pack_madness": frozenset({"wary", "paranoid"}),
    "obsession": frozenset({"fixated", "compulsive"}),
    "night_terrors": frozenset({"restless_nights", "screaming_dreams"}),
    "chronic_stress": frozenset({"tense", "strained"}),
    "eating_distress": frozenset({"picky", "refusing"}),
    "shock_emotional": frozenset({"active"}),
    "heartworm": frozenset({"active"}),
    "pupcough": frozenset({"active"}),
    "leafbare_cough": frozenset({"chill", "hacking"}),
    "asthma": frozenset({"tight", "wheeze"}),
    "epilepsy": frozenset({"tremor", "convulsion"}),
    "bloat": frozenset({"swelling"}),
}


def parse_disease(raw: str) -> Tuple[Optional[str], Optional[str]]:
    if not raw:
        return None, None
    if raw in LEGACY_COUGH_STAGES:
        return "cough", raw
    if ":" in raw:
        key, stage = raw.split(":", 1)
        if key in DISEASES and stage in DISEASES[key]["stages"]:
            return key, stage
    if raw in DISEASES:
        stages = DISEASES[raw]["stages"]
        stage = next(iter(stages.keys()))
        return raw, stage
    return None, None


def get_stage_info(disease_key: str, stage: str) -> Optional[Dict]:
    disease = DISEASES.get(disease_key)
    if not disease:
        return None
    return disease["stages"].get(stage)


# ============================================================================
# 2. HERB COMPENDIUM (full, with preparations)
# ============================================================================

def _h(name, rarity, effect, packs=(), cures=(), poison=False, habitat=("wild",),
       side_effects="", preparation="", preparations=None, method_reqs=None):
    if preparations is None:
        methods = []
        prep_lower = preparation.lower()
        for kw in ["chewed", "poultice", "tea", "decoction", "infusion", "ointment",
                   "juice", "raw", "dried", "cooked", "sap", "rub"]:
            if kw in prep_lower:
                methods.append(kw)
        if not methods:
            methods.append("default")
        preparations = {m: preparation for m in methods}
    if method_reqs is None:
        method_reqs = {}
    return {
        "name": name,
        "rarity": rarity,
        "packs": packs,
        "effect": effect,
        "cures": cures,
        "poison": poison,
        "habitat": habitat,
        "side_effects": side_effects,
        "preparation": preparation,
        "preparations": preparations,
        "method_requirements": method_reqs,
    }

HERBS = {
    # ----- COMMON HERBS -----
    "adders_tongue": _h(
        "Adder's Tongue",
        "common",
        "reroll failed poison save with advantage if within 1 minute of sting; juice soothes inflamed eyes and draws out wound swelling.",
        cures=("mild_poison", "swollen_eye", "deep_gash", "shaking_sickness"),
        side_effects="can cause swelling, blistering, itching; toxic in large amounts - nausea, vomiting, diarrhea.",
        preparation="fresh roots or leaves simmered in milk; juice infused in apple cider.",
        method_reqs={"mild_poison": "juice", "swollen_eye": "juice", "deep_gash": "juice", "shaking_sickness": "simmered_milk"}
    ),
    "alder_bark": _h(
        "Alder Bark",
        "uncommon",
        "chewed and applied to wounds - prevents infection and reduces swelling; soothes toothache and gum pain; settles gut sickness. fresh bark causes vomiting; only use dried.",
        packs=("mistmoor",),
        cures=("tooth_infection", "infected_wound", "diarrhea"),
        side_effects="fresh bark causes severe vomiting; prolonged use may cause low potassium, heart problems.",
        preparation="bark chewed directly or applied as poultice; decoction used as mouthwash.",
        method_reqs={"tooth_infection": "chewed", "infected_wound": "poultice", "diarrhea": "decoction"}
    ),
    "arnica": _h(
        "Arnica",
        "rare",
        "halves bruise and sprain recovery (external only); anti-inflammatory poultice for joint pain. never eat - internal use is lethal.",
        packs=("greyspire",),
        cures=("sprained_leg", "punctured_paw", "arthritis"),
        side_effects="highly toxic if ingested - nausea, vomiting, irregular heartbeat, coma; topical may cause itching or rash.",
        preparation="external use only as gel, cream, or ointment; homeopathic dilutions are safer.",
    ),
    "beech_leaves": _h(
        "Beech Leaves",
        "common",
        "carry herbs; nut oil prevents infection and clears minor surface wounds. leaf tea is mildly antiseptic and eases leaf-bare cough.",
        cures=("leafbare_cough", "infected_wound"),
        side_effects="excessive intake may be toxic; unripe nuts cause vomiting, diarrhea, abdominal pain.",
        preparation="leaves used in teas; ointments for burns, sores, and ulcers.",
    ),
    "bindweed": _h(
        "Bindweed Vines",
        "common",
        "relieves gut complaints and urinary problems; immune-stimulating tonic for fever. strong laxative in large amounts - use sparingly.",
        cures=("eating_distress", "urinary_infection", "influenza", "constipation"),
        side_effects="strong laxative; large amounts cause stomach pain; toxic to livestock.",
        preparation="leaves may be cooked to reduce oxalic acid; seeds used as purgative.",
    ),
    "blackberry": _h(
        "Blackberry (Bramble)",
        "common",
        "soothes insect stings and ends non-magical venom; root bark is strongly astringent - settles diarrhea and gut upsets.",
        cures=("diarrhea", "eating_distress", "infected_wound", "mild_poison"),
        side_effects="prolonged or high-dose use may cause digestive upset or constipation from tannins.",
        preparation="leaves chewed into pulp and applied to stings; root bark used internally.",
    ),
    "boneset": _h(
        "Boneset",
        "common",
        "reroll failed disease save with advantage; take the better result. slows early rabies (one sunrise, no cure). eases deep respiratory congestion and fever pain. fresh plant is toxic - always dried.",
        packs=("mistmoor",),
        cures=("influenza", "leafbare_cough"),
        side_effects="large amounts cause severe diarrhea; contains hepatotoxic pyrrolizidine alkaloids - liver damage.",
        preparation="traditional use at 2g of leaves and flowers.",
    ),
    "borage": _h(
        "Borage",
        "common",
        "extra milk for nursing mother; one additional pup. leaf reduces fever and eases cough. must be used fresh - drying destroys properties.",
        cures=("influenza", "leafbare_cough", "anxiety", "depression"),
        side_effects="upset stomach, headache, nausea; possible liver damage with prolonged use.",
        preparation="must be used fresh, never dried; leaves and roots chewed and eaten.",
    ),
    "broom": _h(
        "Broom",
        "common",
        "bind broken bones; move at half speed without worsening. anti-inflammatory poultice for bruising. toxic in large doses - cardiac effects and weakness.",
        cures=("fractured_rib", "sprained_leg", "broken_jaw"),
        side_effects="contains toxic alkaloids - weakness, blurred vision, cardiac arrhythmias, nausea.",
        preparation="1 tsp chopped flower shoots in water 3-4 times daily - traditional.",
    ),
    "burdock_root": _h(
        "Burdock Root",
        "common",
        "poultice draws infection from bites and open wounds after 24h rest. anti-inflammatory blood purifier - eases skin disease and early growth-sickness. diuretic; avoid when dehydrated.",
        cures=("infected_wound", "deep_gash", "mange", "cancer"),
        side_effects="generally safe; may cause allergic reactions; high doses may cause liver injury.",
        preparation="root dug up, washed, chewed into pulp, applied to bites and wounds.",
    ),
    "burnet": _h(
        "Burnet",
        "common",
        "leaf applied to cuts staunches bleeding; astringent tonic settles gut and internal wounds. 1 leaf per day ignores first exhaustion from a forced march.",
        cures=("sprained_leg", "diarrhea", "deep_gash"),
        side_effects="limited documented side effects.",
        preparation="applied as poultice; root used as astringent and tonic.",
    ),
    "catchweed": _h(
        "Catchweed Burrs",
        "common",
        "burrs hold poultices in place; extends duration 4 hours without harming the pelt. whole plant has mild diuretic and antispasmodic properties - clears urinary complaints.",
        cures=("urinary_infection",),
        side_effects="limited documented side effects.",
        preparation="burrs attached to pelt over poultices.",
    ),
    "cattail": _h(
        "Cattail",
        "common",
        "pollen is hemostatic - stops bleeding like yarrow; analgesic; mildly antiseptic.",
        packs=("silverrush", "mistmoor"),
        cures=("deep_gash",),
        side_effects="generally safe short-term; may cause mild gi discomfort; avoid in pregnancy.",
        preparation="pollen taken as capsules; young shoots and rhizomes eaten.",
    ),
    "celandine": _h(
        "Celandine",
        "common",
        "removes eye swelling and strengthens weak eyesight within 1 hour. treats liver complaints and eases respiratory spasms. large doses cause vomiting - use sparingly.",
        cures=("swollen_eye", "hepatitis", "leafbare_cough", "gallstones"),
        side_effects="large quantities cause vomiting and purging; fresh juice is local irritant; may cause dry mouth.",
        preparation="juice trickled into the eye.",
    ),
    "chamomile": _h(
        "Chamomile",
        "common",
        "advantage on wisdom saves vs fear for 1 hour. reduces fever, calms nerves, soothes eating troubles, and eases grief. mildly sedative - aids sleep and recovery.",
        habitat=("compound",),
        cures=("anxiety", "insomnia", "eating_distress", "influenza", "grief_melancholy", "delirium"),
        side_effects="generally safe; allergic reactions possible, especially in ragweed-sensitive wolves.",
        preparation="leaves and flowers consumed; tea made from flowers.",
    ),
    "chervil": _h(
        "Chervil",
        "common",
        "removes nausea; eases redscratch itch; leaf juice clears infected wounds. stimulates appetite and eases gut troubles in wasting wolves.",
        cures=("infected_wound", "diarrhea", "redscratch", "eating_distress", "wasting_sickness"),
        side_effects="generally safe; potential for mild gi discomfort or allergic reactions.",
        preparation="juice extracted from leaves or root for infected wounds and bellyache.",
    ),
    "chickweed": _h(
        "Chickweed",
        "common",
        "ends green-cough (3 doses per 24 hours); poultice soothes skin conditions and reduces mild swelling. anti-bacterial - promotes wound healing.",
        habitat=("roadside", "compound"),
        cures=("cough", "leafbare_cough", "infected_wound"),
        side_effects="high doses may cause vertigo, weakness, headache, difficulty breathing.",
        preparation="used as tea or topical application.",
    ),
    "cobnuts": _h(
        "Cobnuts",
        "common",
        "+1 stealth when approaching prey. rich in protein and fiber; supports steady energy on patrol.",
        cures=(),
        side_effects="may trigger allergic reactions in tree-nut-sensitive individuals.",
        preparation="eaten raw or cooked.",
    ),
    "cobwebs": _h(
        "Cobwebs",
        "common",
        "auto-stabilize dying wolf; bandages deep gashes and burns. required for `/medic action:field_dressing`. can increase infection risk if wound is already dirty - clean wound first.",
        cures=("dying", "deep_gash", "shaking_sickness", "scorched_hide"),
        side_effects="can cause increased risk of infection if wound is dirty.",
        preparation="gathered in a swath and applied to bleeding wound; wrapped around injury.",
    ),
    "coltsfoot": _h(
        "Coltsfoot",
        "common",
        "ends green-cough after 1 dose; leaf pulp soothes cracked and sore paw pads. toxic long-term - contains alkaloids that damage the liver; use short-term only.",
        cures=("cough", "leafbare_cough", "punctured_paw", "asthma"),
        side_effects="likely unsafe - contains hepatotoxic pyrrolizidine alkaloids that damage liver and lungs.",
        preparation="leaves chewed to pulp and eaten for shortness of breath.",
    ),
    "comfrey": _h(
        "Comfrey",
        "uncommon",
        "poultice heals 1d4 hp on deep wounds; stimulates tissue regeneration and prevents scar tissue. do not eat - pyrrolizidine alkaloids cause fatal liver damage.",
        packs=("thistlehide",),
        cures=("fractured_rib", "broken_jaw", "sprained_leg", "deep_gash"),
        side_effects="do not take internally - contains pyrrolizidine alkaloids causing fatal liver damage; may cause abortion.",
        preparation="roots chewed into poultice and applied externally.",
    ),
    "coneflower": _h(
        "Coneflower (Echinacea)",
        "common",
        "advantage on infection saves within 1h of injury; boosts immune system. shortens cough and fever duration. allergic reactions possible - watch for hives.",
        packs=("greyspire",),
        cures=("infected_wound", "influenza", "leafbare_cough"),
        side_effects="common: nausea, upset stomach; allergic reactions possible including anaphylaxis.",
        preparation="tea, tincture, tablet, or capsule.",
    ),
    "daisy": _h(
        "Daisy",
        "common",
        "ignore arthritis and joint pain penalties for 8 hours; leaf promotes wound healing and skin repair. tea eases sleeplessness and mild low spirits.",
        cures=("deep_gash", "leafbare_cough", "infected_wound", "insomnia", "sprained_leg", "arthritis"),
        side_effects="mildly toxic to humans and pets.",
        preparation="various preparations; tea, topical applications.",
    ),
    "dandelion": _h(
        "Dandelion",
        "common",
        "soothes stings; reduces headache pain. diuretic - helps flush fever and promotes liver health. eases gut troubles and appetite loss.",
        habitat=("roadside", "compound"),
        cures=("eating_distress", "hepatitis", "influenza", "leptospirosis"),
        side_effects="generally safe; rare upset stomach or diarrhea; allergic reactions possible.",
        preparation="leaves and stems eaten; root made into tea.",
    ),
    "dock": _h(
        "Dock",
        "common",
        "restores cracked paw pads after 1 day rest; leaf chewed and applied soothes scratches. treats liver complaints and gut sickness.",
        cures=("leafbare_cough", "hepatitis", "diarrhea"),
        side_effects="oxalate content may cause gi symptoms or kidney damage; avoid mature or uncooked leaves.",
        preparation="leaf chewed and applied to scratches.",
    ),
    "douglas_sagewort": _h(
        "Douglas' Sagewort",
        "common",
        "prevents infection 24h; soothes poison-ivy rash and insect stings. antibacterial - treats rashes and abrasions. internal use may have mutagenic effects; use topically.",
        packs=("greyspire",),
        cures=("poison_ivy", "infected_wound", "mild_poison"),
        side_effects="contains thujone with mild psychoactive properties; internal use may have mutagenic effects.",
        preparation="leaves and stems dried, burned as incense or drunk as tea.",
    ),
    "edelweiss": _h(
        "Edelweiss",
        "very_rare",
        "ends bellyache and eating troubles; suppresses cough 4h. anti-inflammatory and antimicrobial. very rare; found only at altitude.",
        packs=("greyspire",),
        cures=("diarrhea", "eating_distress"),
        side_effects="generally safe; coumarins may damage liver and kidneys in large amounts.",
        preparation="various traditional preparations.",
    ),
    "elder": _h(
        "Elder (external)",
        "common",
        "treats sprains; toxic if eaten (dc 14 or 2d4 poison). bark and leaf poultice reduce swelling. unripe berries and all internal parts cause severe vomiting.",
        cures=("sprained_leg",),
        poison=True,
        side_effects="poisoning: vomiting, diarrhea, weakness, coma; unripe berries and other parts toxic.",
        preparation="requires careful preparation; unripe or uncooked parts are toxic.",
    ),
    "elderberry": _h(
        "Elderberry",
        "rare",
        "advantage on disease saves for 3 sunrises; rich in antioxidants. reduces weeping-scale and flu symptoms. raw or unripe berries cause violent vomiting - must be fully ripe.",
        packs=("mistmoor",),
        cures=("hard_paw", "influenza", "leafbare_cough"),
        side_effects="raw or unripe berries, leaves, stems are toxic - can cause nausea, vomiting, severe diarrhea; cooked berries are safe.",
        preparation="must be cooked; raw or unripe berries are toxic.",
    ),
    "fennel": _h(
        "Fennel",
        "common",
        "extra day without food before exhaustion sets in; loosens phlegm and eases chest tightness. settles digestive cramps and eating troubles. antifungal and antibacterial.",
        habitat=("compound",),
        cures=("eating_distress", "leafbare_cough", "bloat"),
        side_effects="generally safe; rare: stomach upset, seizures; oil may cause hallucinations.",
        preparation="seeds used as spice or tea; oil used with caution.",
    ),
    "feverfew": _h(
        "Feverfew",
        "common",
        "reduces inflammation and fever; advantage on disease saves for 1 day. treats swollen eyes and head pain. chewing fresh leaves causes mouth sores - use dried only.",
        cures=("influenza", "redscratch", "pox", "rot_lung", "milk_fever", "swollen_eye", "leafbare_cough"),
        side_effects="5-15% develop mouth ulcers or gi irritation; may increase bleeding; abrupt stop may cause rebound headaches.",
        preparation="dried leaf or extract taken orally.",
    ),
    "goldenrod": _h(
        "Goldenrod",
        "rare",
        "+2 hp per 8h rest. slows early rabies (+2 next save, no cure). anti-inflammatory and diuretic - clears urinary infection and wound infection.",
        cures=("infected_wound", "deep_gash", "urinary_infection", "lyme"),
        side_effects="generally well-tolerated; may cause heartburn; allergic reactions possible.",
        preparation="tea, tincture, or supplement.",
    ),
    "heather": _h(
        "Heather",
        "common",
        "sweetens bitter herb mixtures. tea is anti-inflammatory and antiseptic - eases gut upsets, mild cough, and nervy tension.",
        cures=("diarrhea", "leafbare_cough", "anxiety"),
        side_effects="possibly safe; no side effects reported; safety in pregnancy not established.",
        preparation="tender tops and flowers made into decoction; roots in milk for diarrhea.",
    ),
    "honey": _h(
        "Honey",
        "common",
        "feeds starving pups (+10 hunger, -1 exhaustion); sweetens `/pupcare action:feed`. adults: -1 starvation exhaustion when depleted. soothes smoke-damaged throat and cough; antibacterial wound dressing.",
        cures=("leafbare_cough", "deep_gash"),
        side_effects="generally safe; may cause blood sugar spikes; allergic reactions possible.",
        preparation="used directly or mixed with other herbs.",
    ),
    "horsetail": _h(
        "Horsetail",
        "common",
        "+3 medicine to stabilize dying; hemostatic poultice closes wounds and stops bleeding. antimicrobial - treats torn claws, paw wounds, and urinary complaints. long-term use may cause thiamine deficiency.",
        cures=("deep_gash", "torn_claw", "punctured_paw", "urinary_infection"),
        side_effects="contains thiaminase - long-term use may cause thiamine deficiency; high doses may cause liver injury.",
        preparation="tea, poultice, or supplement.",
    ),
    "ivy_vines": _h(
        "Ivy Vines",
        "common",
        "preserves dried herbs 2 extra weeks. leaf extract thins chest mucus, opens airways, and eases fever congestion. mild expectorant.",
        cures=("leafbare_cough", "influenza", "asthma"),
        side_effects="rarely causes noticeable side effects; nausea and vomiting possible with excessive doses.",
        preparation="pill, powder, or extract.",
    ),
    "jewelweed": _h(
        "Jewelweed",
        "common",
        "touch-me-not sap neutralizes poison-ivy rash; cools bee and nettle stings. anti-fungal; soothes liver complaints and eases gut sickness.",
        habitat=("roadside", "wild"),
        cures=("poison_ivy", "mild_poison", "hepatitis", "diarrhea"),
        side_effects="possibly safe; may cause digestive upset if consumed in high amounts.",
        preparation="sap applied directly to skin; tea traditionally used.",
    ),
    "juniper_berry": _h(
        "Juniper Berries",
        "common",
        "cures mild poison or nausea. antiseptic berries slow infection in minor wounds. anti-inflammatory and diuretic - clears urinary complaints. excessive use damages kidneys over time.",
        cures=("mild_poison", "diarrhea", "urinary_infection"),
        side_effects="allergic reactions possible; excessive use may cause kidney damage; large doses cause convulsions.",
        preparation="berries eaten directly; leaves used for respiratory issues.",
    ),
    "knotgrass": _h(
        "Knotgrass",
        "common",
        "cures diarrhea; kills internal parasites and worms in 1 day; drives off fleas. eases urinary complaints and leaf-bare cough. no serious side effects reported.",
        habitat=("roadside", "compound"),
        cures=("diarrhea", "fleas", "leafbare_cough", "urinary_infection", "parasites"),
        side_effects="no serious side effects reported; may cause mild gi discomfort.",
        preparation="1.5g taken 3-5 times daily; infusions for kidney and bladder conditions.",
    ),
    "labrador_tea": _h(
        "Labrador Tea",
        "common",
        "ends wheezing for 4 hours; settles gut sickness; source of vitamin c. toxic in large amounts - causes vomiting, diarrhea, paralysis, and death. maximum one dose per day.",
        cures=("leafbare_cough", "diarrhea", "asthma"),
        side_effects="contains ledol and grayanotoxin - toxic; large amounts cause vomiting, gastroenteritis, diarrhea, delirium, spasms, death.",
        preparation="dried leaves brewed as tea - maximum one cup per day.",
    ),
    "lambs_ear": _h(
        "Lamb's Ear",
        "common",
        "fuzzy leaves pressed on wounds stop bleeding and soothe insect stings. advantage on disease saves until next sunrise. antiseptic; no known toxicity.",
        habitat=("roadside",),
        cures=("infected_wound", "mild_poison"),
        side_effects="not known to be toxic; possible allergic reactions.",
        preparation="fuzzy leaves applied directly to skin as compress.",
    ),
    "lavender": _h(
        "Lavender",
        "common",
        "cures fever and chills; hides death-scent at burial. calming - advantage vs fear when inhaled; eases grief and nightmares. large oral doses cause nausea.",
        habitat=("compound",),
        cures=("influenza", "anxiety", "insomnia", "grief_melancholy", "night_terrors"),
        side_effects="generally well-tolerated; allergic skin reactions possible; large oral doses may cause nausea.",
        preparation="leaves or flowers eaten; aromatherapy; essential oil - diluted.",
    ),
    "mullein": _h(
        "Mullein",
        "rare",
        "heals yellowcough and rot-lung lung damage; medics use it for full recovery. expectorant and antiviral - shortens cough duration. fda-classified as generally safe.",
        packs=("greyspire", "mistmoor"),
        habitat=("roadside",),
        cures=("yellowcough", "rot_lung", "cancer", "asthma", "bronchitis"),
        side_effects="no common or severe side effects; tiny hairs may cause skin irritation; seeds contain rotenone.",
        preparation="tea, tincture, or smoked.",
    ),
    "lungwort": _h(
        "Lungwort",
        "rare",
        "also heals yellowcough and rot-lung when mullein is scarce. soothes respiratory irritation; expectorant and wound healing. use in moderation - may contain liver-affecting substances.",
        packs=("greyspire", "mistmoor"),
        cures=("yellowcough", "rot_lung", "cancer", "asthma", "bronchitis"),
        side_effects="generally safe in moderation; large doses may cause stomach discomfort; may contain liver-toxic substances.",
        preparation="tea, tincture, topical application.",
    ),
    "marsh_mallow": _h(
        "Marsh-Mallow Root",
        "uncommon",
        "soothes rot-lung fever and wheeze; mucilaginous root coats sore throat and eases leaf-bare cough. demulcent for bruises, swellings, and sprains. may lower blood sugar.",
        packs=("mistmoor",),
        cures=("rot_lung", "leafbare_cough", "sprained_leg", "asthma"),
        side_effects="generally recognized as safe; rare: bloating, gas, fullness; may lower blood sugar.",
        preparation="tea, topical application, bath additive.",
    ),
    "belly_rip_fungus": _h(
        "Belly-Rip Fungus",
        "rare",
        "glow-fungus from the belly-rip sinkhole; only cure for rot-lung necrosis.",
        packs=("mistmoor",),
        cures=("rot_lung",),
        side_effects="unknown; use with extreme caution.",
        preparation="applied directly to necrotic tissue; healer's discretion.",
    ),
    "lizards_tail": _h(
        "Lizard's Tail",
        "common",
        "removes 1 fever exhaustion; anti-inflammatory and diuretic. sedative rhizome eases fever, body aches, and urinary complaints. contains saponins - causes nausea if too much is eaten.",
        packs=("mistmoor",),
        cures=("influenza", "urinary_infection"),
        side_effects="contains saponins - poisonous when ingested; causes irritation, nausea, vomiting.",
        preparation="dried roots ground into powder; tea or infusion.",
    ),
    "meadowsweet": _h(
        "Meadowsweet",
        "uncommon",
        "ignore 1 pain exhaustion for 4 hours; pain relief for 1 sunrise - ignores chronic pain and arthritis penalties. contains salicylates - eases gut upset, diarrhea, and fever. increases bleeding risk if used with wounds.",
        packs=("silverrush",),
        cures=("sprained_leg", "diarrhea", "eating_distress", "influenza", "lyme", "arthritis"),
        side_effects="contains salicylates - increases bleeding risk; large amounts or long-term use possibly unsafe.",
        preparation="tea, tincture; traditional adult dose: 2.5-3.5g flower or 4-5g herb daily.",
    ),
    "mountain_ash": _h(
        "Mountain Ash (Rowan)",
        "common",
        "bitter bark eases fever and weeping-scale, soothes liver complaints; choleretic. berries require caution - large amounts cause stomach damage.",
        cures=("influenza", "hard_paw"),
        side_effects="fresh berries possibly unsafe - large amounts cause stomach irritation, vomiting, kidney damage.",
        preparation="bark for medicinal use; berries require caution.",
    ),
    "oak_bark": _h(
        "Oak Bark",
        "common",
        "stops bleeding; +2 stabilize. astringent and antiviral - treats acute diarrhea, reduces inflammation, and prevents infection in cuts and scrapes. prolonged use damages liver.",
        packs=("thistlehide",),
        cures=("deep_gash", "infected_wound", "diarrhea"),
        side_effects="oral use may cause stomach upset; topical may irritate skin; prolonged use may cause kidney or liver damage.",
        preparation="tea for diarrhea; topical applications.",
    ),
    "parsley": _h(
        "Parsley",
        "common",
        "ends lactation within 6 hours; eases milk-fever and eating troubles. analgesic, antibacterial, and digestive aid. parsley oil is hepatotoxic in high doses - use leaves only.",
        habitat=("compound",),
        cures=("milk_fever", "wasting_sickness", "eating_distress", "urinary_infection"),
        side_effects="parsley oil: headache, convulsions, kidney damage; psoralens cause photodermatitis; avoid in pregnancy.",
        preparation="used as food or tea; oil requires caution.",
    ),
    "passionflower": _h(
        "Passionflower",
        "uncommon",
        "eases racing thoughts and nightmare sleep. sedative and anxiolytic - reduces anxiety and feral drift. safe up to 8 weeks; prolonged use causes drowsiness.",
        habitat=("compound",),
        cures=("anxiety", "insomnia", "feral_shift"),
        side_effects="common: dizziness, drowsiness, confusion; not for use by pregnant wolves.",
        preparation="tea or dietary supplement.",
    ),
    "pine_needle": _h(
        "Pine Needles",
        "common",
        "tea ends coughing after 1 dose; expectorant for chest congestion. supports urinary tract and immune system. avoid in pregnancy - may cause uterine contractions.",
        packs=("greyspire",),
        cures=("cough", "leafbare_cough", "urinary_infection", "asthma"),
        side_effects="may cause uterine contractions - avoid pregnancy; large quantities may cause stomach upset.",
        preparation="tea; essential oil - diluted, with caution.",
    ),
    "pine_bark": _h(
        "Pine Bark",
        "common",
        "inner bark strips ease leaf-bare cough and frost-nipped paws; greyspire medics peel it in cold weather. rich in antioxidants; reduces inflammation and eases breathing.",
        packs=("greyspire",),
        cures=("leafbare_cough", "punctured_paw", "asthma"),
        side_effects="minor: stomach upset, headaches, dizziness; may increase bleeding risk.",
        preparation="extract supplement.",
    ),
    "plantain": _h(
        "Plantain",
        "uncommon",
        "gentle wound remedy; cleanses torn claws and deep gashes. expectorant - opens airways and eases chest illness. astringent and hemostatic. anaphylaxis possible in rare cases.",
        packs=("thistlehide",),
        habitat=("roadside", "compound"),
        cures=("leafbare_cough", "deep_gash", "punctured_paw", "torn_claw", "asthma", "bronchitis"),
        side_effects="anaphylaxis possible; mild: nausea, vomiting, bloating; high doses may cause serious allergic reactions.",
        preparation="tea, tincture, poultice.",
    ),
    "poppy_seeds": _h(
        "Poppy Seeds",
        "common",
        "sedative and pain relief; unconscious rest 1 sunrise. calms shock and emotional distress. mild hypnotic - aids sleep and reduces anxiety. excessive intake is toxic.",
        habitat=("compound",),
        cures=("insomnia", "anxiety", "shock_emotional", "grief_melancholy"),
        side_effects="generally safe; excessive intake may cause digestive discomfort; may cause positive drug test.",
        preparation="seeds consumed; flower heads for coughs; petals and leaves chewed for sleep.",
    ),
    "prickly_ash": _h(
        "Prickly Ash",
        "rare",
        "ends frozen-paw numbness; numbs tooth pain for 1 hour. improves circulation to cold extremities; analgesic and anti-inflammatory. may increase bleeding risk.",
        packs=("greyspire",),
        cures=("tooth_infection", "punctured_paw", "arthritis"),
        side_effects="no known major side effects; may cause allergic reactions; may increase bleeding risk.",
        preparation="bark and berries used medicinally.",
    ),
    "purple_loosestrife": _h(
        "Purple Loosestrife",
        "common",
        "staunches bleeding on stitched wounds; reduces bleed timer; cures diarrhea. antibiotic and astringent - treats bacterial infections. sedative in large amounts.",
        packs=("silverrush",),
        habitat=("roadside",),
        cures=("deep_gash", "diarrhea", "infected_wound"),
        side_effects="astringent properties may cause gi distress in large quantities.",
        preparation="tea; flowering tops dried.",
    ),
    "ragweed": _h(
        "Ragweed",
        "common",
        "3 leaves removes 1 exhaustion. astringent properties ease mild respiratory inflammation and liver complaints. highly allergenic - avoid in wolves with known pollen sensitivity.",
        habitat=("roadside",),
        cures=("leafbare_cough", "hepatitis", "allergy"),
        side_effects="highly allergenic - causes hay fever, contact dermatitis, respiratory distress.",
        preparation="tea - caution, highly allergenic.",
    ),
    "ragwort": _h(
        "Ragwort",
        "common",
        "elder hunts at full speed for 1 day. eases joint and limb stiffness. toxic - contains pyrrolizidine alkaloids; causes liver damage with repeated use. lethal to grazing animals.",
        cures=("sprained_leg",),
        side_effects="toxic - contains pyrrolizidine alkaloids causing liver toxicity; fatal to grazing animals.",
        preparation="avoid - no safe preparation.",
    ),
    "raspberry_leaves": _h(
        "Raspberry Leaves",
        "common",
        "advantage on birth hemorrhage saves; rich in vitamins and minerals. strongly astringent - eases mild diarrhea and chest cough. detoxifying tonic.",
        cures=("diarrhea", "leafbare_cough"),
        side_effects="generally safe; may cause diarrhea, hypoglycemia, acute liver injury; may cause premature labor.",
        preparation="tea.",
    ),
    "rosemary": _h(
        "Rosemary",
        "common",
        "hides death-scent at burial. relieves grief, decreases stress, calms anxiety; anti-inflammatory and digestive aid. large doses cause vomiting and kidney damage - use sparingly.",
        habitat=("compound",),
        cures=("grief_melancholy", "dementia", "chronic_stress", "anxiety", "obsession"),
        side_effects="large amounts cause vomiting, sun sensitivity, kidney damage; undiluted oil toxic.",
        preparation="culinary herb, tea, essential oil - diluted.",
    ),
    "rush_stalks": _h(
        "Rush Stalks",
        "common",
        "hard stalks bind broken bones; lash splints with sticks (+2 medicine to set fractures). antispasmodic and expectorant. long-term use may cause thiamine deficiency.",
        packs=("mistmoor", "silverrush"),
        cures=("fractured_rib", "broken_jaw", "sprained_leg"),
        side_effects="contains thiaminase - long-term use may cause thiamine deficiency.",
        preparation="stalks boiled for diuretic; used as splint material.",
    ),
    "saffron": _h(
        "Saffron",
        "common",
        "auto-stabilize postpartum hemorrhage; ends milk-fever. sedative and expectorant; eases cough, anxiety, and grief. large doses (>5g) cause vomiting and bloody urine.",
        habitat=("compound",),
        cures=("dying", "milk_fever", "leafbare_cough", "anxiety", "grief_melancholy"),
        side_effects="generally safe up to 100mg daily; large doses (>5g) cause vomiting, dizziness, bloody urine; may cause miscarriage.",
        preparation="used as spice or supplement.",
    ),
    "sage": _h(
        "Sage",
        "common",
        "soothes sore throat; elders eat hard food longer. eases leaf-bare cough, eating troubles, and diarrhea. antimicrobial wash for infected wounds. extended use or large amounts cause seizures.",
        habitat=("compound",),
        cures=("leafbare_cough", "eating_distress", "diarrhea", "infected_wound"),
        side_effects="extended use or large amounts: restlessness, vomiting, vertigo, rapid heart rate, seizures, kidney damage.",
        preparation="tea, gargle, culinary herb.",
    ),
    "skunk_cabbage": _h(
        "Skunk Cabbage (dried)",
        "common",
        "treats severe cough and blackcough; antispasmodic for the chest. toxic fresh (dc 12) - contains oxalates; causes mouth pain. overconsumption causes kidney failure.",
        cures=("cough", "leafbare_cough", "asthma"),
        side_effects="possibly safe in small amounts; large amounts cause nausea, vomiting, dizziness; contains oxalates.",
        preparation="ointment from roots boiled in oil - dried form only.",
    ),
    "slippery_elm": _h(
        "Slippery Elm",
        "uncommon",
        "eat or drink without pain for 8 hours. powdered bark soothes gut lining - treats diarrhea, eating troubles, and urinary inflammation. eases stress and anxiety. whole bark may cause miscarriage.",
        packs=("thistlehide",),
        cures=("broken_jaw", "diarrhea", "eating_distress", "anxiety", "urinary_infection"),
        side_effects="no known side effects orally; topical may cause contact dermatitis; whole bark may be abortifacient.",
        preparation="powdered bark; tea, tincture.",
    ),
    "snakeroot": _h(
        "Snakeroot",
        "common",
        "advantage vs snake venom saves. sedative and antihypertensive - calms anxiety and promotes sleep. excessive use causes depression, nightmares, and severe diarrhea.",
        cures=("anxiety", "insomnia"),
        side_effects="nasal congestion, sedation, gi upset, bradycardia; diarrhea, depression.",
        preparation="powdered root: 50-300mg daily.",
    ),
    "sorrel": _h(
        "Sorrel",
        "common",
        "stops heavy bleeding; restores appetite and eases chest congestion. hemostatic, analgesic, and diuretic. large amounts cause kidney damage - toxic in excess.",
        cures=("deep_gash", "leafbare_cough"),
        side_effects="large amounts possibly unsafe - may increase kidney stone risk; contains oxalic acid.",
        preparation="leaves used fresh or cooked.",
    ),
    "stick": _h(
        "Straight Stick",
        "common",
        "thin twig for wolves in pain to bite during deep treatment; also used to lash splints.",
        habitat=("wild",),
        cures=(),
        side_effects="none; splinters possible if not smoothed.",
        preparation="gathered from any woody area.",
    ),
    "sticklewort": _h(
        "Sticklewort",
        "common",
        "neutralizes snake venom if within 1 minute. strongly astringent - treats diarrhea, cough, and superficial wounds. hepatoprotective and antioxidant.",
        cures=("diarrhea", "leafbare_cough", "infected_wound", "mild_poison"),
        side_effects="allergic reactions possible; caution for blood clotting issues.",
        preparation="tea, gargle, topical application.",
    ),
    "stinging_nettle": _h(
        "Stinging Nettle",
        "common",
        "with comfrey +1 broken bone healing day. dried leaves drive off fleas. reduces joint inflammation and clears urinary complaints. cook or dry before use - raw stings.",
        cures=("fractured_rib", "sprained_leg", "fleas", "urinary_infection", "lyme", "arthritis"),
        side_effects="generally safe in moderate amounts; common: constipation, diarrhea, upset stomach; touching plant causes irritation.",
        preparation="dried or cooked form safe; tea, tincture, supplement.",
    ),
    "sweet_sedge": _h(
        "Sweet Sedge",
        "common",
        "ends mild gut infection in 1 day; steadies belly-rip tremors; eases eating distress. digestive aid. likely unsafe internally - contains cancer-causing beta-isoasarone; use externally or in tiny amounts only.",
        cures=("diarrhea", "shaking_sickness", "eating_distress", "bloat"),
        side_effects="likely unsafe - contains cancer-causing beta-isoasarone; causes kidney damage, shaking, seizures.",
        preparation="avoid - no safe preparation.",
    ),
    "tansy": _h(
        "Tansy",
        "common",
        "halves sprain recovery time; expels internal parasites and worms; leaf suppresses leaf-bare cough. drives off fleas. toxic - contains thujone; lethal in pregnancy - causes miscarriage.",
        cures=("sprained_leg", "fleas", "leafbare_cough", "parasites"),
        side_effects="toxic - contains thujone; causes vomiting, severe diarrhea, tremors, kidney and liver damage, seizures; not for pregnant wolves.",
        preparation="leaves, flowers, stems eaten together - extreme caution.",
    ),
    "thyme": _h(
        "Thyme",
        "common",
        "ends minor pain for 2 hours. mucolytic expectorant for chest congestion. calms anxiety and aids restful sleep. antifungal and antibacterial.",
        habitat=("compound",),
        cures=("anxiety", "insomnia", "leafbare_cough", "asthma"),
        side_effects="possibly safe short-term; allergic reactions, dizziness, stomach upset; rare hypersensitivity.",
        preparation="consumed; tea, culinary herb.",
    ),
    "tormentil": _h(
        "Tormentil",
        "common",
        "+2 medicine for any injury. more tannin than oak bark - strongly astringent; treats diarrhea and acute gut sickness; soothes throat inflammation and infected wounds.",
        cures=("diarrhea", "leafbare_cough", "infected_wound"),
        side_effects="generally well-tolerated; mild stomach pain or heartburn possible.",
        preparation="tea, tincture, topical.",
    ),
    "valerian": _h(
        "Valerian",
        "common",
        "calms shock; unconscious 1d4 hours. reduces nervous tension, eating troubles, and feral drift. improves sleep. withdrawal symptoms after long-term use - wean slowly.",
        habitat=("compound",),
        cures=("anxiety", "insomnia", "feral_shift", "eating_distress", "grief_melancholy"),
        side_effects="generally well-tolerated; common: dizziness, headache, daytime drowsiness; withdrawal symptoms if discontinued.",
        preparation="tea, tincture, supplement.",
    ),
    "watermint": _h(
        "Watermint",
        "common",
        "removes nausea in 10 minutes. analgesic, antiseptic, and antispasmodic - treats cough, wounds, gut sickness, and liver complaints. not for pregnant wolves - may cause premature birth.",
        cures=("leafbare_cough", "infected_wound", "diarrhea", "eating_distress", "hepatitis", "bloat", "leptospirosis"),
        side_effects="not for pregnant mothers - may cause premature birth or miscarriage; toxic to sheep.",
        preparation="chewed into pulp; tea from fresh or dried leaves.",
    ),
    "wild_cherry_bark": _h(
        "Wild Cherry Bark",
        "common",
        "stops coughing for 2 hours, even blackcough; sedative and digestive tonic. calms anxiety. contains cyanogenic glycosides - short-term use only (10-14 days); large doses toxic.",
        cures=("cough", "leafbare_cough", "diarrhea", "anxiety"),
        side_effects="generally safe in small amounts; excessive doses toxic due to cyanogenic glycosides; short-term use only.",
        preparation="bark tea or syrup; short-term use only.",
    ),
    "wild_garlic": _h(
        "Wild Garlic",
        "common",
        "advantage vs vermin disease 24h. antibacterial - cleans and slows infection in fresh wounds. treats leaf-bare cough and liver complaints. supports cardiovascular health. excessive intake causes vomiting.",
        cures=("leafbare_cough", "fleas", "infected_wound", "hepatitis", "leptospirosis"),
        side_effects="generally safe; excessive intake may cause nausea, vomiting, diarrhea.",
        preparation="eaten raw or cooked; tea.",
    ),
    "willow_bark": _h(
        "Willow Bark",
        "common",
        "pain relief 1 sunrise; cools fever. ignores chronic pain and arthritis penalties for 1 sunrise. contains salicin - natural anti-inflammatory for joints and fractures. stomach bleeding possible with long-term use.",
        packs=("mistmoor", "silverrush"),
        cures=("influenza", "sprained_leg", "fractured_rib", "lyme", "arthritis"),
        side_effects="common: nausea, vomiting, diarrhea, heartburn, rash; may affect blood clotting; similar to aspirin.",
        preparation="bark chewed in small amounts for pain; tea, tincture.",
    ),
    "witch_hazel": _h(
        "Witch Hazel",
        "common",
        "astringent and hemostatic; reduces eye swelling; soothes poison ivy rash and insect stings; eases chest cough. internal use in large doses may cause liver problems.",
        cures=("swollen_eye", "infected_wound", "poison_ivy", "leafbare_cough", "mild_poison"),
        side_effects="most common: dry skin; high doses may cause liver or kidney problems; contains trace safrole.",
        preparation="topical application - distillate or cream; internal use with caution.",
    ),
    "yarrow": _h(
        "Yarrow",
        "common",
        "+2 medicine to stabilize; stops bleeding; cleanses torn claws. anti-inflammatory; lowers blood pressure. also settles gut sickness. allergic reactions possible.",
        cures=("deep_gash", "infected_wound", "shaking_sickness", "torn_claw", "diarrhea"),
        side_effects="generally considered safe; may interact with lithium; allergic reactions possible.",
        preparation="tea, tincture, topical application.",
    ),
    "catmint": _h(
        "Catmint Tea",
        "uncommon",
        "cures severe blackcough (2 doses per 24 hours); eases anxiety, insomnia, and eating troubles. sedative; increases appetite; treats nervous conditions. large doses cause vomiting. not for pregnant wolves.",
        habitat=("compound",),
        cures=("cough", "leafbare_cough", "anxiety", "insomnia", "eating_distress", "asthma"),
        side_effects="high doses possibly unsafe; headaches, vomiting; emmenagogue and abortifacient - avoid in pregnancy.",
        preparation="leaves and flowers for congestion and coughs; tea.",
    ),
    "purslane": _h(
        "Purslane",
        "common",
        "fleshy leaves hold ditch-water; chew for +12 thirst without visiting the creek. rich in omega-3 fatty acids and vitamin c - anti-inflammatory; eases gut trouble and mild anxiety.",
        habitat=("roadside", "compound"),
        cures=("eating_distress", "anxiety"),
        side_effects="limited studies - no significant adverse effects; constipation reported; contains oxalates.",
        preparation="eaten as vegetable; cooking reduces oxalates.",
    ),
    "chicory": _h(
        "Chicory",
        "common",
        "bitter roadside root; settles gut upset and supports liver health. liver and digestive tonic; diuretic and appetite stimulant. high fiber may cause gas and bloating.",
        habitat=("roadside",),
        cures=("diarrhea", "eating_distress", "hepatitis"),
        side_effects="fresh plant may cause allergic skin reactions; high fiber may cause gas, bloating, diarrhea.",
        preparation="root as coffee substitute; tea.",
    ),
    "mugwort": _h(
        "Mugwort",
        "uncommon",
        "rub through pelt to drive off fleas. settles digestion and eases gut upsets and eating troubles. mild digestive relief. toxic in pregnancy - causes miscarriage.",
        habitat=("roadside",),
        cures=("fleas", "diarrhea", "eating_distress"),
        side_effects="contains thujone - harmful in large amounts; may cause miscarriage; respiratory allergic responses.",
        preparation="tea, topical; use with caution.",
    ),
    "garden_mint": _h(
        "Garden Mint",
        "common",
        "escaped from a twoleg herb bed; ends nausea in minutes. antispasmodic - eases stomach and intestinal cramps; treats indigestion and eating troubles. antimicrobial.",
        habitat=("compound",),
        cures=("eating_distress", "diarrhea", "bloat"),
        side_effects="may cause sleepiness; concentrated oils toxic to dogs and cats in large quantities.",
        preparation="tea, culinary herb.",
    ),
    "wood_sorrel": _h(
        "Wood Sorrel",
        "common",
        "sour shamrock in mowed lawn; steadies a queasy stomach and eating troubles. antipyretic - reduces fever in small doses. contains oxalic acid - high doses are toxic; causes kidney damage.",
        habitat=("compound",),
        cures=("influenza", "eating_distress"),
        side_effects="contains oxalic acid - high doses toxic; overdose causes diarrhea, nausea, kidney damage.",
        preparation="small amounts as tonic; poultice.",
    ),
    "oxeye_daisy": _h(
        "Oxeye Daisy",
        "common",
        "thunderpath-margin daisy; eases joint ache; suppresses leaf-bare cough and chest tightness; aids liver complaints. antispasmodic and diuretic. allergic reactions in asteraceae-sensitive wolves.",
        habitat=("roadside",),
        cures=("sprained_leg", "leafbare_cough", "influenza", "hepatitis"),
        side_effects="may cause allergic reactions in those sensitive to asteraceae; may cause contact and inhalant allergy.",
        preparation="young leaves in salads; tea.",
    ),
    "common_mallow": _h(
        "Common Mallow",
        "common",
        "soft leaves in roadside dust; mild poultice for scraped and scorched pads. soothes dry cough, throat soreness, and gut trouble. regulates bowel movements.",
        habitat=("roadside", "compound"),
        cures=("punctured_paw", "leafbare_cough", "eating_distress", "scorched_hide", "asthma"),
        side_effects="none known; may lower blood sugar; livestock poisoning reported - muscular tremors.",
        preparation="tea, topical, bath.",
    ),
    "shepherds_purse": _h(
        "Shepherd's Purse",
        "common",
        "triangular seed-pods along the gravel; slows oozing cuts and treats wound inflammation. hemostatic - stops internal and external bleeding. toxic in pregnancy - causes uterine contractions.",
        habitat=("roadside",),
        cures=("deep_gash", "internal_bleeding"),
        side_effects="possibly safe in small amounts short-term; large amounts cause heart palpitations; causes uterine contractions - avoid pregnancy.",
        preparation="tea, tincture, powder.",
    ),
    "garlic_mustard": _h(
        "Garlic Mustard",
        "common",
        "invasive roadside mustard; rub through pelt to drive off fleas; antiseptic poultice for infected bites and wounds. neutralizes mild poison. rich in vitamins a and c.",
        habitat=("roadside",),
        cures=("leafbare_cough", "infected_wound", "mild_poison", "lyme"),
        side_effects="safe in moderate amounts; large quantities may cause digestive discomfort; contains goitrogens.",
        preparation="young leaves eaten; poultice.",
    ),

    # ----- RESTRICTED / POISON (handled separately) -----
    "bloodroot": _h(
        "Bloodroot",
        "restricted",
        "3d6 poison damage (dc 16 half). prolonged contact causes tissue damage and scarring.",
        poison=True,
        side_effects="nausea, vomiting, drowsiness, vertigo, contact dermatitis; topical use can cause tissue damage.",
        preparation="used in toothpaste and mouthwash; traditional salves - extreme caution.",
    ),
    "deathberries": _h(
        "Deathberries (Yew)",
        "restricted",
        "mercy killing; medic knowledge only. seeds kill within minutes; yarrow used as antidote to induce vomiting.",
        poison=True,
        side_effects="seeds can kill within minutes; poisonous to most animals.",
        preparation="seeds consumed for euthanasia; yarrow used as antidote to induce vomiting.",
    ),
    "deadly_nightshade": _h(
        "Deadly Nightshade",
        "restricted",
        "confusion then paralysis (wis dc 15). as few as 5 berries kill an adult. touch may be toxic.",
        poison=True,
        side_effects="extremely toxic - all parts poisonous; symptoms: blurred vision, seizures, death.",
        preparation="no safe preparation for lay use.",
    ),
    "foxglove": _h(
        "Foxglove",
        "restricted",
        "deadly heart poison (dc 18 or die in 1d4 min). narrow margin between medicine and death. all parts poisonous.",
        poison=True,
        side_effects="extremely toxic - all parts poisonous; narrow therapeutic index; toxicity: vomiting, cardiac arrhythmias, death.",
        preparation="no safe preparation for lay use; professional medical use only.",
    ),
    "holly_berries": _h(
        "Holly Berries",
        "restricted",
        "2d4 poison (dc 12 half). leaves cause diarrhea and vomiting; leaf spines can puncture the digestive tract.",
        poison=True,
        side_effects="berries poisonous; leaves cause diarrhea, nausea, vomiting; leaf spines may tear mouth.",
        preparation="avoid ingestion; external use only with caution.",
    ),
    "oleander": _h(
        "Oleander",
        "restricted",
        "4d6 poison, no antidote (dc 18 half). one of the most poisonous plants known - all parts lethal. sap causes severe eye inflammation.",
        poison=True,
        side_effects="one of the most poisonous plants - all parts toxic; small amounts lethal.",
        preparation="no safe preparation for lay use.",
    ),
    "poison_ivy": _h(
        "Poison Ivy",
        "restricted",
        "contact: -1d4 cha, disadvantage stealth 3 days. contains urushiol - causes severe skin rash and mouth or throat irritation if eaten.",
        poison=True,
        side_effects="highly toxic - contains urushiol; causes severe skin irritation; ingestion causes severe mouth and throat irritation.",
        preparation="avoid - no safe preparation for medicinal use.",
    ),
    "water_hemlock": _h(
        "Water Hemlock",
        "restricted",
        "lethal poison (dc 20 half, still 6d6). one of the most poisonous plants - cicutoxin causes death within 15 minutes. all parts are poisonous; even small amounts cause convulsions.",
        poison=True,
        side_effects="one of the most poisonous plants; contains cicutoxin; even small amounts cause muscle spasms, respiratory failure, death within an hour.",
        preparation="extremely dangerous - no safe preparation.",
    ),
    "wintergreen": _h(
        "Wintergreen",
        "restricted",
        "often misidentified; 1d4 poison (dc 10). oil is unsafe to eat. external redness and irritation; large amounts cause tinnitus, confusion, and death.",
        poison=True,
        side_effects="oil is unsafe to take orally; topical: redness, irritation; large amounts cause ringing in ears, nausea, confusion.",
        preparation="external use only; tea with caution; oil externally - diluted.",
    ),
    "wolfsbane": _h(
        "Wolfsbane",
        "very_rare",
        "removes spirit curse (dc 20 medicine check); deals 2d6 poison damage to patient. extremely toxic - all parts poisonous; historically used to poison wolves. can be absorbed through skin.",
        packs=("greyspire",),
        cures=("spirit_curse",),
        poison=True,
        side_effects="extremely toxic - all parts poisonous; contains aconitine; ingestion causes numbness, nausea, respiratory failure; can be absorbed through skin.",
        preparation="no safe preparation for lay herbalists.",
    ),
    "swamp_milkweed": _h(
        "Swamp Milkweed",
        "very_rare",
        "breaks curses; only herb known to cure pox in its late stage. toxic - contains cardiac glycosides; causes dangerous heart issues in large doses.",
        packs=("mistmoor",),
        cures=("pox",),
        side_effects="toxic - contains cardiac glycosides; causes dangerous heart issues; lethal in large doses.",
        preparation="avoid - no safe preparation for lay use.",
    ),
    "death_cap": _h(
        "Death-Cap Mushroom",
        "rare",
        "pale mushroom found only in the rotting mere. intensely toxic; 3d6 poison (dc 18 half). causes organ failure and seizures. healers may use trace amounts experimentally.",
        packs=("mistmoor",),
        poison=True,
        habitat=("rotting_mere",),
        side_effects="extremely toxic - one of the most lethal mushrooms; causes organ failure, seizures, nausea; fatal if ingested.",
        preparation="no safe preparation; experimental use only by experienced healers.",
    ),
}

# ============================================================================
# 3. GLOBAL METHOD REQUIREMENTS (fallback)
# ============================================================================

DEFAULT_METHOD_REQS = {
    "cough": "tea",
    "leafbare_cough": "tea",
    "yellowcough": "tea",
    "rot_lung": "tea",
    "bronchitis": "tea",
    "asthma": "tea",
    "influenza": "tea",
    "hard_paw": "tea",
    "diarrhea": "tea",
    "constipation": "tea",
    "eating_distress": "tea",
    "wasting_sickness": "tea",
    "deep_gash": "poultice",
    "infected_wound": "poultice",
    "festering_wound": "poultice",
    "punctured_paw": "poultice",
    "torn_claw": "poultice",
    "scorched_hide": "ointment",
    "mild_poison": "juice",
    "poison_ivy": "sap",
    "mange": "ointment",
    "fleas": "rub",
    "anxiety": "tea",
    "insomnia": "tea",
    "night_terrors": "tea",
    "grief_melancholy": "tea",
    "shock_emotional": "tea",
}

# ============================================================================
# 4. PREPARATION LOGIC
# ============================================================================

class PreparedHerb:
    def __init__(self, herb_key: str, method: str, preparer_id: int, timestamp: float,
                 skill_success: bool = True):
        self.herb_key = herb_key
        self.method = method
        self.preparer_id = preparer_id
        self.timestamp = timestamp
        self.skill_success = skill_success
        self.herb_data = HERBS[herb_key]
        self.valid_method = self._validate_method()
        if not self.valid_method:
            raise ValueError(f"Method '{method}' is not valid for {herb_key}.")

    def _validate_method(self) -> bool:
        prep_dict = self.herb_data.get("preparations", {})
        return self.method in prep_dict

    def get_effect_description(self) -> str:
        prep_dict = self.herb_data.get("preparations", {})
        return prep_dict.get(self.method, self.herb_data.get("effect", "unknown effect"))

    def get_cures(self) -> tuple:
        return self.herb_data.get("cures", ())

    def get_side_effects(self) -> str:
        return self.herb_data.get("side_effects", "")

    def is_poison(self) -> bool:
        return self.herb_data.get("poison", False)

    def get_method_requirements(self) -> Dict[str, str]:
        return self.herb_data.get("method_requirements", {})


def get_available_methods(herb_key: str) -> List[str]:
    herb = HERBS.get(herb_key)
    if not herb:
        return []
    return list(herb.get("preparations", {}).keys())


def prepare_herb(herb_key: str, method: str, preparer_id: int,
                 medicine_bonus: int = 0, difficulty: int = 10) -> PreparedHerb:
    if herb_key not in HERBS:
        raise ValueError(f"Unknown herb: {herb_key}")

    avail = get_available_methods(herb_key)
    if method not in avail:
        raise ValueError(f"Method '{method}' is not valid for {herb_key}. Available: {', '.join(avail)}")

    roll = random.randint(1, 20) + medicine_bonus
    success = roll >= difficulty
    return PreparedHerb(herb_key, method, preparer_id, time.time(), skill_success=success)


# ============================================================================
# 5. SIDE EFFECT PARSER
# ============================================================================

def apply_side_effects(side_effects_text: str, user_data: Dict, severity_multiplier: float = 1.0) -> Dict:
    changes = {"hunger": 0, "thirst": 0, "mood": 0, "hp": 0, "exhaustion": 0}
    text_lower = side_effects_text.lower()

    effects_map = {
        "nausea": {"hunger": -6, "thirst": -4},
        "vomiting": {"hunger": -10, "thirst": -8},
        "diarrhea": {"hunger": -10, "thirst": -12},
        "dizziness": {"mood": -4, "exhaustion": 1},
        "headache": {"mood": -4},
        "weakness": {"hunger": -4, "mood": -4},
        "blurred vision": {"mood": -4},
        "confusion": {"mood": -6},
        "drowsiness": {"mood": -2, "exhaustion": 1},
        "liver damage": {"hp": -2},
        "kidney damage": {"hp": -1, "thirst": -6},
        "heart problems": {"hp": -2},
        "skin irritation": {"mood": -2},
        "itching": {"mood": -2},
        "rash": {"mood": -2},
        "allergic reaction": {"hp": -1, "mood": -4},
        "anaphylaxis": {"hp": -4},
        "seizures": {"hp": -3, "exhaustion": 2},
        "paralysis": {"hp": -2, "exhaustion": 3},
        "coma": {"hp": -5, "exhaustion": 5},
        "death": {"hp": -999},
    }

    for effect, changes_dict in effects_map.items():
        if effect in text_lower:
            for stat, delta in changes_dict.items():
                changes[stat] += int(delta * severity_multiplier)

    for stat, delta in changes.items():
        if stat == "hunger":
            user_data["hunger"] = max(0, user_data.get("hunger", 100) + delta)
        elif stat == "thirst":
            user_data["thirst"] = max(0, user_data.get("thirst", 100) + delta)
        elif stat == "mood":
            user_data["mood"] = max(0, min(100, user_data.get("mood", 100) + delta))
        elif stat == "hp":
            user_data["hp"] = max(0, user_data.get("hp", 100) + delta)
        elif stat == "exhaustion":
            user_data["exhaustion"] = max(0, user_data.get("exhaustion", 0) + delta)

    return changes


# ============================================================================
# 6. ADMINISTRATION LOGIC
# ============================================================================

def administer_herb(prepared: PreparedHerb, target_user: Dict) -> Dict:
    result = {
        "success": False,
        "cured": False,
        "cured_disease": None,
        "message": "",
        "changes": {},
        "damage_taken": 0,
    }

    if not prepared.skill_success:
        result["message"] = f"The {prepared.herb_data['name']} was ruined during preparation. It has no effect."
        return result

    if prepared.is_poison():
        herb_key = prepared.herb_key
        damage = 0
        if herb_key == "bloodroot":
            damage = random.randint(3, 18)  # 3d6
        elif herb_key == "holly_berries":
            damage = random.randint(2, 8)   # 2d4
        elif herb_key == "oleander":
            damage = random.randint(4, 24)  # 4d6
        elif herb_key == "water_hemlock":
            damage = random.randint(6, 36)  # 6d6
        elif herb_key == "deathberries" or herb_key == "foxglove" or herb_key == "deadly_nightshade":
            damage = 999
        elif herb_key == "wolfsbane":
            damage = random.randint(2, 12)  # 2d6
        else:
            damage = random.randint(1, 6)

        target_user["hp"] = max(0, target_user.get("hp", 100) - damage)
        result["damage_taken"] = damage
        result["message"] = f"The {prepared.herb_data['name']} is poisonous! {target_user.get('name', 'Wolf')} takes {damage} damage."
        result["success"] = True
        if prepared.get_side_effects():
            changes = apply_side_effects(prepared.get_side_effects(), target_user, severity_multiplier=1.0)
            result["changes"] = changes
            result["message"] += f" Additionally, {changes}."
        return result

    target_disease_raw = target_user.get("disease", "")
    disease_key, stage = parse_disease(target_disease_raw)
    cures = prepared.get_cures()

    if disease_key and disease_key in cures:
        allowed_stages = HERB_CURE_STAGES.get(disease_key)
        if allowed_stages is not None and stage not in allowed_stages:
            result["message"] = f"The {prepared.herb_data['name']} cannot cure {disease_key} at its current stage ({stage})."
            return result

        method_reqs = prepared.get_method_requirements()
        required_method = method_reqs.get(disease_key)
        if required_method is None:
            required_method = DEFAULT_METHOD_REQS.get(disease_key)

        if required_method and prepared.method.lower() != required_method.lower():
            result["message"] = (f"The {prepared.herb_data['name']} was prepared using {prepared.method}, "
                                 f"but {disease_key} requires {required_method}. It has no healing effect.")
            if prepared.get_side_effects():
                changes = apply_side_effects(prepared.get_side_effects(), target_user, severity_multiplier=0.5)
                result["changes"] = changes
                result["message"] += f" It causes mild {changes}."
            return result

        target_user["disease"] = None
        result["cured"] = True
        result["cured_disease"] = disease_key
        result["success"] = True
        result["message"] = f"The {prepared.herb_data['name']} cured {disease_key}!"

        effect_text = prepared.herb_data.get("effect", "")
        if "heals" in effect_text.lower() or "restores" in effect_text.lower():
            match = re.search(r'(\d+)\s*hp', effect_text, re.IGNORECASE)
            if match:
                hp_gain = int(match.group(1))
                target_user["hp"] = min(100, target_user.get("hp", 100) + hp_gain)
                result["changes"]["hp"] = hp_gain
                result["message"] += f" Restores {hp_gain} HP."
        return result

    # No matching disease – check for generic effects
    effect_text = prepared.herb_data.get("effect", "")
    if "pain relief" in effect_text.lower():
        target_user["pain_relief_until"] = time.time() + 3600
        result["message"] = f"The {prepared.herb_data['name']} provides pain relief."
        result["success"] = True
    elif "fever" in effect_text.lower():
        target_user["exhaustion"] = max(0, target_user.get("exhaustion", 0) - 1)
        result["message"] = f"The {prepared.herb_data['name']} reduces fever and exhaustion."
        result["success"] = True
    else:
        if prepared.get_side_effects():
            changes = apply_side_effects(prepared.get_side_effects(), target_user, severity_multiplier=1.0)
            result["changes"] = changes
            result["message"] = f"The {prepared.herb_data['name']} has no specific benefit and causes {changes}."
        else:
            result["message"] = f"The {prepared.herb_data['name']} has no noticeable effect."
    return result


