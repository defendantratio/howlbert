"""Per-wolf RP skill bonuses and weaknesses; stored as JSON on users.character_traits."""

from __future__ import annotations

import copy
import json

from rpg_rules import SKILLS

LABEL_TO_SKILL = {info[1].lower(): key for key, info in SKILLS.items()}

MIREWORT_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Herbal Mastery (Swamp)",
            "modifier": 6,
            "skills": ["herblore"],
            "packs": ["mistmoor"],
            "blurb": (
                "Knows every toxic, curative, and hallucinogenic plant in the Rotting Mere; "
                "poultices draw infection overnight."
            ),
        },
        {
            "name": "Wound-Tending",
            "modifier": 5,
            "skills": ["medicine"],
            "treat_heal_bonus": 1,
            "clears_infection_on_heal": True,
            "blurb": (
                "Cleans, sews, and packs wounds with rot-fighting muds; unerring eye for infection."
            ),
        },
        {
            "name": "Swamp Navigation",
            "modifier": 3,
            "skills": ["survival", "stealth", "tracking"],
            "packs": ["mistmoor"],
            "blurb": (
                "Knows sinkholes and safe paths; moves silently through standing water."
            ),
        },
    ],
    "weaknesses": [
        {
            "name": "Physically Frail",
            "modifier": -4,
            "attrs": ["attr_str", "attr_dex", "attr_con"],
            "combat": True,
            "blurb": (
                "Swamp-rot and a limp; cannot fight; strength and stamina tasks suffer heavily."
            ),
        },
        {
            "name": "Morbid Detachment",
            "modifier": -2,
            "skills": ["persuasion"],
            "blurb": (
                "Unsettling calm around death; comfort and morale checks go poorly."
            ),
        },
        {
            "name": "Obsession with the Belly-Rip",
            "modifier": -1,
            "attrs": ["attr_int", "attr_wis"],
            "exclude_skills": ["herblore", "medicine"],
            "blurb": (
                "Monthly vigils at the sinkhole cloud memory and clarity."
            ),
        },
    ],
}


SPLINTER_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "blurb": "Moves quietly on three legs; learned to be invisible.",
        },
        {
            "name": "Survival",
            "modifier": 3,
            "skills": ["survival"],
            "blurb": "Finds food where other wolves starve.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "blurb": "Follows pack patrols to find weaknesses.",
        },
    ],
    "weaknesses": [
        {
            "name": "Missing Leg",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "combat": True,
            "blurb": "Three-legged; slower than four-legged wolves; cannot climb or swim well.",
        },
        {
            "name": "Despised",
            "modifier": -3,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "No pack will take him; he has no allies.",
        },
        {
            "name": "Guilty",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking"],
            "blurb": "Haunted by the wolf he killed; might surrender if confronted.",
        },
    ],
}


MOTH_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "blurb": "Excellent at hiding; can vanish into shadows.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "blurb": "Sharp nose; follows scents to hidden caches.",
        },
        {
            "name": "Persuasion",
            "modifier": 3,
            "skills": ["persuasion"],
            "blurb": "Timidness makes wolves underestimate her; she gathers information.",
        },
    ],
    "weaknesses": [
        {
            "name": "Physically Weak",
            "modifier": -3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Cannot fight; one solid blow would drop her.",
        },
        {
            "name": "Timid",
            "modifier": -3,
            "skills": ["intimidation"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["persuasion"],
            "blurb": "Freezes when confronted; has never won a direct challenge.",
        },
        {
            "name": "Haunted",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking"],
            "blurb": "Sees her mother's death in her dreams.",
        },
    ],
}


SCAB_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "blurb": "Moves quietly through the caves; knows every hidden crevice.",
        },
        {
            "name": "Intimidation",
            "modifier": 3,
            "skills": ["intimidation"],
            "blurb": "His mangy, scarred appearance alone makes wolves recoil.",
        },
        {
            "name": "Survival",
            "modifier": 3,
            "skills": ["survival"],
            "blurb": "Survives on scraps that would starve other wolves.",
        },
    ],
    "weaknesses": [
        {
            "name": "Despised",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["intimidation"],
            "blurb": "No allies; no one would speak for him.",
        },
        {
            "name": "Sickly",
            "modifier": -3,
            "attrs": ["attr_con"],
            "combat": True,
            "blurb": "Mange and infection; one good fight could kill him.",
        },
        {
            "name": "Untrustworthy",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["survival"],
            "blurb": "Will betray anyone for a meal.",
        },
    ],
}


SLEET_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Persuasion",
            "modifier": 3,
            "skills": ["persuasion"],
            "blurb": "Can turn an enemy into a reluctant ally.",
        },
        {
            "name": "Intimidation",
            "modifier": 3,
            "skills": ["intimidation"],
            "blurb": "Calm threats are more frightening than screaming.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Reads micro-expressions and hidden motives.",
        },
    ],
    "weaknesses": [
        {
            "name": "Cold Reputation",
            "modifier": -2,
            "skills": ["persuasion"],
            "blurb": "Other packs trust her skill but not her heart.",
        },
        {
            "name": "Loyal to Greyspire",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking"],
            "blurb": "Will never betray her pack, even when they are wrong.",
        },
        {
            "name": "Scarred Lip",
            "modifier": -2,
            "skills": ["persuasion"],
            "blurb": "Her lip twitches when she lies; gives her away.",
        },
    ],
}


HAREPUP_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Running",
            "modifier": 3,
            "attrs": ["attr_dex"],
            "skills": ["stealth"],
            "blurb": "Exceptionally fast; can outrun most yearlings.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "blurb": "Sharp nose; follows rabbit trails for fun.",
        },
    ],
    "weaknesses": [
        {
            "name": "Lonely",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Desperate for friends, but drives them away with her attitude.",
        },
        {
            "name": "Impatient",
            "modifier": -2,
            "skills": ["stealth"],
            "attrs": ["attr_wis"],
            "blurb": "Cannot sit still; fails at stealth and ambush.",
        },
        {
            "name": "No Fighting Skill",
            "modifier": -3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "All speed, no strength; one solid hit would drop her.",
        },
    ],
}


CINDERPUP_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Climbing",
            "modifier": 3,
            "attrs": ["attr_dex"],
            "blurb": "Surprisingly nimble on rock faces for his age.",
        },
        {
            "name": "Intimidation",
            "modifier": 3,
            "skills": ["intimidation"],
            "blurb": "Loud bark and puffed-up chest make other pups flinch.",
        },
    ],
    "weaknesses": [
        {
            "name": "Fear of Heights",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "blurb": "Freezes on exposed ledges; the fear he tries to hide.",
        },
        {
            "name": "Overconfident",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "blurb": "Picks fights with older pups and loses badly.",
        },
        {
            "name": "Nightmares",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "blurb": "Sleeps poorly; wakes the den with whimpers.",
        },
    ],
}


RIME_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Medicine",
            "modifier": 4,
            "skills": ["medicine"],
            "blurb": "Treats minor wounds and identifies common illnesses.",
        },
        {
            "name": "Persuasion",
            "modifier": 3,
            "skills": ["persuasion"],
            "blurb": "Calms frightened pups and breaks up fights.",
        },
        {
            "name": "Survival",
            "modifier": 3,
            "skills": ["survival"],
            "blurb": "Knows which dens stay warm in leaf-bare.",
        },
    ],
    "weaknesses": [
        {
            "name": "Old Injuries",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "combat": True,
            "blurb": "Limping hip; cannot run or defend the den from predators.",
        },
        {
            "name": "Emotionally Closed",
            "modifier": -3,
            "attrs": ["attr_cha"],
            "exclude_skills": ["persuasion"],
            "blurb": "Cannot show affection; pups find her cold.",
        },
        {
            "name": "Haunted by Stillbirths",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["medicine"],
            "blurb": "Avoids pregnant wolves; cannot bear to watch them.",
        },
    ],
}


TALUS_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Hunting",
            "modifier": 4,
            "skills": ["hunting"],
            "blurb": "Fast and agile; specializes in hares, ptarmigan, and small prey.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "blurb": "Sharp nose; can follow a cold trail.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "blurb": "Moves quietly on snow and loose rock.",
        },
    ],
    "weaknesses": [
        {
            "name": "Easily Distracted",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "skills": ["hunting", "tracking"],
            "blurb": "Loses focus during long hunts.",
        },
        {
            "name": "Desperate to Prove Herself",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["hunting", "tracking", "stealth"],
            "blurb": "Takes unnecessary risks.",
        },
        {
            "name": "Lowbelly Scars",
            "modifier": -2,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Older wolves still sneer at her Lowbelly origins.",
        },
    ],
}


SLATE_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Hunting",
            "modifier": 4,
            "skills": ["hunting"],
            "blurb": "Specialist in mountain goats and sheep; ambush from above.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "blurb": "Moves silently on scree and loose rock.",
        },
        {
            "name": "Survival",
            "modifier": 3,
            "skills": ["survival"],
            "blurb": "Knows the high peaks better than most scouts.",
        },
    ],
    "weaknesses": [
        {
            "name": "Grumpy",
            "modifier": -3,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Drives away wolves who might otherwise help him.",
        },
        {
            "name": "Competitive with Ironjaw",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["hunting", "stealth", "survival"],
            "blurb": "Might take unnecessary risks to prove himself.",
        },
        {
            "name": "Old Shoulder Injury",
            "modifier": -2,
            "attrs": ["attr_dex"],
            "blurb": "Aches in cold weather, slowing him down.",
        },
    ],
}


IRONJAW_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Hunting",
            "modifier": 4,
            "skills": ["hunting"],
            "blurb": "Expert at close-range ambush and neck-snap kills.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "blurb": "Volcanic ash mask makes him nearly scentless.",
        },
        {
            "name": "Survival",
            "modifier": 3,
            "skills": ["survival"],
            "blurb": "Endures days without food; sleeps in snow dens.",
        },
    ],
    "weaknesses": [
        {
            "name": "Old Leg Injury",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "blurb": "Cannot chase fleeing prey; must kill quickly or lose the hunt.",
        },
        {
            "name": "Socially Withdrawn",
            "modifier": -3,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Other wolves find him unsettling; he has no allies.",
        },
        {
            "name": "Secret Guilt",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["survival"],
            "blurb": "Blames himself for the rescuer who died in the avalanche.",
        },
    ],
}


STONEPIERCER_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "blurb": "Moves across loose rock without a sound.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "blurb": "Reads stone scuffs, displaced pebbles, and scent on the wind.",
        },
        {
            "name": "Survival",
            "modifier": 3,
            "skills": ["survival"],
            "blurb": "Knows every water source and shelter in the high peaks.",
        },
    ],
    "weaknesses": [
        {
            "name": "Laconic",
            "modifier": -3,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Silence mistaken for hostility; few wolves trust xem.",
        },
        {
            "name": "Lowbelly Scars",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["intimidation"],
            "blurb": "High ranks still sneer at Lowbelly origins.",
        },
        {
            "name": "Sentimental Secret",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["survival", "tracking", "stealth"],
            "blurb": "If the stone pouch were discovered, xir reputation would shatter.",
        },
    ],
}


