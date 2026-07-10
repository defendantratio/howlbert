"""Wolvden-style illnesses + Warriors cough stages (whitecough → redcough)."""

from __future__ import annotations

# Cough uses legacy DB values mild / severe / deadly (Warriors names in display text).
COUGH_STAGES = {
    "mild": {
        "name": "Green-cough (Mild)",
        "dc": 12,
        "next": "severe",
        "effect": (
            "Mold spores from rotten meat irritate the lungs (spore-lung); "
            "disadvantage on Dexterity checks."
        ),
    },
    "severe": {
        "name": "Blackcough (Severe)",
        "dc": 15,
        "next": "deadly",
        "effect": "Disadvantage on Dexterity and Strength; speed −¼.",
    },
    "deadly": {
        "name": "Redcough (Deadly)",
        "dc": 18,
        "next": None,
        "effect": "Disadvantage on all physical checks; lose 1 HP each sunrise.",
        "hp_loss": 1,
    },
}

# Wolvden-inspired single- and multi-stage illnesses.
DISEASES: dict[str, dict] = {
    "cough": {
        "label": "Cough",
        "contagious": 0.14,
        "respiratory": True,
        "spread_stage": "mild",
        "stages": COUGH_STAGES,
    },
    "diarrhea": {
        "label": "Gut-Run",
        "contagious": 0.0,
        "mating_contagious": 0.12,
        "stages": {
            "active": {
                "name": "Gut-Run",
                "dc": 11,
                "next": None,
                "effect": "Gut sickness: −8 hunger each sunrise; CON save to recover.",
                "hunger_loss": 8,
                "cure_on_save": True,
            },
        },
    },
    "distemper": {
        "label": "Weeping-Scale",
        "contagious": 0.18,
        "respiratory": True,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "Weeping-Scale",
                "dc": 16,
                "next": None,
                "effect": "Hardened pads: 1 HP loss each sunrise; −25% hunt until treated.",
                "hp_loss": 1,
                "hunt_mult": 0.75,
                "lethal": True,
            },
        },
    },
    "influenza": {
        "label": "Shiver-Fever",
        "contagious": 0.50,
        "respiratory": True,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "Shiver-Fever",
                "dc": 13,
                "next": None,
                "effect": "Fever and lethargy: +1 exhaustion each sunrise.",
                "exhaustion_gain": 1,
                "cure_on_save": True,
            },
        },
    },
    "fleas": {
        "label": "The Itch",
        "contagious": 0.36,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "The Itch",
                "dc": 12,
                "next": None,
                "effect": "Itching misery: −8 mood each sunrise.",
                "mood_loss": 8,
                "cure_on_save": True,
            },
        },
    },
    "mild_poison": {
        "label": "Sting-Swell / Snake Venom",
        "contagious": 0.0,
        "spread_stage": "stung",
        "stages": {
            "stung": {
                "name": "Sting-Swell",
                "dc": 11,
                "next": None,
                "effect": (
                    "Swollen muzzle or paw; wasps, hornets, or biting flies. "
                    "−6 mood each sunrise; awkward movement."
                ),
                "mood_loss": 6,
                "cure_on_save": True,
            },
            "venom": {
                "name": "Snake Venom",
                "dc": 14,
                "next": None,
                "effect": (
                    "Venom burn in the bite; limb swells fast. "
                    "−8 mood and −1 HP each sunrise until treated."
                ),
                "mood_loss": 8,
                "hp_loss": 1,
                "cure_on_save": True,
            },
        },
    },
    "poison_ivy": {
        "label": "Leaf-Burn",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "Leaf-Burn (Rash)",
                "dc": 12,
                "next": None,
                "effect": (
                    "Itching contact rash from oily leaves; −4 mood each sunrise; "
                    "hard to move quietly through brush."
                ),
                "mood_loss": 4,
                "cure_on_save": True,
            },
        },
    },
    "mange": {
        "label": "Scratch-Bare",
        "contagious": 0.18,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "Scratch-Bare",
                "dc": 14,
                "next": None,
                "effect": "Patchy fur and raw skin: −25% hunt bones.",
                "hunt_mult": 0.75,
                "cure_on_save": True,
            },
        },
    },
    "hepatitis": {
        "label": "Yellow-Eye",
        "contagious": 0.18,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "Yellow-Eye",
                "dc": 14,
                "next": None,
                "effect": "Liver fever: −10 hydration each sunrise.",
                "thirst_loss": 10,
                "cure_on_save": True,
            },
        },
    },
    "pox": {
        "label": "The Spotting",
        "contagious": 0.18,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "The Spotting",
                "dc": 15,
                "next": None,
                "effect": "Sores and fever; pups lose extra HP; adults −1 HP/sunrise.",
                "hp_loss": 1,
                "juvenile_hp_loss": 3,
                "lethal": True,
            },
        },
    },
    "redscratch": {
        "label": "Redscratch",
        "contagious": 0.0,
        "mating_contagious": 0.45,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "Redscratch",
                "dc": 14,
                "next": None,
                "effect": (
                    "Itching sores from mating contact; soreness, chills, and lethargy; "
                    "blocks conception until treated."
                ),
                "mood_loss": 6,
                "exhaustion_gain": 1,
                "thirst_loss": 8,
                "blocks_conception": True,
                "cure_on_save": True,
            },
        },
    },
    "yellowcough": {
        "label": "Yellowcough",
        "contagious": 0.45,
        "respiratory": True,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "Yellowcough",
                "dc": 17,
                "next": None,
                "effect": (
                    "Labored breathing and severe wheezing; loss of appetite and weakness; "
                    "high fever; sore throat; delirium; coughing bright yellow phlegm; "
                    "fatal without **mullein** or **lungwort** to heal the lung damage."
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
    "rot_lung": {
        "label": "Rot-Lung",
        "contagious": 0.42,
        "respiratory": True,
        "spread_stage": "fever",
        "stages": {
            "fever": {
                "name": "Rot-Lung (Fever)",
                "dc": 13,
                "next": "wheeze",
                "effect": (
                    "Marsh lung-fever: +1 exhaustion and −8 hunger each sunrise; "
                    "pups take extra harm as the season worsens."
                ),
                "exhaustion_gain": 1,
                "hunger_loss": 8,
            },
            "wheeze": {
                "name": "Rot-Lung (Wheeze)",
                "dc": 15,
                "next": "necrosis",
                "effect": "Wheezing lung-rot: −1 HP/sunrise; −25% hunt bones until treated.",
                "hp_loss": 1,
                "juvenile_hp_loss": 2,
                "hunt_mult": 0.75,
            },
            "necrosis": {
                "name": "Rot-Lung (Necrosis)",
                "dc": 17,
                "next": None,
                "effect": (
                    "Tissue blackens: −2 HP/sunrise (pups worse); fatal without "
                    "**marsh-mallow**, **feverfew**, **mullein**, or **lungwort**."
                ),
                "hp_loss": 2,
                "juvenile_hp_loss": 4,
                "lethal": True,
            },
        },
    },
    "milk_fever": {
        "label": "Milk-Fever",
        "contagious": 0.0,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "Milk-Fever",
                "dc": 14,
                "next": None,
                "effect": (
                    "Eclampsia at peak nursing; tremors and weakness; +1 exhaustion and "
                    "−6 mood each sunrise; −1 HP if untreated. "
                    "**Parsley**, **saffron**, or **feverfew**."
                ),
                "thirst_loss": 4,
                "hp_loss": 1,
                "exhaustion_gain": 1,
                "mood_loss": 6,
                "lethal": True,
            },
        },
    },
    "shaking_sickness": {
        "label": "Shaking-Sickness",
        "contagious": 0.15,
        "spread_stage": "shaking",
        "stages": {
            "shaking": {
                "name": "Shaking-Sickness",
                "dc": 12,
                "next": "hemorrhage",
                "effect": (
                    "Belly-Rip tremors; disadvantage on Dexterity; −6 mood each sunrise."
                ),
                "mood_loss": 6,
                "cure_on_save": True,
            },
            "hemorrhage": {
                "name": "Shaking-Sickness (Hemorrhage)",
                "dc": 15,
                "next": None,
                "effect": (
                    "Internal bleeding from bad swamp water: −1 HP/sunrise; "
                    "stabilize with **yarrow** or **cobwebs**."
                ),
                "hp_loss": 1,
                "lethal": True,
            },
        },
    },
    "pupcough": {
        "label": "Pupcough",
        "contagious": 0.10,
        "respiratory": True,
        "spread_stage": "active",
        "stages": {
            "active": {
                "name": "Pupcough",
                "dc": 10,
                "next": "weak_lungs",
                "effect": (
                    "Harsh cough in weak pups; usually harmless; "
                    "disadvantage on the first Dexterity check each sunrise."
                ),
            },
            "weak_lungs": {
                "name": "Pupcough (Weak Lungs)",
                "dc": 12,
                "next": None,
                "effect": (
                    "Lungs never fully strengthen: −1 on Constitution saves; "
                    "treat early with honey and rest."
                ),
            },
        },
    },
    "leafbare_cough": {
        "label": "Leaf-Bare Cough",
        "contagious": 0.22,
        "respiratory": True,
        "spread_stage": "chill",
        "stages": {
            "chill": {
                "name": "Leaf-Bare Cough (Chill)",
                "dc": 11,
                "next": "hacking",
                "effect": (
                    "Cold air bites deep; a dry rasp at the back of the throat; "
                    "−4 mood each sunrise. "
                    "**Catmint**, **honey**, or **thyme** soothes it early."
                ),
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "hacking": {
                "name": "Leaf-Bare Cough (Hacking)",
                "dc": 13,
                "next": "congestion",
                "effect": (
                    "The cough turns bark-deep and relentless; lungs ache with every breath; "
                    "−6 mood and −15% hunt bones each sunrise. "
                    "**Catmint** (2 doses), **lungwort**, or **mullein**."
                ),
                "mood_loss": 6,
                "hunt_mult": 0.85,
            },
            "congestion": {
                "name": "Leaf-Bare Cough (Congestion)",
                "dc": 15,
                "next": None,
                "effect": (
                    "Chest fills; breathing rattles; fever climbs: "
                    "+1 exhaustion and −1 HP each sunrise. "
                    "Without **catmint**, **mullein**, or **lungwort** this turns deadly."
                ),
                "exhaustion_gain": 1,
                "hp_loss": 1,
                "mood_loss": 4,
                "hunt_mult": 0.75,
                "lethal": True,
            },
        },
    },
    "shock_emotional": {
        "label": "Heart-Shock",
        "contagious": 0.0,
        "mental": True,
        "stages": {
            "active": {
                "name": "Heart-Shock",
                "dc": 12,
                "next": None,
                "effect": (
                    "After severe trauma; numbness, denial, silence. "
                    "Treat with poppy seeds, comfort, or valerian in extreme cases."
                ),
                "mood_loss": 8,
                "cure_on_save": True,
            },
        },
    },
    "shock_physical": {
        "label": "Blood-Shock",
        "contagious": 0.0,
        "stages": {
            "active": {
                "name": "Blood-Shock",
                "dc": 14,
                "next": None,
                "effect": (
                    "Blood loss or extreme pain; chills, weakness, rapid heartbeat. "
                    "Life-threatening; stabilize bleeding, water, honey, dry yarrow."
                ),
                "hp_loss": 1,
                "lethal": True,
            },
        },
    },
    "rabies": {
        "label": "Cloudmouth (Rabies)",
        "contagious": 0.0,
        "chronic": True,
        "spread_stage": "incubation",
        "stages": {
            "incubation": {
                "name": "Cloudmouth (Incubation)",
                "dc": 14,
                "next": "prodrome",
                "effect": (
                    "Bite wound festers; anxiety, light sensitivity, and throat tightness; "
                    "**boneset** or **goldenrod** may slow progression (+2 next save) but "
                    "cannot cure rabies."
                ),
                "mood_loss": 4,
            },
            "prodrome": {
                "name": "Cloudmouth (Prodrome)",
                "dc": 16,
                "next": "frenzy",
                "effect": (
                    "Agitation and confusion; disadvantage on Intelligence and Wisdom checks; "
                    "**boneset** or **goldenrod** may buy time before frenzy (no cure)."
                ),
                "mood_loss": 6,
                "exhaustion_gain": 1,
            },
            "frenzy": {
                "name": "Cloudmouth (Frenzy)",
                "dc": 18,
                "next": "terminal",
                "effect": (
                    "Hydrophobia and rage; disadvantage on attacks and social checks; "
                    "bites can spread rabies; no herb cure."
                ),
                "exhaustion_gain": 1,
                "blocks_conception": True,
                "lethal": True,
            },
            "terminal": {
                "name": "Cloudmouth (Terminal)",
                "dc": 20,
                "next": None,
                "effect": "Paralysis and organ failure; lose 2 HP each sunrise until death.",
                "hp_loss": 2,
                "lethal": True,
            },
        },
    },
    "wasting_sickness": {
        "label": "Wasting Sickness",
        "contagious": 0.0,
        "chronic": True,
        "spread_stage": "waning",
        "stages": {
            "waning": {
                "name": "Wasting Sickness (Waning)",
                "dc": 14,
                "next": "emaciated",
                "effect": (
                    "Body sheds weight: −12 hunger each sunrise; −15% hunt bones; "
                    "**borage** or **parsley** may halt it."
                ),
                "hunger_loss": 12,
                "hunt_mult": 0.85,
            },
            "emaciated": {
                "name": "Wasting Sickness (Emaciated)",
                "dc": 16,
                "next": "cachectic",
                "effect": "Muscle wastes away: −1 HP and −15 hunger each sunrise.",
                "hunger_loss": 15,
                "hp_loss": 1,
                "hunt_mult": 0.7,
            },
            "cachectic": {
                "name": "Wasting Sickness (Cachectic)",
                "dc": 18,
                "next": None,
                "effect": "Final wasting; lose 2 HP each sunrise; fatal without den care.",
                "hp_loss": 2,
                "lethal": True,
            },
        },
    },
    "river_rot": {
        "label": "River Rot",
        "contagious": 0.0,
        "chronic": True,
        "spread_stage": "fouled",
        "stages": {
            "fouled": {
                "name": "River Rot (Fouled Gut)",
                "dc": 13,
                "next": "bloody_flux",
                "effect": (
                    "Sewage-tainted water churns the belly: −10 hunger and −6 hydration "
                    "each sunrise; con save shakes it off before it sets in."
                ),
                "hunger_loss": 10,
                "thirst_loss": 6,
            },
            "bloody_flux": {
                "name": "River Rot (Bloody Flux)",
                "dc": 17,
                "next": "failing",
                "effect": (
                    "Bowels turn against the wolf: −1 hp, −14 hunger, −12 hydration each "
                    "sunrise. no known herb touches it."
                ),
                "hp_loss": 1,
                "hunger_loss": 14,
                "thirst_loss": 12,
            },
            "failing": {
                "name": "River Rot (Failing)",
                "dc": 20,
                "next": None,
                "effect": (
                    "Can no longer keep water down; −3 hp each sunrise. fatal without "
                    "den care; no cure is known."
                ),
                "hp_loss": 3,
                "lethal": True,
            },
        },
    },
    "cancer": {
        "label": "Growth-Sickness",
        "contagious": 0.0,
        "chronic": True,
        "spread_stage": "lump",
        "stages": {
            "lump": {
                "name": "Growth-Sickness (Hidden Lump)",
                "dc": 16,
                "next": "spreading",
                "effect": (
                    "A deep swelling the body cannot heal; rare in wolves who outlive the wild; "
                    "−6 mood; **mullein** or **lungwort** if caught early."
                ),
                "mood_loss": 6,
            },
            "spreading": {
                "name": "Growth-Sickness (Spreading)",
                "dc": 17,
                "next": "terminal",
                "effect": "The growth spreads: −1 HP/sunrise; −30% hunt bones.",
                "hp_loss": 1,
                "hunt_mult": 0.7,
            },
            "terminal": {
                "name": "Growth-Sickness (Terminal)",
                "dc": 19,
                "next": None,
                "effect": "Body fails by degrees; lose 2 HP each sunrise.",
                "hp_loss": 2,
                "lethal": True,
            },
        },
    },
    "dementia": {
        "label": "The Long-Forgetting",
        "contagious": 0.0,
        "chronic": True,
        "mental": True,
        "spread_stage": "forgetful",
        "stages": {
            "forgetful": {
                "name": "The Long-Forgetting (Forgetful)",
                "dc": 14,
                "next": "confused",
                "effect": (
                    "Names and trails slip away; disadvantage on Intelligence checks; "
                    "**chamomile** or **dried skullcap** may slow decline."
                ),
            },
            "confused": {
                "name": "The Long-Forgetting (Confused)",
                "dc": 16,
                "next": "lost",
                "effect": (
                    "Time blurs; disadvantage on Intelligence and Wisdom; −8 mood each sunrise."
                ),
                "mood_loss": 8,
            },
            "lost": {
                "name": "The Long-Forgetting (Lost)",
                "dc": 18,
                "next": None,
                "effect": (
                    "Pack faces are strangers; cannot court, socialize, or lead; "
                    "den-bound care only."
                ),
                "mood_loss": 6,
                "blocks_social": True,
            },
        },
    },
    "feral_shift": {
        "label": "Feral Shift",
        "contagious": 0.0,
        "chronic": True,
        "mental": True,
        "spread_stage": "restless",
        "stages": {
            "restless": {
                "name": "Feral Shift (Restless)",
                "dc": 13,
                "next": "feral",
                "effect": "Mind skitters toward the wild: −6 mood; disadvantage on Charisma checks.",
                "mood_loss": 6,
            },
            "feral": {
                "name": "Feral Shift (Feral)",
                "dc": 15,
                "next": "unsentient",
                "effect": (
                    "Speech frays into snarls; cannot court or groom; "
                    "disadvantage on Intelligence, Wisdom, and Charisma."
                ),
                "mood_loss": 8,
                "blocks_social": True,
                "hunt_mult": 0.9,
            },
            "unsentient": {
                "name": "Mind-Fracture (Unsentient)",
                "dc": 17,
                "next": None,
                "effect": (
                    "Wolf lost to the wild; instinct only (**RP fantasy**). Can still "
                    "eat, drink, and receive den care, but cannot hunt, patrol, explore, "
                    "court, or socialize. Pack must decide your fate."
                ),
                "blocks_social": True,
                "blocks_field": True,
                "hunt_mult": 0.5,
                "mood_loss": 6,
            },
        },
    },
    "insomnia": {
        "label": "The Sleepless",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "restless",
        "stages": {
            "restless": {
                "name": "The Sleepless (Restless)",
                "dc": 11,
                "next": "sleepless",
                "effect": (
                    "Sleep won't come: −4 mood each sunrise; "
                    "**chamomile**, **lavender**, or **valerian** tea helps."
                ),
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "sleepless": {
                "name": "The Sleepless (Deep)",
                "dc": 13,
                "next": "exhaustion_cascade",
                "effect": (
                    "Days blur without rest: +1 exhaustion; −6 mood; "
                    "**valerian** or **lavender** (2 doses) or **poppy seeds**."
                ),
                "mood_loss": 6,
                "exhaustion_gain": 1,
            },
            "exhaustion_cascade": {
                "name": "The Sleepless (Exhaustion Cascade)",
                "dc": 15,
                "next": None,
                "effect": (
                    "Body runs on fumes: +1 exhaustion; −8 mood; −15% hunt bones; "
                    "strong **poppy** sedation and den rest only."
                ),
                "mood_loss": 8,
                "exhaustion_gain": 1,
                "hunt_mult": 0.85,
            },
        },
    },
    "anxiety": {
        "label": "The Skitters",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "uneasy",
        "stages": {
            "uneasy": {
                "name": "The Skitters (Uneasy)",
                "dc": 11,
                "next": "anxious",
                "effect": (
                    "Every sound feels like a threat: −4 mood; "
                    "**chamomile**, **catmint**, or **borage** steadies nerves."
                ),
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "anxious": {
                "name": "The Skitters (Anxious)",
                "dc": 13,
                "next": "panic_prone",
                "effect": (
                    "Heart hammers; breath short: −6 mood; disadvantage on Wisdom saves; "
                    "**chamomile** (2 doses), **passionflower**, or **dried skullcap**."
                ),
                "mood_loss": 6,
            },
            "panic_prone": {
                "name": "The Skitters (Panic-Prone)",
                "dc": 15,
                "next": None,
                "effect": (
                    "Panic closes in without warning: −8 mood; +1 exhaustion; "
                    "blocks courtship until calmed; **valerian** or **poppy seeds**."
                ),
                "mood_loss": 8,
                "exhaustion_gain": 1,
                "blocks_social": True,
            },
        },
    },
    "grief_melancholy": {
        "label": "The Hollowing",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "mourning",
        "stages": {
            "mourning": {
                "name": "The Hollowing (Mourning)",
                "dc": 12,
                "next": "melancholy",
                "effect": (
                    "Loss sits heavy: −6 mood each sunrise; "
                    "**chamomile**, **lavender**, **borage**, or pack comfort."
                ),
                "mood_loss": 6,
                "cure_on_save": True,
            },
            "melancholy": {
                "name": "The Hollow",
                "dc": 14,
                "next": "hollow",
                "effect": (
                    "Joy feels far away: −8 mood; −10 hunger; "
                    "**lavender**, **meadowsweet**, or **rosemary** at burial rites."
                ),
                "mood_loss": 8,
                "hunger_loss": 10,
            },
            "hollow": {
                "name": "The Husk",
                "dc": 16,
                "next": None,
                "effect": (
                    "Empty and unreachable: −6 mood; blocks socialize; "
                    "den care and time; **valerian** may ease the worst nights."
                ),
                "mood_loss": 6,
                "blocks_social": True,
            },
        },
    },
    "delirium": {
        "label": "Fever-Wander",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "feverish",
        "stages": {
            "feverish": {
                "name": "Fever-Wander (Feverish)",
                "dc": 12,
                "next": "wandering",
                "effect": (
                    "Fever dreams bleed into waking: −4 mood; "
                    "**dried skullcap**, **lavender**, or fever herbs."
                ),
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "wandering": {
                "name": "Fever-Wander (Wandering)",
                "dc": 14,
                "next": "incoherent",
                "effect": (
                    "Trails and names slip; disadvantage on Intelligence; "
                    "**dried skullcap** (2 doses) or **valerian** rest."
                ),
                "mood_loss": 6,
            },
            "incoherent": {
                "name": "Fever-Wander (Incoherent)",
                "dc": 16,
                "next": None,
                "effect": (
                    "Speech breaks into nonsense; blocks field work; "
                    "sedating rest and Medic watch."
                ),
                "mood_loss": 8,
                "blocks_field": True,
            },
        },
    },
    "pack_madness": {
        "label": "Den-Madness",
        "contagious": 0.08,
        "mental": True,
        "spread_stage": "wary",
        "stages": {
            "wary": {
                "name": "Den-Madness (Wary)",
                "dc": 12,
                "next": "paranoid",
                "effect": (
                    "Eyes everywhere: −4 mood; disadvantage on Charisma with strangers; "
                    "**chamomile** or **douglas sagewort**."
                ),
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "paranoid": {
                "name": "Den-Madness (Paranoid)",
                "dc": 14,
                "next": "break",
                "effect": (
                    "Packmates feel like enemies: −8 mood; disadvantage on Charisma; "
                    "**dried skullcap** or **valerian** under Medic care."
                ),
                "mood_loss": 8,
            },
            "break": {
                "name": "Den-Madness (Break)",
                "dc": 16,
                "next": None,
                "effect": (
                    "Mind turns on the den; blocks socialize and courtship; "
                    "quarantine and sedatives only."
                ),
                "mood_loss": 6,
                "blocks_social": True,
            },
        },
    },
    "obsession": {
        "label": "The Fixing",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "fixated",
        "stages": {
            "fixated": {
                "name": "The Fixing (Fixated)",
                "dc": 12,
                "next": "compulsive",
                "effect": (
                    "One thought won't leave: −4 mood; disadvantage on Intelligence "
                    "checks not about the fixation; **rosemary** or **chamomile**."
                ),
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "compulsive": {
                "name": "The Fixing (Compulsive)",
                "dc": 14,
                "next": "tunnel_vision",
                "effect": (
                    "Rituals take over the day: −6 mood; −15% hunt bones; "
                    "**dried skullcap** or **meadowsweet**."
                ),
                "mood_loss": 6,
                "hunt_mult": 0.85,
            },
            "tunnel_vision": {
                "name": "The Fixing (Tunnel Vision)",
                "dc": 16,
                "next": None,
                "effect": (
                    "Nothing else exists; blocks socialize; disadvantage on Wisdom; "
                    "den rest and **valerian**."
                ),
                "mood_loss": 8,
                "blocks_social": True,
            },
        },
    },
    "night_terrors": {
        "label": "The Screaming-Sleep",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "restless_nights",
        "stages": {
            "restless_nights": {
                "name": "The Screaming-Sleep (Restless)",
                "dc": 11,
                "next": "screaming_dreams",
                "effect": (
                    "Sleep shatters at every noise: −4 mood; "
                    "**lavender**, **chamomile**, or **passionflower**."
                ),
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "screaming_dreams": {
                "name": "The Screaming-Sleep (Screaming Dreams)",
                "dc": 13,
                "next": "sleep_panic",
                "effect": (
                    "The den wakes to your cries: −6 mood; +1 exhaustion; "
                    "**valerian** or **poppy seeds** before sleep."
                ),
                "mood_loss": 6,
                "exhaustion_gain": 1,
            },
            "sleep_panic": {
                "name": "The Screaming-Sleep (Sleep Panic)",
                "dc": 15,
                "next": None,
                "effect": (
                    "Fear of closing eyes: −8 mood; blocks field work until calmed; "
                    "**valerian** sedation and den watch."
                ),
                "mood_loss": 8,
                "blocks_field": True,
            },
        },
    },
    "chronic_stress": {
        "label": "The Fraying",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "tense",
        "stages": {
            "tense": {
                "name": "The Fraying (Tense)",
                "dc": 11,
                "next": "strained",
                "effect": (
                    "Shoulders never drop: −4 mood; "
                    "**meadowsweet**, **douglas sagewort**, or rest."
                ),
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "strained": {
                "name": "The Fraying (Strained)",
                "dc": 13,
                "next": "frayed",
                "effect": (
                    "Every task feels too heavy: −6 mood; +1 exhaustion on failed save; "
                    "**meadowsweet** or **chamomile**."
                ),
                "mood_loss": 6,
            },
            "frayed": {
                "name": "The Fraying (Frayed)",
                "dc": 15,
                "next": None,
                "effect": (
                    "One more thing will snap: −8 mood; +1 exhaustion each sunrise; "
                    "−20% hunt bones; den rest required."
                ),
                "mood_loss": 8,
                "exhaustion_gain": 1,
                "hunt_mult": 0.8,
            },
        },
    },
    "eating_distress": {
        "label": "The Refusing",
        "contagious": 0.0,
        "mental": True,
        "spread_stage": "picky",
        "stages": {
            "picky": {
                "name": "The Refusing (Picky)",
                "dc": 11,
                "next": "refusing",
                "effect": (
                    "Food turns to ash: −6 hunger; −4 mood; "
                    "**chamomile**, **meadowsweet**, or honey."
                ),
                "hunger_loss": 6,
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "refusing": {
                "name": "The Refusing (Deep)",
                "dc": 13,
                "next": "wasting",
                "effect": (
                    "Won't keep meals down: −10 hunger; −6 mood; "
                    "**chervil**, **watermint**, or **meadowsweet**."
                ),
                "hunger_loss": 10,
                "mood_loss": 6,
            },
            "wasting": {
                "name": "The Refusing (Wasting)",
                "dc": 15,
                "next": None,
                "effect": (
                    "Body thins from refusal: −12 hunger; −1 HP/sunrise; "
                    "Medic feeding and **borage** support."
                ),
                "hunger_loss": 12,
                "hp_loss": 1,
                "mood_loss": 6,
            },
        },
    },
    "asthma": {
        "label": "Tight-Chest",
        "contagious": 0.0,
        "chronic": True,
        "respiratory": True,
        "spread_stage": "tight",
        "stages": {
            "tight": {
                "name": "Tight-Chest (Tight)",
                "dc": 12,
                "next": "wheeze",
                "effect": (
                    "Airways narrow under exertion: −10% hunt bones; "
                    "**mullein** or **lungwort** eases breathing."
                ),
                "hunt_mult": 0.9,
                "cure_on_save": True,
            },
            "wheeze": {
                "name": "Tight-Chest (Wheeze)",
                "dc": 14,
                "next": "crisis",
                "effect": "Wheezing breath and low stamina: +1 exhaustion; −25% hunt bones.",
                "exhaustion_gain": 1,
                "hunt_mult": 0.75,
            },
            "crisis": {
                "name": "Tight-Chest (Crisis)",
                "dc": 17,
                "next": None,
                "effect": (
                    "Breath won't come at all under strain: −1 HP/sunrise; "
                    "−50% hunt bones; fatal without den rest and **mullein**."
                ),
                "hp_loss": 1,
                "hunt_mult": 0.5,
                "lethal": True,
            },
        },
    },
    "bloat": {
        "label": "Gut-Twist",
        "contagious": 0.0,
        "spread_stage": "distension",
        "stages": {
            "distension": {
                "name": "Gut-Twist (Distension)",
                "dc": 13,
                "next": "torsion",
                "effect": (
                    "Belly swells tight after gorging; pacing and drooling; −6 mood; "
                    "**fennel** or **garden mint** may settle it."
                ),
                "mood_loss": 6,
                "thirst_loss": 4,
                "cure_on_save": True,
            },
            "torsion": {
                "name": "Gut-Twist (Torsion)",
                "dc": 18,
                "next": None,
                "effect": (
                    "Gut twists on itself; cannot hunt or range until treated; "
                    "−2 HP/sunrise; fatal without a Medic's care."
                ),
                "hp_loss": 2,
                "blocks_field": True,
                "lethal": True,
            },
        },
    },
    "bronchitis": {
        "label": "Rasp-Chest",
        "contagious": 0.30,
        "respiratory": True,
        "spread_stage": "irritated",
        "stages": {
            "irritated": {
                "name": "Rasp-Chest (Irritated)",
                "dc": 12,
                "next": "productive",
                "effect": (
                    "Dry rasping cough deep in the chest: −4 mood; "
                    "**mullein**, **lungwort**, or **plantain** soothes it."
                ),
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "productive": {
                "name": "Rasp-Chest (Wet Cough)",
                "dc": 14,
                "next": "chronic",
                "effect": "Wet, rattling cough: +1 exhaustion; −15% hunt bones.",
                "exhaustion_gain": 1,
                "hunt_mult": 0.85,
            },
            "chronic": {
                "name": "Rasp-Chest (Chronic)",
                "dc": 16,
                "next": None,
                "effect": "Lingers deep in the lungs: −1 HP/sunrise; −30% hunt bones.",
                "hp_loss": 1,
                "hunt_mult": 0.7,
            },
        },
    },
    "constipation": {
        "label": "The Stopping",
        "contagious": 0.0,
        "spread_stage": "blocked",
        "stages": {
            "blocked": {
                "name": "The Stopping (Blocked)",
                "dc": 11,
                "next": "impacted",
                "effect": (
                    "Gut backs up; strained and uncomfortable: −4 hunger; −4 mood; "
                    "**bindweed** or extra water."
                ),
                "hunger_loss": 4,
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "impacted": {
                "name": "The Stopping (Impacted)",
                "dc": 14,
                "next": None,
                "effect": "Gut fully blocked: −8 hunger; −1 HP/sunrise; needs Medic care.",
                "hunger_loss": 8,
                "hp_loss": 1,
                "mood_loss": 6,
            },
        },
    },
    "depression": {
        "label": "The Dimming",
        "contagious": 0.0,
        "chronic": True,
        "mental": True,
        "spread_stage": "numb",
        "stages": {
            "numb": {
                "name": "The Dimming (Numb)",
                "dc": 12,
                "next": "withdrawn",
                "effect": (
                    "Days blur gray and flavorless: −6 mood each sunrise; "
                    "**borage** or pack comfort."
                ),
                "mood_loss": 6,
                "cure_on_save": True,
            },
            "withdrawn": {
                "name": "The Dimming (Withdrawn)",
                "dc": 14,
                "next": "despair",
                "effect": (
                    "Pulls away from the den: −8 mood; −6 hunger; "
                    "**borage** and steady den care."
                ),
                "mood_loss": 8,
                "hunger_loss": 6,
            },
            "despair": {
                "name": "The Dimming (Despair)",
                "dc": 17,
                "next": None,
                "effect": (
                    "Nothing left to reach for: −10 mood; −8 hunger; blocks socialize; "
                    "den care, patience, and time."
                ),
                "mood_loss": 10,
                "hunger_loss": 8,
                "blocks_social": True,
            },
        },
    },
    "gallstones": {
        "label": "Stone-Gall",
        "contagious": 0.0,
        "chronic": True,
        "spread_stage": "forming",
        "stages": {
            "forming": {
                "name": "Stone-Gall (Forming)",
                "dc": 13,
                "next": "blocking",
                "effect": (
                    "Dull ache under the ribs after rich meals: −4 mood; −4 hydration; "
                    "**celandine** may dissolve it early."
                ),
                "mood_loss": 4,
                "thirst_loss": 4,
                "cure_on_save": True,
            },
            "blocking": {
                "name": "Stone-Gall (Blocking)",
                "dc": 17,
                "next": None,
                "effect": (
                    "Bile duct blocked; yellowing and pain: −1 HP/sunrise; −8 hydration; "
                    "fatal without a Medic's care."
                ),
                "hp_loss": 1,
                "thirst_loss": 8,
                "lethal": True,
            },
        },
    },
    "leptospirosis": {
        "label": "Foul-Water Fever",
        "contagious": 0.08,
        "mating_contagious": 0.0,
        "spread_stage": "fever",
        "stages": {
            "fever": {
                "name": "Foul-Water Fever (Fever)",
                "dc": 13,
                "next": "kidney_strain",
                "effect": (
                    "Fever from tainted water or infected urine: +1 exhaustion; −6 hydration; "
                    "**dandelion** or **watermint** early on."
                ),
                "exhaustion_gain": 1,
                "thirst_loss": 6,
                "cure_on_save": True,
            },
            "kidney_strain": {
                "name": "Foul-Water Fever (Kidney Strain)",
                "dc": 16,
                "next": "organ_failure",
                "effect": "Kidneys strain to keep up: −10 hydration; −1 HP/sunrise; −20% hunt bones.",
                "thirst_loss": 10,
                "hp_loss": 1,
                "hunt_mult": 0.8,
            },
            "organ_failure": {
                "name": "Foul-Water Fever (Organ Failure)",
                "dc": 19,
                "next": None,
                "effect": "Kidneys and liver fail together: −2 HP/sunrise; −12 hydration.",
                "hp_loss": 2,
                "thirst_loss": 12,
                "lethal": True,
            },
        },
    },
    "lyme": {
        "label": "Tick-Bite Fever",
        "contagious": 0.0,
        "chronic": True,
        "spread_stage": "bullseye",
        "stages": {
            "bullseye": {
                "name": "Tick-Bite Fever (Bite Mark)",
                "dc": 12,
                "next": "joint_ache",
                "effect": (
                    "A ring-marked bite lingers and itches: −4 mood; "
                    "**willow bark** or **goldenrod** early on."
                ),
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "joint_ache": {
                "name": "Tick-Bite Fever (Joint Ache)",
                "dc": 15,
                "next": "chronic_lyme",
                "effect": "Infection settles in the joints: disadvantage on Dexterity; −15% hunt bones.",
                "hunt_mult": 0.85,
            },
            "chronic_lyme": {
                "name": "Tick-Bite Fever (Chronic)",
                "dc": 18,
                "next": None,
                "effect": "Joints ache for good on damp days: −30% hunt bones; −6 mood.",
                "hunt_mult": 0.7,
                "mood_loss": 6,
            },
        },
    },
    "tooth_infection": {
        "label": "Rot-Fang",
        "contagious": 0.0,
        "spread_stage": "abscess",
        "stages": {
            "abscess": {
                "name": "Rot-Fang (Abscess)",
                "dc": 13,
                "next": "sepsis_risk",
                "effect": (
                    "A cracked tooth festers at the root: −4 mood; disadvantage on bite attacks; "
                    "**alder bark** or **prickly ash** eases it."
                ),
                "mood_loss": 4,
                "hunt_mult": 0.9,
                "cure_on_save": True,
            },
            "sepsis_risk": {
                "name": "Rot-Fang (Spreading)",
                "dc": 17,
                "next": None,
                "effect": (
                    "Infection spreads past the jaw into the blood: −1 HP/sunrise; −6 mood; "
                    "fatal without a Medic's care."
                ),
                "hp_loss": 1,
                "mood_loss": 6,
                "lethal": True,
            },
        },
    },
    "urinary_infection": {
        "label": "Sting-Water",
        "contagious": 0.0,
        "spread_stage": "irritation",
        "stages": {
            "irritation": {
                "name": "Sting-Water (Irritation)",
                "dc": 11,
                "next": "spreading",
                "effect": (
                    "Stinging discomfort passing water: −6 hydration; −4 mood; "
                    "**bindweed**, **goldenrod**, or extra water."
                ),
                "thirst_loss": 6,
                "mood_loss": 4,
                "cure_on_save": True,
            },
            "spreading": {
                "name": "Sting-Water (Spreading)",
                "dc": 15,
                "next": None,
                "effect": "Infection climbs toward the kidneys: −10 hydration; −1 HP/sunrise.",
                "thirst_loss": 10,
                "hp_loss": 1,
                "mood_loss": 6,
            },
        },
    },
    "worms": {
        "label": "Belly-Crawlers",
        "contagious": 0.10,
        "spread_stage": "mild_burden",
        "stages": {
            "mild_burden": {
                "name": "Belly-Crawlers (Mild)",
                "dc": 11,
                "next": "heavy_burden",
                "effect": (
                    "Parasites from raw prey sap strength quietly: −6 hunger each sunrise; "
                    "**tansy** or **knotgrass** clears them early."
                ),
                "hunger_loss": 6,
                "cure_on_save": True,
            },
            "heavy_burden": {
                "name": "Belly-Crawlers (Heavy)",
                "dc": 14,
                "next": None,
                "effect": (
                    "Burden grows heavy: −12 hunger; −15% hunt bones; "
                    "pups hit hardest by the drain."
                ),
                "hunger_loss": 12,
                "hunt_mult": 0.85,
                "juvenile_hp_loss": 2,
            },
        },
    },
}

# Backward compat for imports from herbs.py
DISEASE_STAGES = COUGH_STAGES

LEGACY_COUGH_STAGES = frozenset(COUGH_STAGES.keys())

MULTI_STAGE_DISEASES = frozenset(
    {
        "rot_lung",
        "shaking_sickness",
        "rabies",
        "wasting_sickness",
        "river_rot",
        "cancer",
        "dementia",
        "feral_shift",
        "insomnia",
        "anxiety",
        "grief_melancholy",
        "delirium",
        "pack_madness",
        "obsession",
        "night_terrors",
        "chronic_stress",
        "eating_distress",
        "mild_poison",
        "leafbare_cough",
        "asthma",
        "bloat",
        "bronchitis",
        "constipation",
        "depression",
        "gallstones",
        "leptospirosis",
        "lyme",
        "tooth_infection",
        "urinary_infection",
        "worms",
    }
)

MENTAL_DISEASES = frozenset(
    {
        "shock_emotional",
        "dementia",
        "feral_shift",
        "insomnia",
        "anxiety",
        "grief_melancholy",
        "delirium",
        "pack_madness",
        "obsession",
        "night_terrors",
        "chronic_stress",
        "eating_distress",
        "depression",
    }
)

# Herbs only cure these stages (later stages need mercy or are irreversible).
HERB_CURE_STAGES: dict[str, frozenset[str]] = {
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
    "leafbare_cough": frozenset({"chill", "hacking"}),
}


def encode_disease(disease_key: str, stage: str) -> str:
    if disease_key == "cough":
        return stage
    if disease_key in MULTI_STAGE_DISEASES:
        return f"{disease_key}:{stage}"
    return disease_key


def parse_disease(raw: str | None) -> tuple[str | None, str | None]:
    """return (disease_key, stage_key). cough legacy: mild/severe/deadly."""
    if not raw:
        return None, None
    if raw == "den_fever":
        raw = "redscratch"
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


def get_stage_info(disease_key: str, stage: str) -> dict | None:
    disease = DISEASES.get(disease_key)
    if not disease:
        return None
    return disease["stages"].get(stage)


def disease_display(user) -> tuple[str, str] | None:
    """return (name, effect) for primary physical/mental illness in users.disease."""
    displays = illness_displays(user)
    return displays[0] if displays else None


def illness_displays(user) -> list[tuple[str, str]]:
    """primary disease plus fever-delirium overlay (herb_buffs.mental_disease)."""
    lines: list[tuple[str, str]] = []
    raw = user["disease"] if user and "disease" in user.keys() else None
    key, stage = parse_disease(raw)
    if key and stage:
        info = get_stage_info(key, stage)
        if info:
            lines.append((info["name"], info["effect"]))
    from engine.herb_buffs import get_buffs

    overlay = get_buffs(user).get("mental_disease") if user else None
    if overlay:
        o_key, o_stage = parse_disease(str(overlay))
        if o_key and o_stage and is_mental_disease(o_key):
            info = get_stage_info(o_key, o_stage)
            if info and (o_key, o_stage) != (key, stage):
                lines.append((info["name"], info["effect"]))
    return lines


def is_mental_disease(disease_key: str | None) -> bool:
    if not disease_key:
        return False
    if disease_key in MENTAL_DISEASES:
        return True
    return bool(DISEASES.get(disease_key, {}).get("mental"))


def disease_matches_cure(
    disease_key: str | None,
    stage: str | None,
    cures: tuple,
    *,
    herb_key: str | None = None,
) -> bool:
    if not disease_key or not cures:
        return False
    if disease_key == "insomnia" and stage == "exhaustion_cascade":
        return herb_key == "poppy_seeds" and "insomnia" in cures
    if disease_key == "insomnia" and stage == "sleepless" and herb_key:
        from engine.herb_buffs import DISEASE_DOSE_HERBS

        if herb_key in DISEASE_DOSE_HERBS and DISEASE_DOSE_HERBS[herb_key][0] == "insomnia":
            return False
    if disease_key == "anxiety" and stage == "uneasy" and herb_key:
        from engine.herb_buffs import DISEASE_DOSE_HERBS

        if herb_key in DISEASE_DOSE_HERBS and DISEASE_DOSE_HERBS[herb_key][0] == "anxiety":
            return False
    if disease_key == "delirium" and stage == "wandering" and herb_key:
        from engine.herb_buffs import DISEASE_DOSE_HERBS

        if herb_key in DISEASE_DOSE_HERBS and DISEASE_DOSE_HERBS[herb_key][0] == "delirium":
            return False
    if disease_key == "rot_lung":
        if stage == "necrosis":
            return herb_key == "belly_rip_fungus"
        if herb_key == "belly_rip_fungus":
            return True
        return "rot_lung" in cures
    allowed = HERB_CURE_STAGES.get(disease_key)
    if allowed is not None and stage not in allowed:
        return False
    if disease_key in cures:
        return True
    if stage and stage in cures and disease_key == "cough":
        return True
    return False


def contagious_rate(disease_key: str | None) -> float:
    if not disease_key:
        return 0.0
    return float(DISEASES.get(disease_key, {}).get("contagious", 0.0))


# Mating = prolonged close contact (saliva, skin, respiratory droplets).
# Respiratory illnesses: ~55% of den rollover rate. Contact illnesses: ~45%. Diarrhea: low filth risk.
MATING_RESPIRATORY_MULT = 0.55
MATING_RESPIRATORY_CAP = 0.70
MATING_CONTACT_MULT = 0.45
MATING_CONTACT_CAP = 0.55


def mating_contagious_rate(disease_key: str | None) -> float:
    """Mating spread for any illness; tiered by how the disease actually transmits."""
    if not disease_key:
        return 0.0
    disease = DISEASES.get(disease_key, {})
    if "mating_contagious" in disease:
        return float(disease["mating_contagious"])
    base = float(disease.get("contagious", 0.0))
    if base <= 0:
        return 0.0
    if disease.get("respiratory"):
        return min(MATING_RESPIRATORY_CAP, base * MATING_RESPIRATORY_MULT)
    return min(MATING_CONTACT_CAP, base * MATING_CONTACT_MULT)


def blocks_social(disease_key: str | None, stage: str | None) -> bool:
    if not disease_key or not stage:
        return False
    info = get_stage_info(disease_key, stage)
    return bool(info and info.get("blocks_social"))


def blocks_field(disease_key: str | None, stage: str | None) -> bool:
    """Block hunt, patrol, explore, and similar field commands (not eat/drink/vitals)."""
    if not disease_key or not stage:
        return False
    info = get_stage_info(disease_key, stage)
    return bool(info and (info.get("blocks_field") or info.get("blocks_activity")))


def blocks_all_activity(disease_key: str | None, stage: str | None) -> bool:
    """Deprecated alias; use blocks_field for partial command blocks."""
    return blocks_field(disease_key, stage)


def is_chronic_disease(disease_key: str | None) -> bool:
    if not disease_key:
        return False
    return bool(DISEASES.get(disease_key, {}).get("chronic"))


def blocks_conception(disease_key: str | None, stage: str | None) -> bool:
    if not disease_key or not stage:
        return False
    info = get_stage_info(disease_key, stage)
    return bool(info and info.get("blocks_conception"))


def spread_stage_for(disease_key: str) -> str:
    disease = DISEASES.get(disease_key, {})
    return disease.get("spread_stage") or next(iter(disease.get("stages", {"active": {}})))
