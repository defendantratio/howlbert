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

# Injury table; roll 1d10 when a wolf is dropped to 0 HP
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

# Severe injury table; a critical hit (outside spine_bite, which has its own
# paralysis odds) risks one of these instead of the base table above.
SEVERE_INJURY_TABLE = (
    "nerve_damage",
    "flail_chest",
    "ruptured_tendon",
    "dislocated_shoulder",
    "crushed_paw",
    "internal_bleeding",
    "lost_eye",
    "ligament_tear",
)

INJURIES = {
    "broken_tooth": {
        "name": "Broken Tooth",
        "effect": "Disadvantage on bite attacks. No cure; permanent.",
        "treatment": "Permanent.",
        "permanent": True,
        "roll": 1,
        "penalties": {"bite_disadvantage": True},
    },
    "torn_claw": {
        "name": "Torn Claw",
        "effect": "−1 to claw damage. Heals in 1 week, or 3 days with horsetail poultice.",
        "treatment": "Horsetail poultice · 1 week natural heal",
        "heal_days": 7,
        "permanent": False,
        "roll": 2,
        "penalties": {"claw_damage_penalty": 1},
        "treat_herbs": ["horsetail"],
        "heal_reduction": 4,
    },
    "deep_gash": {
        "name": "Deep Gash",
        "effect": "Bleeding: lose 1 HP each sunrise until bandaged.",
        "treatment": "Yarrow + cobwebs (or cattail/oak bark) stops bleeding",
        "permanent": False,
        "bleeding": True,
        "roll": 3,
        "penalties": {"hp_loss_per_sunrise": 1, "pain_exhaustion_gain": 1},
        "treat_herbs": ["yarrow", "oak_bark", "cattail", "cobwebs"],
        "bandage_required": True,
    },
    "sprained_leg": {
        "name": "Sprained Leg",
        "effect": "Movement halved. Comfrey + 1 week rest.",
        "treatment": "Comfrey poultice · 1 week rest",
        "heal_days": 7,
        "permanent": False,
        "roll": 4,
        "penalties": {"dex_disadvantage": True, "speed_halved": True},
        "treat_herbs": ["comfrey", "arnica", "tansy"],
        "heal_reduction": 3,
    },
    "fractured_rib": {
        "name": "Fractured Rib",
        "effect": "Disadvantage on Strength checks; cannot hunt.",
        "treatment": "Comfrey poultice · 2 weeks rest",
        "heal_days": 14,
        "permanent": False,
        "blocks_hunt": True,
        "roll": 5,
        "penalties": {"str_disadvantage": True, "pain_exhaustion_gain": 1},
        "treat_herbs": ["comfrey", "bindweed", "broom"],
        "heal_reduction": 5,
    },
    "concussion": {
        "name": "Concussion",
        "effect": "Disadvantage on Intelligence checks; memory loss.",
        "treatment": "Dried skullcap · 1 week sleep",
        "heal_days": 7,
        "permanent": False,
        "roll": 6,
        "penalties": {"int_disadvantage": True},
        "treat_herbs": ["dried_skullcap"],
        "heal_reduction": 2,
    },
    "punctured_paw": {
        "name": "Punctured Paw",
        "effect": "Disadvantage on Dexterity checks involving running or climbing.",
        "treatment": "Heals in 1 week; oak bark binding halves time",
        "heal_days": 7,
        "permanent": False,
        "roll": 7,
        "penalties": {"dex_disadvantage": True, "mobility_penalty": True},
        "treat_herbs": ["oak_bark", "dock", "plantain"],
        "heal_reduction": 4,
    },
    "infected_wound": {
        "name": "Infected Wound",
        "effect": "Each sunrise: Survival/Constitution save or −1 HP and +1 exhaustion.",
        "treatment": "Yarrow or goldenrod poultice",
        "permanent": False,
        "infection": True,
        "roll": 8,
        "penalties": {"hp_loss_per_sunrise": 1, "exhaustion_gain_on_fail": 1},
        "treat_herbs": ["yarrow", "goldenrod", "burdock_root", "wild_garlic"],
        "cure_dc": 14,
    },
    "torn_ear": {
        "name": "Torn Ear / Lost Eye",
        "effect": "Permanent −1 to Perception (Wisdom) checks.",
        "treatment": "Torn ear heals cosmetically; penalty remains. Lost eye: no cure.",
        "permanent": True,
        "roll": 9,
        "penalties": {"perception_penalty": 1},
    },
    "broken_jaw": {
        "name": "Broken Jaw",
        "effect": "Cannot bite or eat solid food. Liquid diet + 3 weeks rest.",
        "treatment": "Broth/milk · comfrey poultice reduces to 2 weeks",
        "heal_days": 21,
        "permanent": False,
        "blocks_bite": True,
        "roll": 10,
        "penalties": {"bite_blocked": True, "pain_exhaustion_gain": 1},
        "treat_herbs": ["comfrey", "bindweed", "slippery_elm"],
        "heal_reduction": 7,
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
        "penalties": {"paralysis": True, "pain_exhaustion_gain": 2},
        "treat_herbs": ["comfrey", "bindweed", "broom"],
        "heal_reduction": 7,
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
        "blocks_all_activity": True,
        "penalties": {"paralysis": True},
    },
    "festering_wound": {
        "name": "Festering Wound",
        "effect": (
            "Deep infection: −1 HP and +1 exhaustion each sunrise without a save. "
            "DC 15 to cure (yarrow or goldenrod tea)."
        ),
        "treatment": "Yarrow tea · goldenrod tea · urgent Medic care",
        "permanent": False,
        "infection": True,
        "festering": True,
        "heal_days": 7,
        "penalties": {"hp_loss_per_sunrise": 1, "exhaustion_gain_per_sunrise": 1},
        "treat_herbs": ["yarrow", "goldenrod", "burdock_root"],
        "cure_dc": 15,
    },
    "scorched_hide": {
        "name": "Scorched Hide",
        "effect": (
            "Burnt skin and fur from fire or boiling liquid: +1 exhaustion each sunrise. "
            "Cannot be treated with herbs; only cobwebs and total rest (7 days)."
        ),
        "treatment": "Cobwebs dressing · 7 days full rest; no herb cure",
        "permanent": False,
        "heat_injury": True,
        "heal_days": 7,
        "penalties": {"exhaustion_gain_per_sunrise": 1, "pain_exhaustion_gain": 1},
        "treat_herbs": ["cobwebs", "common_mallow"],
        "herb_cure": False,
    },
    "bruised_lung": {
        "name": "Bruised Lung",
        "effect": (
            "Develops from a fractured rib left untreated for 2+ sunrises. "
            "Each breath is shallow and laboured: −1 STR and −1 WIS while active. "
            "Surgery only; cannot be cured with herbs."
        ),
        "treatment": "Surgery (set_bone); no herb cure",
        "permanent": False,
        "heal_days": 14,
        "surgery_only": True,
        "penalties": {"str_penalty": 1, "wis_penalty": 1, "hunt_mult": 0.80},
        "treat_herbs": [],
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
        "penalties": {"attack_disadvantage": True, "perception_penalty": 2},
        "treat_herbs": ["celandine", "feverfew", "witch_hazel"],
    },
    "blood_loss": {
        "name": "Blood Loss",
        "effect": (
            "Wolf ended a fight at ≤2 HP: severe haemorrhage reduces blood volume. "
            "−1 max HP until 3 full rests have passed. Clears automatically."
        ),
        "treatment": "3 full rests; clears automatically",
        "permanent": False,
        "blood_loss": True,
        "heal_days": 3,
        "penalties": {"max_hp_penalty": 1},
        "auto_clear": True,
    },
    "snake_venom": {
        "name": "Snake Venom",
        "effect": (
            "venom courses through the body; +1 pain exhaustion and -1 HP each sunrise. "
            "dex -4; con save DC 14 each sunrise or +1 exhaustion. fades after ~5 days if survived."
        ),
        "treatment": "twinflower poultice may slow progression; feverfew reduces fever. no guaranteed cure.",
        "permanent": False,
        "heal_days": 5,
        "snake_venom": True,
        "penalties": {"dex_penalty": 4, "hp_loss_per_sunrise": 1, "pain_exhaustion_gain": 1},
        "treat_herbs": ["blackberry", "snakeroot", "sticklewort", "adders_tongue", "feverfew"],
        "cure_dc": 14,
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
        "penalties": {"dex_penalty": 1, "mood_loss_per_sunrise": 6},
        "treat_herbs": ["dock", "burdock_root", "blackberry", "jewelweed"],
    },
    "lost_eye": {
        "name": "Lost Eye",
        "effect": "Permanent −2 to Perception; disadvantage on ranged attacks.",
        "treatment": "Permanent.",
        "permanent": True,
        "heal_days": None,
        "penalties": {"perception_penalty": 2, "ranged_disadvantage": True},
    },
    "nerve_damage": {
        "name": "Dead-Limb",
        "effect": "Limb partially paralyzed; −2 Dex; cannot use that limb fully; permanent.",
        "treatment": "No cure; can compensate with training.",
        "permanent": True,
        "heal_days": None,
        "penalties": {"dex_penalty": 2},
    },
    "flail_chest": {
        "name": "Caved-Chest",
        "effect": "Multiple ribs broken; breathing laboured; −1 Con; −20% hunt; risk of lung puncture.",
        "treatment": "Surgery only; 6 weeks rest; comfrey poultice for pain.",
        "heal_days": 42,
        "permanent": False,
        "blocks_hunt": True,
        "surgery_required": True,
        "painful": True,
        "penalties": {"con_penalty": 1, "hunt_mult": 0.80, "pain_exhaustion_gain": 2},
        "treat_herbs": ["comfrey", "willow_bark"],
    },
    "heatstroke": {
        "name": "Heatstroke (Sun-Sick)",
        "effect": "Exhaustion; +1 exhaustion; −4 mood; CON save each sunrise or +1 exhaustion.",
        "treatment": "Cool water; rest; feverfew; can be fatal if untreated.",
        "heal_days": 3,
        "permanent": False,
        "heatstroke": True,
        "penalties": {"exhaustion_gain_per_sunrise": 1, "mood_loss_per_sunrise": 4},
        "treat_herbs": ["feverfew", "watermint", "willow_bark"],
        "cure_dc": 12,
    },
    "hypothermia": {
        "name": "Hypothermia (Chill-Bite)",
        "effect": "Shivering; +1 exhaustion; −2 Dex; risk of death in cold.",
        "treatment": "Warmth; honey; rest; avoid extreme cold.",
        "heal_days": 3,
        "permanent": False,
        "hypothermia": True,
        "penalties": {"dex_penalty": 2, "exhaustion_gain_per_sunrise": 1},
        "treat_herbs": ["honey", "pine_bark"],
    },
    "smoke_inhalation": {
        "name": "Smoke-Lung",
        "effect": "Coughing; −1 Con; −10% hunt; risk of pneumonia.",
        "treatment": "Mullein or lungwort tea; rest; avoid smoke.",
        "heal_days": 7,
        "permanent": False,
        "smoke_injury": True,
        "penalties": {"con_penalty": 1, "hunt_mult": 0.90},
        "treat_herbs": ["mullein", "lungwort", "pine_needle"],
        "heal_reduction": 3,
    },
    "ruptured_tendon": {
        "name": "Snapped Sinew",
        "effect": "Cannot put weight on leg; −30% hunt; disadvantage on Dex; +1 pain exhaustion.",
        "treatment": "Surgery only; long healing (6 weeks); no herb cure.",
        "heal_days": 42,
        "permanent": False,
        "surgery_only": True,
        "painful": True,
        "penalties": {"dex_disadvantage": True, "hunt_mult": 0.70, "pain_exhaustion_gain": 1},
        "treat_herbs": [],
    },
    "dislocated_shoulder": {
        "name": "Wrenched Joint",
        "effect": "Arm useless; disadvantage on Strength & Dexterity; −20% hunt; +1 pain exhaustion.",
        "treatment": "Pop back in (medicine DC 15); then rest 1-2 weeks; willow bark for pain.",
        "heal_days": 10,
        "permanent": False,
        "painful": True,
        "penalties": {"str_disadvantage": True, "dex_disadvantage": True, "hunt_mult": 0.80, "pain_exhaustion_gain": 1},
        "treat_herbs": ["willow_bark", "comfrey", "arnica"],
        "heal_reduction": 3,
        "cure_dc": 15,
    },
    "crushed_paw": {
        "name": "Mangled Paw",
        "effect": "Multiple fractures; cannot walk; −50% hunt; +2 pain exhaustion; infection risk.",
        "treatment": "Comfrey poultice + splint; 3 weeks rest; dock leaf for swelling.",
        "heal_days": 21,
        "permanent": False,
        "painful": True,
        "penalties": {"dex_penalty": 4, "hunt_mult": 0.50, "pain_exhaustion_gain": 2},
        "treat_herbs": ["comfrey", "dock", "plantain", "bindweed"],
        "heal_reduction": 7,
    },
    "internal_bleeding": {
        "name": "Blood-Within",
        "effect": "−1 HP per sunrise; risk of shock; cannot be bandaged externally.",
        "treatment": "Shepherd's purse + yarrow tea; requires medicine check DC 15 to stop; otherwise fatal.",
        "heal_days": 5,
        "permanent": False,
        "penalties": {"hp_loss_per_sunrise": 1, "pain_exhaustion_gain": 1},
        "treat_herbs": ["shepherds_purse", "yarrow", "horsetail"],
        "cure_dc": 15,
    },
    "abscess": {
        "name": "Pus-Pocket",
        "effect": "Swollen, painful lump; −4 mood; −1 HP if untreated; bursts after 3 days.",
        "treatment": "Hot compress + burdock root; lance with stick (surgery).",
        "heal_days": 5,
        "permanent": False,
        "infection": True,
        "penalties": {"mood_loss_per_sunrise": 4, "hp_loss_per_sunrise": 1},
        "treat_herbs": ["burdock_root", "dock", "wild_garlic"],
        "heal_reduction": 2,
        "surgery_optional": True,
    },
    "muscle_strain": {
        "name": "Pulled Sinew",
        "effect": "Reduced speed; −10% hunt; disadvantage on Strength checks.",
        "treatment": "Rest 3 days; comfrey poultice reduces to 1 day.",
        "heal_days": 3,
        "permanent": False,
        "penalties": {"str_disadvantage": True, "hunt_mult": 0.90},
        "treat_herbs": ["comfrey", "arnica", "meadowsweet"],
        "heal_reduction": 2,
    },
    "ligament_tear": {
        "name": "Torn Gristle",
        "effect": "Joint unstable; −15% hunt; pain on movement; +1 pain exhaustion.",
        "treatment": "Surgery needed; long recovery (4 weeks); no simple herb cure.",
        "heal_days": 28,
        "permanent": False,
        "surgery_only": True,
        "painful": True,
        "penalties": {"hunt_mult": 0.85, "pain_exhaustion_gain": 1},
        "treat_herbs": [],
    },
    "splinter": {
        "name": "Thorn-Stuck",
        "effect": "Local pain; risk of infection; −1 Dex in that paw.",
        "treatment": "Remove with stick (survival/medicine DC 10); then dock leaf.",
        "heal_days": 2,
        "permanent": False,
        "penalties": {"dex_penalty": 1},
        "treat_herbs": ["dock", "plantain"],
        "cure_dc": 10,
    },
}

from engine.diseases import COUGH_STAGES

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
    "low": "Unity 1 to 2: −10% hunt bones.",
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