RAVEN_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "blurb": "Dark coat and grace; nearly invisible in shadow on loose stone.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Ears always moving; notices wind, voices, patrols first.",
        },
        {
            "name": "Scout's Instinct",
            "modifier": 3,
            "skills": ["survival"],
            "blurb": "Knows ridges, shortcuts, and the mountain's hiding places.",
        },
    ],
    "weaknesses": [
        {
            "name": "Small and Lanky",
            "modifier": -3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Not built for fighting; one solid blow could break him.",
        },
        {
            "name": "Talks Too Much",
            "modifier": -3,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Cannot stop asking questions; drives older wolves mad.",
        },
        {
            "name": "Fear of the Dark",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["stealth", "tracking", "survival"],
            "blurb": "Terrified of faceless shapes in shadow; freezes when pressed.",
        },
    ],
}


FROSTBURN_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Fighting",
            "modifier": 4,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Immovable in combat; endures blows that would fell others.",
        },
        {
            "name": "Intimidation",
            "modifier": 4,
            "skills": ["intimidation"],
            "blurb": "Pink eyes and silence make enemies hesitate.",
        },
        {
            "name": "Endurance",
            "modifier": 3,
            "attrs": ["attr_con"],
            "skills": ["survival"],
            "blurb": "Can stand watch for two days without sleep.",
        },
    ],
    "weaknesses": [
        {
            "name": "Blind",
            "modifier": -4,
            "attrs": ["attr_dex"],
            "combat": True,
            "blurb": "Cannot see; relies on scent, sound, and memory.",
        },
        {
            "name": "Mute",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["intimidation"],
            "blurb": "Cannot call for help; relies on others to relay messages.",
        },
        {
            "name": "Haunted",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["survival"],
            "blurb": "Nightmares of the eruption leave hir exhausted.",
        },
        {
            "name": "Too Gentle",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "combat": True,
            "exclude_skills": ["intimidation", "survival"],
            "blurb": "Hesitates to kill, even when necessary.",
        },
    ],
}


HEMLOCK_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Herblore",
            "modifier": 4,
            "skills": ["herblore"],
            "blurb": "Every high-altitude medicinal plant; wound-clotting and pain relief.",
        },
        {
            "name": "Medicine",
            "modifier": 4,
            "skills": ["medicine"],
            "blurb": "Smells infection before symptoms show.",
        },
        {
            "name": "Intimidation",
            "modifier": 3,
            "skills": ["intimidation"],
            "blurb": "Legendary insults; can make a Stoneguard cry.",
        },
    ],
    "weaknesses": [
        {
            "name": "Limp",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "combat": True,
            "blurb": "Cannot run or fight; relies on others to bring patients.",
        },
        {
            "name": "Fear of Heights",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["medicine", "herblore"],
            "blurb": "Panic attacks on exposed ledges.",
        },
        {
            "name": "Bitter",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["intimidation"],
            "blurb": "Resentment makes her careless with wolves she dislikes.",
        },
        {
            "name": "Clouded Eye",
            "modifier": -2,
            "skills": ["tracking"],
            "attrs": ["attr_wis", "attr_int"],
            "check_disadvantage": True,
            "blurb": "Puphood cataract; depth and distance fail her in low light.",
        },
    ],
}


THORN_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Fighting",
            "modifier": 4,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Fast and aggressive; uses his smaller size to get inside larger wolves' guard.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "blurb": "Surprisingly quiet for a wolf of his temperament.",
        },
        {
            "name": "Intimidation",
            "modifier": 3,
            "skills": ["intimidation"],
            "blurb": "Burn scars and wild eyes make him look dangerous.",
        },
    ],
    "weaknesses": [
        {
            "name": "Fear of Heights",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["stealth"],
            "blurb": "In a mountain pack; will freeze on exposed ledges.",
        },
        {
            "name": "Hot-Headed",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "combat": True,
            "exclude_skills": ["intimidation"],
            "blurb": "Picks fights he cannot win; needs someone to pull him back.",
        },
        {
            "name": "Insecure",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["intimidation"],
            "blurb": "Can be manipulated by any wolf who offers praise.",
        },
    ],
}


ICEFANG_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Moves across scree and loose rock without a sound.",
        },
        {
            "name": "Medicine",
            "modifier": 3,
            "skills": ["medicine"],
            "attrs": ["attr_wis"],
            "blurb": "Surprisingly skilled at treating wounds; though more for herself than others.",
        },
        {
            "name": "Intimidation",
            "modifier": 4,
            "skills": ["intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Filed teeth and blank stare break most wolves before a fight begins.",
        },
    ],
    "weaknesses": [
        {
            "name": "Emotionally Numb",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["intimidation"],
            "blurb": "Cannot read social cues or understand pack politics; easy to manipulate.",
        },
        {
            "name": "Chronic Mouth Pain",
            "modifier": -3,
            "attrs": ["attr_con"],
            "blurb": "Filed teeth cause constant low-level agony; wears on her stamina.",
        },
        {
            "name": "Blind Spot for Grim",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["medicine", "stealth", "intimidation"],
            "blurb": "Cannot conceive of Grim being wrong; loyalty could be exploited.",
        },
    ],
}


GRIM_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Intimidation",
            "modifier": 4,
            "skills": ["intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Can silence a howling pack with a look.",
        },
        {
            "name": "Hunting",
            "modifier": 3,
            "skills": ["hunting"],
            "attrs": ["attr_str"],
            "blurb": "Expert at ambushing mountain goats on narrow ledges.",
        },
        {
            "name": "Survival",
            "modifier": 3,
            "skills": ["survival"],
            "attrs": ["attr_wis"],
            "blurb": "Knows every cave and water source in the Spinefang range.",
        },
    ],
    "weaknesses": [
        {
            "name": "Paranoia",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["survival"],
            "blurb": "Sees betrayal in every shadow; has executed two wolves on suspicion alone.",
        },
        {
            "name": "Old Injury",
            "modifier": -2,
            "attrs": ["attr_dex"],
            "blurb": "Missing tail chunk affects balance on steep climbs.",
        },
        {
            "name": "No Heirs",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["survival", "hunting"],
            "blurb": "No mate, no pups, no clear successor; the pack will tear itself apart when he dies.",
        },
    ],
}


CINDER_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Endurance",
            "modifier": 3,
            "attrs": ["attr_con"],
            "skills": ["survival"],
            "blurb": "Has survived things that should have killed him.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Moves quietly; a habit from his time alone.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_int"],
            "blurb": "Learned to follow prey alone, without a pack.",
        },
    ],
    "weaknesses": [
        {
            "name": "Traumatized",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking", "stealth"],
            "blurb": "Panic attacks triggered by fire, smoke, or loud noises.",
        },
        {
            "name": "Missing Ear and Tail",
            "modifier": -2,
            "attrs": ["attr_dex"],
            "combat": True,
            "blurb": "Poor balance and hearing on his left side.",
        },
        {
            "name": "Desperate to Belong",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Could be manipulated by any wolf who offers him friendship.",
        },
    ],
}


PEBBLE_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Persuasion",
            "modifier": 3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "His honesty is disarming; wolves want to help him.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Notices micro-expressions because he is always watching for disapproval.",
        },
        {
            "name": "Survival",
            "modifier": 4,
            "skills": ["survival"],
            "attrs": ["attr_con"],
            "blurb": "Knows every safe crossing on the river.",
        },
    ],
    "weaknesses": [
        {
            "name": "Anxious",
            "modifier": -3,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Stutters, sweats, forgets; undermines his own authority.",
        },
        {
            "name": "Lonely",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking", "survival"],
            "blurb": "Desperately wants friends; could be manipulated with kindness.",
        },
        {
            "name": "Crooked Leg",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "combat": True,
            "blurb": "Cannot run; if a negotiation turns violent, he is dead.",
        },
    ],
}


DRIFTPUP_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Learned to hide from the fire; still good at disappearing.",
        },
        {
            "name": "Endurance",
            "modifier": 3,
            "attrs": ["attr_con"],
            "skills": ["survival"],
            "blurb": "Survived alone for a quarter-moon; tough for his age.",
        },
    ],
    "weaknesses": [
        {
            "name": "Traumatized",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["stealth", "survival"],
            "blurb": "Panic attacks triggered by fire, smoke, or loud noises.",
        },
        {
            "name": "Desperate to Belong",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Will do anything to be accepted; could be exploited.",
        },
        {
            "name": "Physically Weak",
            "modifier": -3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Small and scrawny; cannot fight or swim well.",
        },
    ],
}


RIPPLEPUP_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Swimming",
            "modifier": 4,
            "attrs": ["attr_dex"],
            "skills": ["survival"],
            "packs": ["silverrush"],
            "blurb": "Natural swimmer; webbed paws make her fast in water.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Feels the current in her bones.",
        },
    ],
    "weaknesses": [
        {
            "name": "No Fear",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking", "survival"],
            "blurb": "Will walk up to anything; monsters, deep water, strangers. Needs constant watching.",
        },
        {
            "name": "Obsessed with Iron",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking"],
            "blurb": "Collects dangerous scraps; could cut or poison herself.",
        },
        {
            "name": "Lonely",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Misses her littermates; desperately wants a friend.",
        },
    ],
}


RIPTIDE_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Swimming",
            "modifier": 4,
            "attrs": ["attr_dex"],
            "skills": ["survival"],
            "packs": ["silverrush"],
            "blurb": "Can dive and retrieve pups who wander too deep.",
        },
        {
            "name": "Medicine",
            "modifier": 3,
            "skills": ["medicine"],
            "attrs": ["attr_wis"],
            "blurb": "Basic pup care; clears airways, treats minor wounds.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Notices when a pup is about to wander off.",
        },
    ],
    "weaknesses": [
        {
            "name": "Anxious",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["medicine", "tracking"],
            "blurb": "Prone to panic attacks, especially during storms or floods.",
        },
        {
            "name": "Non-Fighter",
            "modifier": -3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Cannot defend the den; relies on guards.",
        },
        {
            "name": "Impostor Syndrome",
            "modifier": -2,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Constantly fears being exposed as a fraud.",
        },
    ],
}


EBB_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Learned to move silently to avoid twolegs; nearly invisible in tall grass.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Notices trap scents, hidden dangers, and subtle changes in the environment.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_int"],
            "blurb": "Excellent at following faint trails and identifying wolf scents from a distance.",
        },
    ],
    "weaknesses": [
        {
            "name": "Traumatized",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking", "stealth"],
            "blurb": "Panic attacks triggered by metal smells, loud noises, or enclosed spaces.",
        },
        {
            "name": "Desperate to Belong",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Will do anything to be accepted; could be exploited.",
        },
        {
            "name": "Physically Weak",
            "modifier": -3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Small and still recovering from malnutrition; cannot fight well.",
        },
    ],
}


CURLGRIP_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Swimming",
            "modifier": 4,
            "attrs": ["attr_dex"],
            "skills": ["survival"],
            "packs": ["silverrush"],
            "blurb": "Exceptionally fast and agile in water.",
        },
        {
            "name": "Hunting",
            "modifier": 3,
            "skills": ["hunting"],
            "attrs": ["attr_str"],
            "blurb": "Specializes in large fish and waterfowl.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Can stalk a fish in clear water without disturbing the surface.",
        },
    ],
    "weaknesses": [
        {
            "name": "Restless",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["hunting", "stealth", "survival"],
            "blurb": "Cannot sit still; paces, fidgets, drives other wolves mad.",
        },
        {
            "name": "Too Playful",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["stealth"],
            "blurb": "Sometimes turns a hunt into a game; has lost prey by showing off.",
        },
        {
            "name": "Secret Philosopher",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Theories about the Maw could be seen as heretical.",
        },
    ],
}


CHURN_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Swimming",
            "modifier": 4,
            "attrs": ["attr_dex"],
            "skills": ["survival"],
            "packs": ["silverrush"],
            "blurb": "Powerful and fast; can fight the strongest currents.",
        },
        {
            "name": "Hunting",
            "modifier": 3,
            "skills": ["hunting"],
            "attrs": ["attr_str"],
            "blurb": "Specializes in large fish; salmon, pike, sturgeon.",
        },
        {
            "name": "Endurance",
            "modifier": 3,
            "attrs": ["attr_con"],
            "skills": ["survival"],
            "blurb": "Can hold his breath for a surprising length of time.",
        },
    ],
    "weaknesses": [
        {
            "name": "Afraid of Deep Water",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["survival", "hunting"],
            "blurb": "Hides it well; but if he panics, he could drown.",
        },
        {
            "name": "Quiet",
            "modifier": -3,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Other wolves forget he exists; he has no allies.",
        },
        {
            "name": "Competitive",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["hunting", "survival"],
            "blurb": "Might take unnecessary risks to beat Aromis.",
        },
    ],
}


AROMIS_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Hunting",
            "modifier": 4,
            "skills": ["hunting"],
            "attrs": ["attr_str"],
            "blurb": "Can take down prey with a single, well-placed bite.",
        },
        {
            "name": "Fighting",
            "modifier": 3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Strong bite force; used to fighting alone, poor defense.",
        },
        {
            "name": "Herblore",
            "modifier": 2,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "blurb": "Basic knowledge of common healing herbs from pack healers.",
        },
    ],
    "weaknesses": [
        {
            "name": "Traumatic Bite Trigger",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["hunting", "herblore"],
            "blurb": "Bite marks on prey or wolves make him relive the attack; stares blankly, unable to speak.",
        },
        {
            "name": "Emotional Avoidance",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Strong feelings shut him down or make him lash out.",
        },
        {
            "name": "Low Empathy",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["intimidation"],
            "blurb": "Difficulty understanding others' pain; though he is trying to learn.",
        },
    ],
}


RIPPLE_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Medicine",
            "modifier": 4,
            "skills": ["medicine"],
            "attrs": ["attr_wis"],
            "treat_heal_bonus": 1,
            "blurb": "Excellent bedside manner; wolves heal faster around her.",
        },
        {
            "name": "Herblore",
            "modifier": 3,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "blurb": "Knows riverside herbs: willow bark, feverfew, watermint.",
        },
        {
            "name": "Persuasion",
            "modifier": 3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Can talk a wolf through panic, grief, or fear.",
        },
    ],
    "weaknesses": [
        {
            "name": "Limp",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "combat": True,
            "blurb": "Cannot run long distances; relies on others to bring patients.",
        },
        {
            "name": "Anxious",
            "modifier": -2,
            "attrs": ["attr_cha"],
            "exclude_skills": ["persuasion", "medicine"],
            "blurb": "Internalizes every death; blames herself when she cannot save someone.",
        },
        {
            "name": "Too Soft",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["medicine", "herblore", "persuasion"],
            "blurb": "Trouble making hard decisions; might hesitate when speed is needed.",
        },
    ],
}


RIFT_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Swimming",
            "modifier": 4,
            "attrs": ["attr_dex"],
            "skills": ["survival"],
            "packs": ["silverrush"],
            "blurb": "Strong and fast; crosses the river in a quarter of the time it takes others.",
        },
        {
            "name": "Fighting",
            "modifier": 3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Prefers to fight in water, where his reach and leverage are best.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Notices disturbances in the current; a sign of danger upstream.",
        },
    ],
    "weaknesses": [
        {
            "name": "Silent",
            "modifier": -3,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Wolves often forget he is there; misses social cues.",
        },
        {
            "name": "Guilt-Ridden",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking", "survival"],
            "blurb": "Will take unnecessary risks to protect Saltmuzzle.",
        },
        {
            "name": "Secret Love",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Could be exploited by an enemy who discovers his feelings for Saltmuzzle.",
        },
    ],
}


SALTMUZZLE_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Persuasion",
            "modifier": 4,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Can calm tempers and broker peace between enemies.",
        },
        {
            "name": "Swimming",
            "modifier": 3,
            "attrs": ["attr_dex"],
            "skills": ["survival"],
            "packs": ["silverrush"],
            "blurb": "Webbed paws make her among the fastest swimmers in the pack.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Reads other wolves' intentions with eerie accuracy.",
        },
    ],
    "weaknesses": [
        {
            "name": "Grieving",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "combat": True,
            "exclude_skills": ["persuasion", "tracking"],
            "blurb": "Her mate's death still haunts her; avoids battle.",
        },
        {
            "name": "Weary",
            "modifier": -2,
            "attrs": ["attr_dex"],
            "blurb": "Burnout makes her slow to act; sometimes misses opportunities.",
        },
        {
            "name": "Too Trusting",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["persuasion", "tracking"],
            "blurb": "Believes wolves can be better than they are; often wrong.",
        },
    ],
}


BARKHOLLOW_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Foraging",
            "modifier": 3,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "packs": ["thistlehide"],
            "blurb": "Knows every edible plant in Thistlehide.",
        },
        {
            "name": "Survival",
            "modifier": 3,
            "skills": ["survival"],
            "attrs": ["attr_wis"],
            "blurb": "Can find shelter and food in any weather.",
        },
        {
            "name": "Herblore",
            "modifier": 4,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "blurb": "Expert in medicinal plants.",
        },
    ],
    "weaknesses": [
        {
            "name": "Hollow Chest",
            "modifier": -4,
            "attrs": ["attr_con"],
            "combat": True,
            "blurb": "Cannot run or fight; a short sprint leaves her gasping.",
        },
        {
            "name": "Forgetful",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["herblore", "survival"],
            "blurb": "Leaves supplies behind; relies on others to remind him.",
        },
        {
            "name": "Slow",
            "modifier": -2,
            "attrs": ["attr_dex"],
            "blurb": "Wolves mock her pace; patience mistaken for stupidity.",
        },
    ],
}


FERNSPOT_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Foraging",
            "modifier": 3,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "packs": ["thistlehide"],
            "blurb": "Knows every edible root and berry in Thistlehide.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Moves quietly; uses it to leave offerings for Kanami unseen.",
        },
    ],
    "weaknesses": [
        {
            "name": "Guilt",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["herblore", "stealth"],
            "blurb": "Paralyzed by remorse; cannot confront what she did.",
        },
        {
            "name": "Anxious",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["stealth"],
            "blurb": "Always looking over her shoulder; afraid of being exposed.",
        },
        {
            "name": "Secretive",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Hidden offerings could be misunderstood as something else.",
        },
    ],
}


MOSSGAZE_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Foraging",
            "modifier": 4,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "packs": ["thistlehide"],
            "blurb": "Expert knowledge of edible and medicinal plants in misty, boggy, thorny terrain.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Quiet on wet stone, mud, and root-tangle; pushes through thistle where larger wolves hesitate.",
        },
        {
            "name": "Escape",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Excellent at squeezing through tight spaces and vanishing into undergrowth.",
        },
    ],
    "weaknesses": [
        {
            "name": "Small and Frail",
            "modifier": -4,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Cannot fight larger wolves or predators; loses any direct confrontation.",
        },
        {
            "name": "Social Anxiety",
            "modifier": -3,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Freezes or stumbles when addressed by authority; seems incompetent.",
        },
        {
            "name": "Overly Self-Reliant",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["herblore", "stealth"],
            "blurb": "Hides injuries rather than ask for help; nearly killed her twice.",
        },
    ],
}


THYME_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Persuasion",
            "modifier": 4,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Can find common ground between enemies.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Reads micro-expressions and hidden motives.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Moves quietly; useful for eavesdropping.",
        },
    ],
    "weaknesses": [
        {
            "name": "Private",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["intimidation"],
            "blurb": "Wolves do not trust zir; ze shares nothing of zirself.",
        },
        {
            "name": "Too Principled",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Refuses to lie, even when a lie would save lives.",
        },
        {
            "name": "Young",
            "modifier": -2,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Older diplomats dismiss zir as inexperienced; must fight for respect.",
        },
    ],
}


ROOT_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Medicine",
            "modifier": 4,
            "skills": ["medicine"],
            "attrs": ["attr_wis"],
            "blurb": "Experienced with pup ailments; fever, colic, and cough.",
        },
        {
            "name": "Persuasion",
            "modifier": 3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Can calm an angry mother or terrified pup with a few words.",
        },
        {
            "name": "Herblore",
            "modifier": 3,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "blurb": "Knows which plants are safe for teething pups to chew.",
        },
    ],
    "weaknesses": [
        {
            "name": "Old and Slow",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "combat": True,
            "blurb": "Cannot chase a pup who runs; needs help.",
        },
        {
            "name": "Stubborn",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Refuses to adapt to new ways; clashes with younger wolves.",
        },
        {
            "name": "Haunted by Loss",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["medicine", "herblore"],
            "blurb": "Her dead pups still visit her dreams.",
        },
    ],
}


MOSSHEART_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "packs": ["thistlehide"],
            "blurb": "Moves through thistle and bramble without a sound.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_int"],
            "blurb": "Can read the forest like a map.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Notices tiny changes; a snapped twig, a shifted stone.",
        },
    ],
    "weaknesses": [
        {
            "name": "Anxious",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking", "stealth"],
            "blurb": "Prone to panic attacks in high-stress situations.",
        },
        {
            "name": "Judgmental",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Alienates wolves who are not as fastidious as he is.",
        },
        {
            "name": "Secret Romance",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Forbidden love with a Silverrush wolf; could be used as leverage.",
        },
    ],
}


RIVENMAW_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Hunting",
            "modifier": 4,
            "skills": ["hunting"],
            "attrs": ["attr_str"],
            "blurb": "Strong jaws and river sense; brings down fish and waterfowl cleanly.",
        },
        {
            "name": "Swimming",
            "modifier": 3,
            "attrs": ["attr_dex"],
            "skills": ["survival"],
            "packs": ["silverrush"],
            "blurb": "Fast in shallows and eddies; reads the current before it shifts.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Picks up patrol patterns and border scents before others notice.",
        },
        {
            "name": "Herbal Knowledge",
            "modifier": 3,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "blurb": "Basic herbs and poultices for minor wounds and ailments.",
        },
    ],
    "weaknesses": [
        {
            "name": "Secret Romance",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Love for a Thistlehide wolf; leverage in the wrong paws ends them both.",
        },
        {
            "name": "Reckless at the Border",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking", "hunting", "survival"],
            "blurb": "Stays too long at neutral ground when Mossheart needs him to leave.",
        },
        {
            "name": "Pack Loyalty vs Heart",
            "modifier": -2,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "If Saltmuzzle orders him to report Thistlehide movements, he will fracture.",
        },
    ],
}


KANAMI_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Supernatural Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "packs": ["thistlehide"],
            "blurb": "Moves so silently even the alpha's guard struggles to hear her footsteps.",
        },
        {
            "name": "Audio Mapping",
            "modifier": 3,
            "skills": ["tracking", "survival"],
            "attrs": ["attr_wis"],
            "blurb": "Navigates dense thorny terrain by mapping echoes of wind and birds.",
        },
        {
            "name": "Small Space Survival",
            "modifier": 2,
            "skills": ["survival"],
            "attrs": ["attr_con"],
            "blurb": "Fits into tiny burrows and hollow logs where predators cannot reach.",
        },
    ],
    "weaknesses": [
        {
            "name": "Permanently Tiny",
            "modifier": -3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Lacks weight or muscle to defend herself against an adult wolf.",
        },
        {
            "name": "The Scapegoat",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Blamed for bad luck, sickness, or failed hunts in the territory.",
        },
        {
            "name": "Total Blindness",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["stealth", "tracking", "survival"],
            "check_disadvantage": True,
            "hunt_mult": 0.65,
            "blurb": "Cannot perceive visual tells, light, or facial expressions.",
        },
    ],
}


FIREPAW_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Acute Hearing",
            "modifier": 4,
            "skills": ["tracking", "medicine"],
            "packs": ["thistlehide"],
            "blurb": "Detects footsteps in snow, breathing shifts, and prey in cover by sound alone.",
        },
        {
            "name": "Touch Herblore",
            "modifier": 4,
            "skills": ["herblore"],
            "packs": ["thistlehide"],
            "blurb": "Identifies plants by texture and scent; rarely mis-picks in Thistlehide brush.",
        },
        {
            "name": "Gentle Hands",
            "modifier": 3,
            "skills": ["medicine"],
            "treat_heal_bonus": 1,
            "packs": ["thistlehide"],
            "blurb": "Steady when treating wounds; touch-guided dressings hold clean.",
        },
    ],
    "weaknesses": [
        {
            "name": "Total Blindness",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["medicine", "herblore", "stealth"],
            "check_disadvantage": True,
            "hunt_mult": 0.45,
            "blurb": "Milky blind eyes; cannot hunt by sight or read expressions.",
        },
        {
            "name": "Defensive Temper",
            "modifier": -3,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Snaps when doubted; snarls before she thinks in tense moments.",
        },
        {
            "name": "Refuses Help",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["medicine", "herblore"],
            "blurb": "Won't accept aid on trails or hunts; overwhelmed when plans collapse.",
        },
        {
            "name": "Pride Before Proof",
            "modifier": -2,
            "skills": ["hunting", "survival"],
            "attrs": ["attr_str"],
            "blurb": "Takes reckless risks to prove blindness is not weakness.",
        },
    ],
}


MURKVEIN_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Persuasion",
            "modifier": 2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "packs": ["mistmoor"],
            "blurb": "Honeyed whisper; wolves agree before they realize what they promised.",
        },
        {
            "name": "Poison & Cure Lore",
            "modifier": 4,
            "skills": ["herblore"],
            "attrs": ["attr_wis"],
            "packs": ["mistmoor"],
            "blurb": "Knows every poison and cure in the swamp; rivals the best healers.",
        },
        {
            "name": "Intimidation",
            "modifier": 3,
            "skills": ["intimidation"],
            "attrs": ["attr_cha"],
            "packs": ["mistmoor"],
            "blurb": "Green eyes and boneless grace; wolves feel the Maw staring back.",
        },
    ],
    "weaknesses": [
        {
            "name": "Old Age",
            "modifier": -4,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Brittle bones and rattling lungs; cannot fight long; a hard fall could break her.",
        },
        {
            "name": "No Tail",
            "modifier": -2,
            "attrs": ["attr_dex"],
            "skills": ["survival"],
            "packs": ["mistmoor"],
            "check_disadvantage": True,
            "hunt_mult": 0.9,
            "blurb": "Lost her tail to rot-lung necrosis; struggles to balance in water.",
        },
        {
            "name": "Paranoid about Mirewort",
            "modifier": -1,
            "attrs": ["attr_wis"],
            "exclude_skills": ["herblore", "intimidation"],
            "blurb": "Distrusts the healer's closeness to the Maw; refuses aid and questions every cure.",
        },
    ],
}


DUSK_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Intimidation",
            "modifier": 4,
            "skills": ["intimidation"],
            "attrs": ["attr_cha"],
            "packs": ["mistmoor"],
            "blurb": "Rasping whisper and scarred throat; sounds like a ghost.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Moves through the swamp like smoke.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_int"],
            "blurb": "Follows trails through standing water.",
        },
    ],
    "weaknesses": [
        {
            "name": "Rasping Voice",
            "modifier": -2,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blocks_howl": True,
            "blurb": "Cannot howl or call for help; silent in emergencies.",
        },
        {
            "name": "Loyal to a Fault",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking", "stealth", "intimidation"],
            "blurb": "Cannot refuse a direct order from his alpha; even into madness or death.",
        },
        {
            "name": "Guilt",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["intimidation"],
            "blurb": "Remembers every wolf he executed; hesitates when confronted with their memory.",
        },
    ],
}


SOOT_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Herblore",
            "modifier": 4,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "packs": ["mistmoor"],
            "blurb": "Learning quickly; knows basics of rot-lung and wound treatment.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Strange vision catches details others miss; mist light, insect movement.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Small and quiet; slips through reeds without a sound.",
        },
    ],
    "weaknesses": [
        {
            "name": "Clumsy",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "exclude_skills": ["stealth"],
            "blurb": "Trips constantly; cannot be trusted with sharp objects.",
        },
        {
            "name": "Insecure",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Needs constant reassurance; freezes if scolded harshly.",
        },
        {
            "name": "Overly Attached to Mirewort",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["herblore", "medicine"],
            "blurb": "Would follow him into danger without question.",
        },
    ],
}


ROTTEDDUST_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Herblore",
            "modifier": 4,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "packs": ["mistmoor"],
            "blurb": "Knows every poisonous and medicinal fungus in the swamp.",
        },
        {
            "name": "Medicine",
            "modifier": 3,
            "skills": ["medicine"],
            "attrs": ["attr_wis"],
            "blurb": "Skilled at treating rot-lung and infection.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Hides in plain sight by blending with rotting logs.",
        },
    ],
    "weaknesses": [
        {
            "name": "Morbid",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["herblore", "medicine"],
            "blurb": "Unsettles patients; wolves avoid eir den unless desperate.",
        },
        {
            "name": "Tremor",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "exclude_skills": ["stealth"],
            "blurb": "Shaking paw makes fine stitching difficult.",
        },
        {
            "name": "Obsessive",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["herblore", "medicine"],
            "blurb": "Will abandon a patient to collect a rare mushroom.",
        },
    ],
}


SLUDGE_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "packs": ["mistmoor"],
            "blurb": "Nearly invisible in shallow water; holds still half a day, strikes when prey forgets he exists.",
        },
        {
            "name": "Hunting",
            "modifier": 3,
            "skills": ["hunting"],
            "attrs": ["attr_str"],
            "blurb": "Ambush specialist; single neck-snap from below; one lunge, one crack, one meal.",
        },
        {
            "name": "Survival",
            "modifier": 3,
            "skills": ["survival"],
            "attrs": ["attr_wis"],
            "blurb": "Knows every sinkhole and safe route; pack follows him when fog rolls in.",
        },
    ],
    "weaknesses": [
        {
            "name": "Twisted Leg",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "exclude_skills": ["stealth"],
            "blurb": "Cannot chase fleeing prey; if the ambush fails, the hunt fails.",
        },
        {
            "name": "Missing Toes",
            "modifier": -2,
            "attrs": ["attr_dex"],
            "exclude_skills": ["stealth"],
            "blurb": "Two toes gone on left forepaw; slips on wet banks at the worst moment.",
        },
        {
            "name": "Superstitious",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["survival", "stealth"],
            "hunt_abort_chance": 0.22,
            "blurb": "Aborts hunts on bad omens; crow flying left, ripple without wind, three frog croaks.",
        },
    ],
}


GRISTLE_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Hunting",
            "modifier": 3,
            "skills": ["hunting"],
            "attrs": ["attr_str"],
            "packs": ["mistmoor"],
            "blurb": "Brutal and direct; takes down prey twice his size by refusing to let go.",
        },
        {
            "name": "Intimidation",
            "modifier": 2,
            "skills": ["intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Scars and stench make smaller prey freeze in fear.",
        },
        {
            "name": "Endurance",
            "modifier": 4,
            "skills": ["survival"],
            "attrs": ["attr_con"],
            "blurb": "Can run a quarter-moon on half a vole; refuses to quit.",
        },
    ],
    "weaknesses": [
        {
            "name": "Loud",
            "modifier": -2,
            "attrs": ["attr_dex"],
            "skills": ["stealth", "hunting"],
            "hunt_mult": 0.85,
            "blurb": "Scares prey away; other hunters hate hunting with him.",
        },
        {
            "name": "Missing Claws",
            "modifier": -2,
            "attrs": ["attr_dex"],
            "exclude_skills": ["hunting", "intimidation"],
            "blurb": "Reduced grip on slippery banks; sometimes loses footing.",
        },
        {
            "name": "Ashamed of His Past",
            "modifier": -3,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Flies into rage if anyone mentions Greyspire.",
        },
    ],
}


CROAKER_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "packs": ["mistmoor"],
            "blurb": "Hides in reeds; not seen from a frog-length away.",
        },
        {
            "name": "Hunting",
            "modifier": 3,
            "skills": ["hunting"],
            "attrs": ["attr_dex"],
            "blurb": "Expert at catching small fast prey with precise paw-strikes.",
        },
        {
            "name": "Mimicry",
            "modifier": 3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Imitates frog calls, bird chirps, and insect buzzes to lure prey.",
        },
    ],
    "weaknesses": [
        {
            "name": "Tiny",
            "modifier": -4,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Cannot fight; one good bite from a rival would kill him.",
        },
        {
            "name": "Easily Startled",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["stealth", "hunting"],
            "blurb": "Panics at loud noises; cracking sticks, raised voices, thunderpath monsters.",
        },
        {
            "name": "Obsessive",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["hunting"],
            "blurb": "Spends all day on one frog; loses track of time and pack.",
        },
    ],
}


GASP_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Prophecy",
            "modifier": 4,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "packs": ["mistmoor"],
            "blurb": "Cryptic predictions often come true; no one knows how.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Hears things from impossible distances; including the Belly-Rip's whispers.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Moves like a ghost; often appears without warning.",
        },
    ],
    "weaknesses": [
        {
            "name": "Frail",
            "modifier": -4,
            "attrs": ["attr_str"],
            "combat": True,
            "hunt_mult": 0.45,
            "blurb": "Cannot fight, hunt, or run; relies on the pack to feed them.",
        },
        {
            "name": "Unsettling",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Wolves avoid them; they have no allies.",
        },
        {
            "name": "Dissociative",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking", "stealth"],
            "blurb": "Lost in visions; forgets to eat, sleep, or speak for days.",
        },
    ],
}


YARROW_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "packs": ["mistmoor"],
            "blurb": "Surprisingly quiet when he remembers to shut up.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_int"],
            "blurb": "Sharp nose; follows trails through mud and water.",
        },
        {
            "name": "Survival",
            "modifier": 3,
            "skills": ["survival"],
            "attrs": ["attr_wis"],
            "blurb": "Knows which mushrooms are edible and which will kill him.",
        },
    ],
    "weaknesses": [
        {
            "name": "Talks Too Much",
            "modifier": -3,
            "skills": ["stealth", "persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Gives away his position; drives other wolves mad.",
        },
        {
            "name": "Nervous",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking", "survival"],
            "blurb": "Prone to panic attacks, especially during storms.",
        },
        {
            "name": "Desperate for Approval",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["stealth"],
            "blurb": "Can be manipulated by any wolf who offers praise.",
        },
    ],
}


HOLLOWSTEM_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Medicine",
            "modifier": 4,
            "skills": ["medicine"],
            "attrs": ["attr_wis"],
            "packs": ["mistmoor"],
            "blurb": "Skilled at treating pup illnesses; rot-lung, fever, parasites.",
        },
        {
            "name": "Persuasion",
            "modifier": 3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Can calm a screaming pup with a whisper.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Moves quietly through the swamp; often finds lost pups first.",
        },
    ],
    "weaknesses": [
        {
            "name": "Non-Fighter",
            "modifier": -4,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Cannot fight; one blow would kill her.",
        },
        {
            "name": "Too Soft",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["medicine", "persuasion"],
            "blurb": "Hesitates to discipline pups; leads to spoiled brats.",
        },
        {
            "name": "Lonely",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Misses having her own litter; might make questionable decisions to keep a pup close.",
        },
    ],
}


MUDPUP_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Stealth",
            "modifier": 4,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "packs": ["mistmoor"],
            "blurb": "Disappears into the swamp like smoke.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Hears things other wolves miss; including the Belly-Rip's whispers.",
        },
    ],
    "weaknesses": [
        {
            "name": "Unsettling",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Other pups avoid him; creepy without meaning to be.",
        },
        {
            "name": "Physically Weak",
            "modifier": -2,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Not built for fighting or hunting; digging is his only strength.",
        },
        {
            "name": "Fixated on the Belly-Rip",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["stealth", "tracking"],
            "blurb": "Will wander toward it if not watched; dangerous.",
        },
    ],
}


MOSSPUP_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Herblore",
            "modifier": 2,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "packs": ["mistmoor"],
            "blurb": "Surprisingly good at identifying plants for her age.",
        },
        {
            "name": "Medicine",
            "modifier": 2,
            "skills": ["medicine"],
            "attrs": ["attr_wis"],
            "blurb": "Mimics basic treatments she has watched Mirewort perform.",
        },
    ],
    "weaknesses": [
        {
            "name": "Fragile Health",
            "modifier": -3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Still prone to lung infections; cold weather is dangerous.",
        },
        {
            "name": "Talks Too Much",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Drives away wolves who might otherwise help her.",
        },
        {
            "name": "No Survival Skills",
            "modifier": -2,
            "attrs": ["attr_dex"],
            "exclude_skills": ["herblore", "medicine"],
            "blurb": "Cannot hunt, fight, or swim well.",
        },
    ],
}


REEDWHISPER_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Persuasion",
            "modifier": 3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "packs": ["mistmoor"],
            "blurb": "Gentle voice disarms hostility.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Reads emotions like a tracker reads prints.",
        },
        {
            "name": "Herblore",
            "modifier": 2,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "blurb": "Uses gifts of medicine to sweeten negotiations.",
        },
    ],
    "weaknesses": [
        {
            "name": "Evasive",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Avoids hard questions; packs find her slippery.",
        },
        {
            "name": "Deep Loyalty to Mistmoor",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["persuasion", "herblore"],
            "blurb": "Will lie to protect her pack's secrets.",
        },
        {
            "name": "Hidden Temper",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "When pushed too far, loses control and credibility.",
        },
    ],
}


MUDNOSE_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Survival",
            "modifier": 4,
            "skills": ["survival"],
            "attrs": ["attr_wis"],
            "packs": ["mistmoor"],
            "blurb": "Expert digger and den-builder.",
        },
        {
            "name": "Foraging",
            "modifier": 3,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "blurb": "Knows every edible root and tuber in the swamp.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Hides in plain sight by standing completely still.",
        },
    ],
    "weaknesses": [
        {
            "name": "Slow Runner",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "exclude_skills": ["stealth"],
            "blurb": "Cannot escape a predator; relies on hiding.",
        },
        {
            "name": "Grumpy",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Drives away wolves who might otherwise be allies.",
        },
        {
            "name": "Secretive",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["survival", "stealth"],
            "blurb": "His secrets could be dangerous if revealed.",
        },
    ],
}


PUDDLEBANE_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Foraging",
            "modifier": 3,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "packs": ["mistmoor"],
            "blurb": "Expert in swamp plants; edible roots, medicinal fungi, poisonous berries.",
        },
        {
            "name": "Herblore",
            "modifier": 4,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "blurb": "Identifies any plant by smell alone.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Moves quietly through thick undergrowth.",
        },
    ],
    "weaknesses": [
        {
            "name": "Absent-Minded",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["herblore", "stealth"],
            "blurb": "Forgets pack meetings, patrols, where she left her herb pouch.",
        },
        {
            "name": "Cheerful",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Other wolves find her unsettling; does not fit Mistmoor's grim mood.",
        },
        {
            "name": "Physically Weak",
            "modifier": -3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Cannot fight; will not fight; will offer a mushroom instead.",
        },
    ],
}


FINNPELT_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Fighting",
            "modifier": 4,
            "attrs": ["attr_str"],
            "combat": True,
            "packs": ["thistlehide"],
            "blurb": "Expert weight and crushing jaw pressure; devastating counter-strikes.",
        },
        {
            "name": "Intimidation",
            "modifier": 3,
            "skills": ["intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Overwhelming presence; commands submission with a glare.",
        },
        {
            "name": "Endurance",
            "modifier": 3,
            "skills": ["survival"],
            "attrs": ["attr_con"],
            "blurb": "High pain tolerance; patrols for days on minimal sleep.",
        },
        {
            "name": "Armor-Like Coat",
            "modifier": 0,
            "attrs": ["attr_con"],
            "combat": True,
            "damage_reduction": 2,
            "blurb": "River-oiled ash-black fur; thorns and teeth slide off like armor.",
        },
    ],
    "weaknesses": [
        {
            "name": "Low Agility",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "combat": True,
            "blurb": "Heavy and methodical; poor dodger against swift enemies.",
        },
        {
            "name": "Hyper-Vigilance",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["intimidation", "survival"],
            "blurb": "Severe sleep deprivation; constantly scanning for threats.",
        },
        {
            "name": "Rigid Thinking",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["intimidation"],
            "blurb": "Struggles with chaotic supernatural events or abstract problems.",
        },
    ],
}


SKYE_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Fighting",
            "modifier": 4,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Brutal, experienced; fights dirty.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_int"],
            "blurb": "Follows scent through fire-scarred land.",
        },
        {
            "name": "Intimidation",
            "modifier": 3,
            "skills": ["intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Mismatched eyes and hidden scars make her terrifying.",
        },
    ],
    "weaknesses": [
        {
            "name": "Gets Distracted When Hunting",
            "modifier": -2,
            "skills": ["hunting", "tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Mind wanders to the past during a chase.",
        },
        {
            "name": "Haunted by Loss",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["intimidation"],
            "blurb": "Still grieves her pups; freezes if she sees a pup in danger.",
        },
        {
            "name": "Trust Issues",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["intimidation"],
            "blurb": "Keeps other wolves at a tail-length, even packmates.",
        },
    ],
}


BRACKENPELT_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Hunting",
            "modifier": 3,
            "skills": ["hunting"],
            "attrs": ["attr_str"],
            "packs": ["thistlehide"],
            "blurb": "Reliable on deer and boar; brings down prey cleanly.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Knows southern territory by heart; follows cold trails through bracken and pine.",
        },
        {
            "name": "Border Patrol",
            "modifier": 2,
            "skills": ["survival"],
            "attrs": ["attr_con"],
            "blurb": "Endures long watches; reads wind and thunderpath noise before trouble arrives.",
        },
    ],
    "weaknesses": [
        {
            "name": "Overprotective",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["hunting", "tracking"],
            "blurb": "Cannot stop checking on Sypha; takes dangerous patrols to keep her from the southern edge.",
        },
        {
            "name": "Plainspoken to a Fault",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Offends without meaning to; uncomfortable with healers, elders, and politics.",
        },
        {
            "name": "No Head for Herbs",
            "modifier": -2,
            "attrs": ["attr_int"],
            "exclude_skills": ["hunting", "tracking", "survival"],
            "blurb": "Cannot tell poison root from edible; relies on Cloverfern and Sypha.",
        },
    ],
}


CLOVERFERN_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Foraging",
            "modifier": 4,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "packs": ["thistlehide"],
            "blurb": "Expert knowledge of edible roots, berries, and common medicinals in Thistlehide.",
        },
        {
            "name": "Herblore",
            "modifier": 3,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "blurb": "Identifies useful plants by leaf, scent, and season; stocks the healer's den when Sypha is away.",
        },
        {
            "name": "Plantcraft",
            "modifier": 2,
            "skills": ["medicine"],
            "attrs": ["attr_wis"],
            "blurb": "Prepares poultices, dried stores, and nursery mash.",
        },
    ],
    "weaknesses": [
        {
            "name": "Not a Fighter",
            "modifier": -3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Cannot hold a border or survive a direct attack; freezes if cornered.",
        },
        {
            "name": "Worrier",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["herblore", "medicine"],
            "blurb": "Imagines worst outcomes for Sypha and Brackenpelt; loses sleep during storms and pipeline raids.",
        },
        {
            "name": "Too Trusting",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Assumes good intent; cheated out of herb credit by lazy packmates.",
        },
    ],
}


SYPHA_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Herblore",
            "modifier": 5,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "packs": ["thistlehide"],
            "blurb": "Expert knowledge of medicinal and poisonous plants; identifies any herb by sight, smell, or taste.",
        },
        {
            "name": "Medicine",
            "modifier": 4,
            "skills": ["medicine"],
            "attrs": ["attr_wis"],
            "blurb": "Diagnoses illness, stitches wounds, treats infections; has saved more wolves than she can count.",
        },
        {
            "name": "Poison-craft",
            "modifier": 3,
            "skills": ["herblore"],
            "attrs": ["attr_int"],
            "blurb": "Brews toxins for hunting; thorn coatings and poisoned fresh-kill for large prey.",
        },
    ],
    "weaknesses": [
        {
            "name": "Fear of Reptiles and Insects",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["herblore", "medicine"],
            "blurb": "Freezes at snakes, lizards, or spiders; nearly cost patients when a snake entered her herb den.",
        },
        {
            "name": "Easily Belittled",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["herblore", "medicine"],
            "blurb": "Sensitive to mockery; harsh words shake confidence and make her second-guess treatments.",
        },
        {
            "name": "Yearns for Recognition",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["medicine"],
            "blurb": "Wants to be legendary, not merely competent; takes risks and hoards credit from elders.",
        },
    ],
}


RIVERSHROUD_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Hunting",
            "modifier": 4,
            "skills": ["hunting"],
            "attrs": ["attr_str"],
            "packs": ["thistlehide"],
            "blurb": "Devastating ambush predator; uses weight and crushing bite to bring down large prey solo.",
        },
        {
            "name": "Fighting",
            "modifier": 4,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Immovable in combat; holds the line and absorbs blows meant for others.",
        },
        {
            "name": "Intimidation",
            "modifier": 3,
            "skills": ["intimidation"],
            "attrs": ["attr_cha"],
            "blurb": "Silent towering presence and antlered silhouette make even seasoned warriors hesitate.",
        },
    ],
    "weaknesses": [
        {
            "name": "Mute Vocal Cords",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["intimidation"],
            "blurb": "Cannot speak above a raspy whisper; gestures and rumbles often misunderstood.",
        },
        {
            "name": "Severe Social Anxiety",
            "modifier": -3,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["intimidation"],
            "blurb": "Freezes or withdraws in large gatherings; avoids pack meetings.",
        },
        {
            "name": "Obsessive Protectiveness",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["hunting", "intimidation"],
            "blurb": "Puts herself in lethal danger for Pale'Step or any wolf under her care.",
        },
    ],
}


LUCID_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Hunting",
            "modifier": 4,
            "skills": ["hunting"],
            "attrs": ["attr_dex"],
            "packs": ["thistlehide"],
            "blurb": "Drives prey toward ambush points; prey underestimates his damaged eye.",
        },
        {
            "name": "Tracking",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_int"],
            "blurb": "Excellent nose; can follow a cold trail for a quarter-moon.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Silent through dry leaves; learned sneaking scraps as a hearth-hound.",
        },
    ],
    "weaknesses": [
        {
            "name": "Old Leg Injury",
            "modifier": -3,
            "attrs": ["attr_dex"],
            "exclude_skills": ["stealth"],
            "blurb": "Shattered bone healed poorly; cannot sprint long; limps in cold weather.",
        },
        {
            "name": "Damaged Eye",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["tracking", "hunting"],
            "blurb": "Poor depth perception; struggles to judge distance, especially in low light.",
        },
        {
            "name": "Self-Sacrificing to a Fault",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Gives up food, den space, and safety even when not needed; packmates exploit it.",
        },
    ],
}


ASHBARK_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Hunting",
            "modifier": 3,
            "skills": ["hunting"],
            "attrs": ["attr_str"],
            "packs": ["thistlehide"],
            "blurb": "Average hunter; specializes in deer and boar.",
        },
        {
            "name": "Stealth",
            "modifier": 3,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Moves quietly through burned forest.",
        },
    ],
    "weaknesses": [
        {
            "name": "Guilt-Ridden",
            "modifier": -3,
            "attrs": ["attr_wis"],
            "exclude_skills": ["hunting", "stealth", "tracking"],
            "blurb": "Freezes when he hears Kanami's voice.",
        },
        {
            "name": "Avoidant",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["hunting"],
            "blurb": "Will not confront problems; lets others make decisions.",
        },
        {
            "name": "Superstitious",
            "modifier": -2,
            "attrs": ["attr_wis"],
            "exclude_skills": ["stealth"],
            "blurb": "Still half-believes Kanami is cursed; fear and guilt tangled.",
        },
    ],
}


ELTANIN_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Observant Tracker",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_int", "attr_wis"],
            "blurb": "Quiet border runs; reads scent and sign before others notice.",
        },
        {
            "name": "Bold Hunter",
            "modifier": 3,
            "skills": ["hunting"],
            "attrs": ["attr_str", "attr_dex"],
            "blurb": "Takes calculated risks to feed the den, not reckless bravado.",
        },
        {
            "name": "Protective Vigilance",
            "modifier": 2,
            "skills": ["survival"],
            "attrs": ["attr_wis"],
            "blurb": "Stalks trouble before pups or caretakers know they are missing.",
        },
    ],
    "weaknesses": [
        {
            "name": "Emotionally Reserved",
            "modifier": -2,
            "skills": ["persuasion"],
            "attrs": ["attr_cha"],
            "blurb": "Walls up; wolves mistake silence for coldness.",
        },
        {
            "name": "Twoleg Avoidance",
            "modifier": -2,
            "skills": ["survival", "tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Refuses logging scars and thunder-stick range; border hunts suffer.",
        },
        {
            "name": "Impatient with Liars",
            "modifier": -2,
            "skills": ["persuasion", "intimidation"],
            "attrs": ["attr_cha"],
            "exclude_skills": ["hunting", "tracking"],
            "blurb": "Little patience for laziness or deceit; snaps when trust breaks.",
        },
    ],
}


PALESTEP_CHARACTER_TRAITS = {
    "bonuses": [
        {
            "name": "Evasion",
            "modifier": 4,
            "skills": ["stealth"],
            "attrs": ["attr_dex"],
            "blurb": "Uses her tiny size to slip through brambles, dodge blows, and escape predators.",
        },
        {
            "name": "Perception",
            "modifier": 3,
            "skills": ["tracking"],
            "attrs": ["attr_wis"],
            "blurb": "Detects shifting scents, snapping twigs, or logging trucks before others notice.",
        },
        {
            "name": "Iron Scenting",
            "modifier": 2,
            "skills": ["tracking"],
            "attrs": ["attr_int"],
            "blurb": "Catches the metallic scent of a twoleg leg-hold trap before stepping in.",
        },
    ],
    "weaknesses": [
        {
            "name": "Severe Asthma",
            "modifier": -4,
            "attrs": ["attr_con"],
            "exclude_skills": ["stealth", "survival"],
            "blurb": "Running full speed or heavy smoke triggers severe breathing distress.",
        },
        {
            "name": "Weak Heart",
            "modifier": -3,
            "attrs": ["attr_str"],
            "combat": True,
            "blurb": "Cannot lift heavy objects, pin opponents, or endure prolonged labor.",
        },
        {
            "name": "Low Physical Defense",
            "modifier": -3,
            "attrs": ["attr_con"],
            "combat": True,
            "exclude_skills": ["stealth"],
            "blurb": "If caught or pinned, her fragile body takes massive damage.",
        },
    ],
}


def skill_label_to_key(skill_label: str | None) -> str | None:
    if not skill_label:
        return None
    return LABEL_TO_SKILL.get(skill_label.lower())


def _user_field(user, key: str, default=None):
    if not user:
        return default
    try:
        keys = user.keys() if hasattr(user, "keys") else ()
        if keys and key not in keys:
            return default
        return user[key]
    except (KeyError, TypeError, IndexError):
        return default


def parse_character_traits(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def encode_character_traits(traits: dict) -> str:
    return json.dumps(traits)


def _blank_traits() -> dict:
    return {"bonuses": [], "weaknesses": []}


def ensure_traits_dict(traits: dict | None) -> dict:
    if not traits:
        return _blank_traits()
    out = copy.deepcopy(traits)
    out.setdefault("bonuses", [])
    out.setdefault("weaknesses", [])
    return out


def _earned_traits_for_skill(traits: dict, skill_key: str, *, group: str) -> list[dict]:
    matches: list[dict] = []
    for trait in traits.get(group, []):
        if not trait.get("earned"):
            continue
        skills = trait.get("skills") or []
        if skill_key in skills:
            matches.append(trait)
    return matches


def earned_trait_bonus_total(traits: dict | None, skill_key: str) -> int:
    if not traits:
        return 0
    total = 0
    for trait in _earned_traits_for_skill(traits, skill_key, group="bonuses"):
        total += max(0, int(trait.get("modifier", 0)))
    return total


def earned_trait_setback_total(traits: dict | None, skill_key: str) -> int:
    if not traits:
        return 0
    total = 0
    for trait in _earned_traits_for_skill(traits, skill_key, group="weaknesses"):
        total += abs(min(0, int(trait.get("modifier", 0))))
    return total


def _adjust_skill_trait_experience_step(
    wolf_id: int,
    skill_key: str,
    step: int,
) -> tuple[bool, str]:
    import database as db
    from rpg_rules import MAX_EARNED_TRAIT_BONUS, MAX_EARNED_TRAIT_SETBACK, SKILLS

    if skill_key not in SKILLS:
        return False, "unknown skill."
    attr_keys, label = SKILLS[skill_key]

    wolf = db.get_user_by_id(wolf_id)
    if not wolf:
        return False, "wolf not found."

    traits = ensure_traits_dict(_traits_for_user(wolf))

    if step > 0:
        current = earned_trait_bonus_total(traits, skill_key)
        if current >= MAX_EARNED_TRAIT_BONUS:
            return (
                False,
                f"**{label}** experience is already maxed "
                f"(+{MAX_EARNED_TRAIT_BONUS} from play; stacks with lore traits).",
            )
        earned = _earned_traits_for_skill(traits, skill_key, group="bonuses")
        if earned:
            trait = earned[0]
            trait["modifier"] = int(trait.get("modifier", 0)) + 1
        else:
            traits["bonuses"].append(
                {
                    "name": f"{label} (experience)",
                    "modifier": 1,
                    "skills": [skill_key],
                    "attrs": list(attr_keys),
                    "earned": True,
                    "blurb": "Honed through quests and practice.",
                }
            )
        db.update_user_by_id(wolf_id, character_traits=encode_character_traits(traits))
        new_total = earned_trait_bonus_total(traits, skill_key)
        return (
            True,
            f"**{label}** gained **+{new_total}** experience trait "
            f"(added to lore traits on matching checks).",
        )

    earned_bonus = _earned_traits_for_skill(traits, skill_key, group="bonuses")
    if earned_bonus and int(earned_bonus[0].get("modifier", 0)) > 0:
        trait = earned_bonus[0]
        trait["modifier"] = int(trait["modifier"]) - 1
        if trait["modifier"] <= 0:
            traits["bonuses"] = [
                t
                for t in traits["bonuses"]
                if not (
                    t.get("earned")
                    and skill_key in (t.get("skills") or [])
                    and t.get("name") == trait.get("name")
                )
            ]
        db.update_user_by_id(wolf_id, character_traits=encode_character_traits(traits))
        remaining = earned_trait_bonus_total(traits, skill_key)
        if remaining:
            return True, f"**{label}** experience slipped to **+{remaining}**."
        return True, f"**{label}** hard-won experience faded."

    current_setback = earned_trait_setback_total(traits, skill_key)
    if current_setback >= MAX_EARNED_TRAIT_SETBACK:
        return False, f"**{label}** setbacks are already as bad as they get."
    earned_weak = _earned_traits_for_skill(traits, skill_key, group="weaknesses")
    if earned_weak:
        trait = earned_weak[0]
        trait["modifier"] = int(trait.get("modifier", 0)) - 1
    else:
        traits["weaknesses"].append(
            {
                "name": f"{label} (setback)",
                "modifier": -1,
                "skills": [skill_key],
                "attrs": list(attr_keys),
                "earned": True,
                "blurb": "A rough lesson left its mark.",
            }
        )
    db.update_user_by_id(wolf_id, character_traits=encode_character_traits(traits))
    new_setback = earned_trait_setback_total(traits, skill_key)
    return True, f"**{label}** setback deepened (**−{new_setback}** on matching checks)."


def adjust_skill_trait_experience(
    wolf_id: int,
    skill_key: str,
    delta: int = 1,
) -> tuple[bool, str]:
    """
    Shift earned trait experience for a skill.
    Positive delta adds earned bonus trait steps; negative peels bonus then adds setbacks.
    """
    skill_key = skill_key.strip().lower()
    if delta == 0:
        return False, "no change."
    steps = abs(int(delta))
    sign = 1 if delta > 0 else -1
    last_msg = "no change."
    for _ in range(steps):
        ok, last_msg = _adjust_skill_trait_experience_step(wolf_id, skill_key, sign)
        if not ok:
            return False, last_msg
    return True, last_msg


def spend_xp_trait_bonus(user, skill: str) -> str | None:
    from rpg_rules import MAX_EARNED_TRAIT_BONUS, SKILLS

    if skill not in SKILLS:
        return "unknown skill."
    traits = _traits_for_user(user)
    if earned_trait_bonus_total(traits, skill) >= MAX_EARNED_TRAIT_BONUS:
        return (
            f"**{SKILLS[skill][1]}** experience is already maxed "
            f"(+{MAX_EARNED_TRAIT_BONUS} from play)."
        )
    return None


def get_earned_trait_bonus_for_wolf(wolf_id: int, skill_key: str) -> int:
    import database as db

    wolf = db.get_user_by_id(wolf_id)
    if not wolf:
        return 0
    return earned_trait_bonus_total(_traits_for_user(wolf), skill_key.strip().lower())


def parse_trait_failure_days(raw: str | None) -> dict[str, int]:
    """Legacy per-skill failure day map (int values only)."""
    state = parse_skill_strain_state(raw)
    out: dict[str, int] = {}
    for skill, entry in state.items():
        day = entry.get("last_fail_day")
        if day is not None:
            out[skill] = int(day)
    return out


def parse_skill_strain_state(raw: str | None) -> dict[str, dict]:
    """
    per-skill practice strain before an earned setback lands.
    stored in users.trait_failure_days as json.
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, dict] = {}
    for key, value in data.items():
        skill = str(key).lower()
        if isinstance(value, int):
            out[skill] = {"strain": 0, "last_fail_day": value}
        elif isinstance(value, dict):
            out[skill] = {
                "strain": max(0, int(value.get("strain", 0))),
                "last_fail_day": int(value["last_fail_day"])
                if value.get("last_fail_day") is not None
                else None,
            }
    return out


def encode_skill_strain_state(state: dict[str, dict]) -> str:
    clean: dict[str, dict] = {}
    for skill, entry in state.items():
        if not entry:
            continue
        strain = max(0, int(entry.get("strain", 0)))
        payload: dict = {"strain": strain}
        if entry.get("last_fail_day") is not None:
            payload["last_fail_day"] = int(entry["last_fail_day"])
        if strain or payload.get("last_fail_day") is not None:
            clean[skill] = payload
    return json.dumps(clean)


def format_skill_strain_line(user) -> str | None:
    state = parse_skill_strain_state(_user_field(user, "trait_failure_days", "{}"))
    if not state:
        return None
    from rpg_rules import SKILL_STRAIN_THRESHOLD, SKILLS

    parts: list[str] = []
    for skill, entry in sorted(state.items()):
        strain = int(entry.get("strain", 0))
        if strain <= 0:
            continue
        label = SKILLS.get(skill, ((), skill.title()))[1]
        parts.append(f"**{label}** {strain}/{SKILL_STRAIN_THRESHOLD}")
    if not parts:
        return None
    return "practice strain (rest or success eases): " + " · ".join(parts)


def compute_failure_strain_gain(
    user,
    *,
    outcome: str,
    total: int | None = None,
    dc: int | None = None,
    margin: int | None = None,
) -> tuple[int, str]:
    """How much strain a failed check should add (0 = close call, no lasting dent)."""
    from rpg_rules import SKILL_STRAIN_THRESHOLD

    if outcome == "critical_failure":
        gain = 2
        note = "a botched attempt shakes confidence."
    elif outcome == "failure":
        if margin is None and total is not None and dc is not None:
            margin = int(dc) - int(total)
        miss = max(0, int(margin or 0))
        if miss <= 1:
            return 0, "_close call; nerves only — no lasting dent._"
        if miss <= 4:
            gain = 1
            note = "the miss lingers in muscle memory."
        else:
            gain = 2
            note = "a clear failure; doubt creeps in."
        if dc is not None and int(dc) >= 20 and gain > 0:
            gain += 1
            note = "legendary difficulty; the failure cuts deep."
    else:
        return 0, ""

    exhaustion = int(user["exhaustion"]) if user and "exhaustion" in user.keys() else 0
    if exhaustion >= 3 and gain > 0:
        gain += 1
        note += " Exhaustion made it worse."

    if gain >= SKILL_STRAIN_THRESHOLD:
        note = "confidence collapses under pressure."

    return gain, note


def _apply_strain_gain(
    user,
    *,
    skill_key: str,
    gain: int,
    game_day: int | None,
    flavor: str,
) -> str | None:
    import database as db
    from rpg_rules import SKILL_STRAIN_THRESHOLD

    if gain <= 0:
        return flavor if flavor.startswith("_") else f"_{flavor}_" if flavor else None

    wolf_id = int(user["id"])
    skill_key = skill_key.strip().lower()
    day = int(game_day) if game_day is not None else 0
    state = parse_skill_strain_state(_user_field(user, "trait_failure_days", "{}"))
    entry = state.get(skill_key, {"strain": 0, "last_fail_day": None})
    entry["strain"] = int(entry.get("strain", 0)) + gain
    entry["last_fail_day"] = day
    state[skill_key] = entry

    lines: list[str] = []
    if flavor:
        lines.append(flavor if flavor.startswith("_") else f"_{flavor}_")

    while entry["strain"] >= SKILL_STRAIN_THRESHOLD:
        ok, msg = adjust_skill_trait_experience(wolf_id, skill_key, -1)
        entry["strain"] -= SKILL_STRAIN_THRESHOLD
        if ok:
            lines.append(f"_{msg}_")
        else:
            entry["strain"] = 0
            break

    state[skill_key] = entry
    db.update_user_by_id(wolf_id, trait_failure_days=encode_skill_strain_state(state))

    remaining = int(entry["strain"])
    if remaining > 0:
        lines.append(
            f"_practice strain on this skill: **{remaining}/{SKILL_STRAIN_THRESHOLD}** "
            f"(success or a night's rest eases it)._"
        )
    return "\n".join(lines) if lines else None


def maybe_apply_success_recovery(
    user,
    *,
    skill_key: str | None,
    game_day: int | None = None,
    dc: int | None = None,
) -> str | None:
    """Successful practice shakes off doubt before it becomes a setback."""
    import database as db

    if not user or not skill_key or "id" not in user.keys():
        return None
    skill_key = skill_key.strip().lower()
    state = parse_skill_strain_state(_user_field(user, "trait_failure_days", "{}"))
    entry = state.get(skill_key)
    if not entry or int(entry.get("strain", 0)) <= 0:
        return None

    relief = 2 if dc is not None and int(dc) >= 18 else 1
    new_strain = max(0, int(entry["strain"]) - relief)
    if new_strain <= 0:
        state.pop(skill_key, None)
    else:
        entry["strain"] = new_strain
        state[skill_key] = entry
    db.update_user_by_id(int(user["id"]), trait_failure_days=encode_skill_strain_state(state))

    if new_strain <= 0:
        return "_a clean success; shaken confidence steadies._"
    from rpg_rules import SKILL_STRAIN_THRESHOLD

    return (
        f"_success helps — strain down to **{new_strain}/{SKILL_STRAIN_THRESHOLD}**._"
    )


def decay_skill_strain_on_rollover() -> None:
    """A night's sleep eases practice strain across all skills."""
    import database as db

    with db.get_db() as conn:
        rows = conn.execute(
            "SELECT id, trait_failure_days FROM users WHERE trait_failure_days IS NOT NULL AND trait_failure_days != '{}'"
        ).fetchall()
        for row in rows:
            state = parse_skill_strain_state(row["trait_failure_days"])
            if not state:
                continue
            changed = False
            for skill in list(state.keys()):
                entry = state[skill]
                strain = int(entry.get("strain", 0))
                if strain <= 0:
                    if not entry.get("last_fail_day"):
                        state.pop(skill, None)
                    continue
                entry["strain"] = strain - 1
                changed = True
                if entry["strain"] <= 0 and not entry.get("last_fail_day"):
                    state.pop(skill, None)
            if changed:
                conn.execute(
                    "UPDATE users SET trait_failure_days = ? WHERE id = ?",
                    (encode_skill_strain_state(state), row["id"]),
                )


def maybe_apply_failure_setback(
    user,
    *,
    skill_key: str | None,
    outcome: str,
    game_day: int | None = None,
    total: int | None = None,
    dc: int | None = None,
    margin: int | None = None,
) -> str | None:
    """
    Failed skill checks build **practice strain** before peeling earned traits.
    Close misses (1 point under DC) only rattle nerves. Nat 1 / big misses build strain faster.
    """
    if not user or not skill_key:
        return None
    if outcome not in ("failure", "critical_failure"):
        return None
    if "id" not in user.keys():
        return None

    gain, flavor = compute_failure_strain_gain(
        user,
        outcome=outcome,
        total=total,
        dc=dc,
        margin=margin,
    )
    return _apply_strain_gain(
        user,
        skill_key=skill_key,
        gain=gain,
        game_day=game_day,
        flavor=flavor,
    )


def _user_pack(user) -> str | None:
    return _user_field(user, "great_pack")


def _traits_for_user(user) -> dict | None:
    return parse_character_traits(_user_field(user, "character_traits"))


def _pack_ok(trait: dict, pack: str | None) -> bool:
    packs = trait.get("packs")
    if not packs:
        return True
    return bool(pack and pack in packs)


def _trait_matches_check(
    trait: dict,
    attr_keys: tuple[str, ...],
    skill_key: str | None,
    pack: str | None,
) -> bool:
    if trait.get("combat"):
        return False
    if not _pack_ok(trait, pack):
        return False
    if skill_key and skill_key in (trait.get("exclude_skills") or []):
        return False
    skills = trait.get("skills") or []
    attrs = trait.get("attrs") or []
    skill_hit = bool(skill_key and skill_key in skills)
    attr_hit = bool(attrs and set(attrs) & set(attr_keys))
    if skills and attrs:
        return skill_hit or attr_hit
    if skills:
        return skill_hit
    if attrs:
        return attr_hit
    return False


def trait_check_adjustments(
    user,
    attr_keys: tuple[str, ...],
    *,
    skill_key: str | None = None,
    skill_label: str | None = None,
) -> tuple[int, list[str]]:
    """Return (flat modifier, names of traits that applied)."""
    traits = _traits_for_user(user)
    if not traits:
        return 0, []

    resolved_skill = skill_key or skill_label_to_key(skill_label)
    pack = _user_pack(user)
    total = 0
    applied: list[str] = []
    for group in ("bonuses", "weaknesses"):
        for trait in traits.get(group, []):
            if not _trait_matches_check(trait, attr_keys, resolved_skill, pack):
                continue
            mod = int(trait.get("modifier", 0))
            total += mod
            applied.append(trait["name"])
    return total, applied


def trait_check_disadvantage(
    user,
    attr_keys: tuple[str, ...],
    *,
    skill_key: str | None = None,
    skill_label: str | None = None,
) -> bool:
    """True when a matching weakness imposes disadvantage on this check."""
    traits = _traits_for_user(user)
    if not traits:
        return False
    resolved_skill = skill_key or skill_label_to_key(skill_label)
    pack = _user_pack(user)
    for trait in traits.get("weaknesses", []):
        if not trait.get("check_disadvantage"):
            continue
        if _trait_matches_check(trait, attr_keys, resolved_skill, pack):
            return True
    return False


def trait_hunt_multiplier(user) -> tuple[float, str]:
    """worst hunt multiplier from character-trait weaknesses."""
    traits = _traits_for_user(user)
    if not traits:
        return 1.0, ""
    pack = _user_pack(user)
    mult = 1.0
    label = ""
    for trait in traits.get("weaknesses", []):
        raw = trait.get("hunt_mult")
        if raw is None:
            continue
        if not _pack_ok(trait, pack):
            continue
        m = float(raw)
        if m < mult:
            mult = m
            label = trait["name"]
    if mult >= 1.0:
        return 1.0, ""
    pct = int((1 - mult) * 100)
    return mult, f"{label}; **−{pct}%** hunt bones."


def trait_combat_modifier(user) -> int:
    """flat attack-roll modifier from character traits (e.g. physically frail)."""
    traits = _traits_for_user(user)
    if not traits:
        return 0
    pack = _user_pack(user)
    total = 0
    for trait in traits.get("weaknesses", []):
        if not trait.get("combat"):
            continue
        if not _pack_ok(trait, pack):
            continue
        attrs = trait.get("attrs") or []
        if attrs and {"attr_str", "attr_dex", "attr_con"} & set(attrs):
            total += int(trait.get("modifier", 0))
    for trait in traits.get("bonuses", []):
        if not trait.get("combat"):
            continue
        if _pack_ok(trait, pack):
            total += int(trait.get("modifier", 0))
    return total


def _trait_blurb_for_display(user, trait: dict) -> str:
    """live canonical blurb when on file, then pronoun adaptation."""
    from engine.pronouns import adapt_text_for_user

    blurb = trait.get("blurb", "") or ""
    canon = canonical_traits_for_name(_user_field(user, "wolf_name") or "")
    if canon:
        for section in ("bonuses", "weaknesses"):
            for canon_trait in canon.get(section, []):
                if canon_trait.get("name") == trait.get("name") and canon_trait.get("blurb"):
                    blurb = canon_trait["blurb"]
                    break
    if not blurb:
        return ""
    return adapt_text_for_user(blurb, user)


def format_traits_for_profile(user) -> str | None:
    traits = _traits_for_user(user)
    if not traits:
        return None
    lines: list[str] = []
    for trait in traits.get("bonuses", []):
        mod = int(trait.get("modifier", 0))
        sign = f"+{mod}" if mod >= 0 else str(mod)
        blurb = _trait_blurb_for_display(user, trait)
        line = f"**{trait['name']}** ({sign})"
        if trait.get("earned"):
            line += " _(earned)_"
        if blurb:
            line += f"; {blurb}"
        lines.append(line)
    for trait in traits.get("weaknesses", []):
        mod = int(trait.get("modifier", 0))
        sign = f"+{mod}" if mod >= 0 else str(mod)
        blurb = _trait_blurb_for_display(user, trait)
        line = f"**{trait['name']}** ({sign})"
        if trait.get("earned"):
            line += " _(earned)_"
        if blurb:
            line += f"; {blurb}"
        lines.append(line)
    return "\n".join(lines) if lines else None


CHARACTER_TRAITS_BY_NAME: dict[str, dict] = {
    "mirewort": MIREWORT_CHARACTER_TRAITS,
    "Splinter": SPLINTER_CHARACTER_TRAITS,
    "Moth": MOTH_CHARACTER_TRAITS,
    "Scab": SCAB_CHARACTER_TRAITS,
    "Sleet": SLEET_CHARACTER_TRAITS,
    "Harepup": HAREPUP_CHARACTER_TRAITS,
    "Cinderpup": CINDERPUP_CHARACTER_TRAITS,
    "Rime": RIME_CHARACTER_TRAITS,
    "Talus": TALUS_CHARACTER_TRAITS,
    "Slate": SLATE_CHARACTER_TRAITS,
    "Ironjaw": IRONJAW_CHARACTER_TRAITS,
    "Stonepiercer": STONEPIERCER_CHARACTER_TRAITS,
    "Raven": RAVEN_CHARACTER_TRAITS,
    "Frostburn": FROSTBURN_CHARACTER_TRAITS,
    "Hemlock": HEMLOCK_CHARACTER_TRAITS,
    "Thorn": THORN_CHARACTER_TRAITS,
    "Icefang": ICEFANG_CHARACTER_TRAITS,
    "Grim": GRIM_CHARACTER_TRAITS,
    "Cinder": CINDER_CHARACTER_TRAITS,
    "Pebble": PEBBLE_CHARACTER_TRAITS,
    "Driftpup": DRIFTPUP_CHARACTER_TRAITS,
    "Ripplepup": RIPPLEPUP_CHARACTER_TRAITS,
    "Riptide": RIPTIDE_CHARACTER_TRAITS,
    "Ebb": EBB_CHARACTER_TRAITS,
    "Curlgrip": CURLGRIP_CHARACTER_TRAITS,
    "Churn": CHURN_CHARACTER_TRAITS,
    "Aromis": AROMIS_CHARACTER_TRAITS,
    "Ripple": RIPPLE_CHARACTER_TRAITS,
    "Rift": RIFT_CHARACTER_TRAITS,
    "Saltmuzzle": SALTMUZZLE_CHARACTER_TRAITS,
    "Barkhollow": BARKHOLLOW_CHARACTER_TRAITS,
    "Fernspot": FERNSPOT_CHARACTER_TRAITS,
    "Mossgaze": MOSSGAZE_CHARACTER_TRAITS,
    "Thyme": THYME_CHARACTER_TRAITS,
    "Root": ROOT_CHARACTER_TRAITS,
    "Mossheart": MOSSHEART_CHARACTER_TRAITS,
    "Rivenmaw": RIVENMAW_CHARACTER_TRAITS,
    "Kanami": KANAMI_CHARACTER_TRAITS,
    "Murkvein": MURKVEIN_CHARACTER_TRAITS,
    "Dusk": DUSK_CHARACTER_TRAITS,
    "Soot": SOOT_CHARACTER_TRAITS,
    "Rotteddust": ROTTEDDUST_CHARACTER_TRAITS,
    "Sludge": SLUDGE_CHARACTER_TRAITS,
    "Gristle": GRISTLE_CHARACTER_TRAITS,
    "Croaker": CROAKER_CHARACTER_TRAITS,
    "Gasp": GASP_CHARACTER_TRAITS,
    "Yarrow": YARROW_CHARACTER_TRAITS,
    "Hollowstem": HOLLOWSTEM_CHARACTER_TRAITS,
    "Mudpup": MUDPUP_CHARACTER_TRAITS,
    "Mosspup": MOSSPUP_CHARACTER_TRAITS,
    "Reedwhisper": REEDWHISPER_CHARACTER_TRAITS,
    "Mudnose": MUDNOSE_CHARACTER_TRAITS,
    "Puddlebane": PUDDLEBANE_CHARACTER_TRAITS,
    "Finnpelt": FINNPELT_CHARACTER_TRAITS,
    "Skye": SKYE_CHARACTER_TRAITS,
    "Brackenpelt": BRACKENPELT_CHARACTER_TRAITS,
    "Cloverfern": CLOVERFERN_CHARACTER_TRAITS,
    "Sypha": SYPHA_CHARACTER_TRAITS,
    "RiverShroud": RIVERSHROUD_CHARACTER_TRAITS,
    "Lucid": LUCID_CHARACTER_TRAITS,
    "Ashbark": ASHBARK_CHARACTER_TRAITS,
    "Pale'Step": PALESTEP_CHARACTER_TRAITS,
    "Eltanin": ELTANIN_CHARACTER_TRAITS,
    "Firepaw": FIREPAW_CHARACTER_TRAITS,
}

# Canonical register backstory hooks (role, belief, build) applied with lore/traits.
CHARACTER_REGISTER_DEFAULTS: dict[str, dict[str, str]] = {
    "Gasp": {"wolf_role": "drown_sick"},
    "Eltanin": {"maw_belief": "agnostic"},
    "Kanami": {"size_class": "small"},
    "Pale'Step": {"size_class": "small"},
    "Croaker": {"size_class": "small"},
    # Thistlehide herb & healers (den checkup, forage, treat)
    "Barkhollow": {"wolf_role": "forager"},
    "Cloverfern": {"wolf_role": "forager"},
    "Fernspot": {"wolf_role": "forager"},
    "Mossgaze": {"wolf_role": "forager"},
    "Sypha": {"wolf_role": "medic"},
    "Skye": {"wolf_role": "advisor"},
    "RiverShroud": {"wolf_role": "alpha"},
    "Finnpelt": {"wolf_role": "hunter"},
    "Firepaw": {"wolf_role": "medic_apprentice"},
    "Soot": {"wolf_role": "medic", "maw_belief": "orthodox"},
}


def canonical_traits_for_name(wolf_name: str) -> dict | None:
    for key, traits in CHARACTER_TRAITS_BY_NAME.items():
        if key.lower() == (wolf_name or "").strip().lower():
            return traits
    return None


def canonical_register_defaults_for_name(wolf_name: str) -> dict[str, str] | None:
    for key, defaults in CHARACTER_REGISTER_DEFAULTS.items():
        if key.lower() == (wolf_name or "").strip().lower():
            return defaults
    return None


def trait_blocks_howl(user) -> tuple[bool, str]:
    """true when a weakness forbids pack howls (e.g. scarred throat)."""
    traits = _traits_for_user(user)
    if not traits:
        return False, ""
    pack = _user_pack(user)
    for trait in traits.get("weaknesses", []):
        if not trait.get("blocks_howl"):
            continue
        if _pack_ok(trait, pack):
            return True, trait["name"]
    return False, ""


def roll_trait_hunt_abort(user) -> tuple[bool, str]:
    """roll omen/superstition abort; consumes the hunt attempt when true."""
    import random

    traits = _traits_for_user(user)
    if not traits:
        return False, ""
    pack = _user_pack(user)
    for trait in traits.get("weaknesses", []):
        chance = trait.get("hunt_abort_chance")
        if chance is None:
            continue
        if not _pack_ok(trait, pack):
            continue
        if random.random() < float(chance):
            return True, trait["name"]
    return False, ""


def trait_treat_heal_bonus(healer) -> int:
    """extra hp healed when this wolf treats with herbs."""
    traits = _traits_for_user(healer)
    if not traits:
        return 0
    pack = _user_pack(healer)
    bonus = 0
    for trait in traits.get("bonuses", []):
        if not _pack_ok(trait, pack):
            continue
        bonus = max(bonus, int(trait.get("treat_heal_bonus", 0)))
    return bonus


def trait_clears_infection_on_heal(healer) -> bool:
    traits = _traits_for_user(healer)
    if not traits:
        return False
    pack = _user_pack(healer)
    for trait in traits.get("bonuses", []):
        if trait.get("clears_infection_on_heal") and _pack_ok(trait, pack):
            return True
    return False


def trait_damage_reduction(defender) -> tuple[int, str]:
    """flat damage shaved off incoming hits (best bonus applies)."""
    traits = _traits_for_user(defender)
    if not traits:
        return 0, ""
    pack = _user_pack(defender)
    best = 0
    label = ""
    for trait in traits.get("bonuses", []):
        raw = trait.get("damage_reduction")
        if raw is None:
            continue
        if not _pack_ok(trait, pack):
            continue
        val = int(raw)
        if val > best:
            best = val
            label = trait["name"]
    return best, label
