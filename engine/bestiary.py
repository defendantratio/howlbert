"""Predators, hearth-hounds, clan cats, and hazard reference for combat encounters."""

from __future__ import annotations

from engine.character import compute_max_hp, format_max_hp_breakdown

# --- Combat NPC stat blocks ---

def _hp(attrs: dict) -> int:
    return compute_max_hp(attrs["attr_str"], attrs["attr_con"])


def npc_hp(template: dict) -> int:
    return _hp(template["attrs"])


BESTIARY_NPCS: dict[str, dict] = {
    "coyote": {
        "name": "coyote",
        "category": "predators",
        "attrs": {
            "attr_str": 4,
            "attr_dex": 7,
            "attr_con": 6,
            "attr_int": 4,
            "attr_cha": 3,
            "attr_wis": 5,
        },
        "proficiencies": ["stealth"],
        "attack": {
            "name": "Bite",
            "type": "bite",
            "die": 4,
            "flat_damage": 0,
            "hit_bonus": 0,
            "skill": None,
        },
        "behavior": "Flees if outnumbered; targets lone pups or injured wolves.",
    },
    "cougar": {
        "name": "Cougar (Mountain Lion)",
        "category": "predators",
        "attrs": {
            "attr_str": 8,
            "attr_dex": 8,
            "attr_con": 7,
            "attr_int": 5,
            "attr_cha": 4,
            "attr_wis": 6,
        },
        "proficiencies": ["stealth", "hunting"],
        "attack": {
            "name": "Bite",
            "type": "bite",
            "die": 8,
            "flat_damage": 2,
            "hit_bonus": 0,
            "skill": "hunting",
        },
        "behavior": "Attacks from above or at dusk. Stealth/Hunting +2.",
    },
    "black_bear": {
        "name": "Black Bear",
        "category": "predators",
        "attrs": {
            "attr_str": 9,
            "attr_dex": 4,
            "attr_con": 8,
            "attr_int": 4,
            "attr_cha": 3,
            "attr_wis": 5,
        },
        "proficiencies": ["survival"],
        "attack": {
            "name": "Claw",
            "type": "claw",
            "die": 6,
            "flat_damage": 2,
            "hit_bonus": 0,
            "skill": None,
        },
        "behavior": "Avoids wolves unless cubs are threatened or starving.",
    },
    "grizzly_bear": {
        "name": "Grizzly Bear",
        "category": "predators",
        "attrs": {
            "attr_str": 10,
            "attr_dex": 3,
            "attr_con": 8,
            "attr_int": 4,
            "attr_cha": 2,
            "attr_wis": 5,
        },
        "proficiencies": ["survival", "intimidation"],
        "attack": {
            "name": "Bite",
            "type": "bite",
            "die": 10,
            "flat_damage": 3,
            "hit_bonus": 0,
            "skill": "hunting",
        },
        "behavior": "Legendary encounter (DC 25 to scare away); avoid at all costs.",
    },
    "wolverine": {
        "name": "Wolverine",
        "category": "predators",
        "attrs": {
            "attr_str": 6,
            "attr_dex": 6,
            "attr_con": 8,
            "attr_int": 4,
            "attr_cha": 5,
            "attr_wis": 5,
        },
        "proficiencies": ["intimidation"],
        "attack": {
            "name": "Bite",
            "type": "bite",
            "die": 4,
            "flat_damage": 1,
            "hit_bonus": 0,
            "skill": None,
            "on_hit": "Lingering bleed (1 HP/round for 3 rounds).",
        },
        "behavior": "Fears nothing; often fights to the death.",
    },
    "large_prey": {
        "name": "Cornered Deer",
        "category": "predators",
        "attrs": {
            "attr_str": 4,
            "attr_dex": 7,
            "attr_con": 5,
            "attr_int": 2,
            "attr_cha": 3,
            "attr_wis": 4,
        },
        "proficiencies": [],
        "attack": {
            "name": "Hoof Kick",
            "type": "kick",
            "attr": "str",
            "die": 4,
            "flat_damage": 0,
            "hit_bonus": -1,
            "skill": None,
            "on_hit": "Wild thrashing; ribs may crack.",
        },
        "behavior": "Panicked prey; no bite or claws, only desperate kicks and charges.",
    },
    "dog_feral": {
        "name": "Feral Hearth-hound",
        "category": "dogs",
        "attrs": {
            "attr_str": 6,
            "attr_dex": 5,
            "attr_con": 3,
            "attr_int": 2,
            "attr_cha": 4,
            "attr_wis": 3,
        },
        "proficiencies": [],
        "attack": {
            "name": "Bite",
            "type": "bite",
            "die": 4,
            "flat_damage": 0,
            "hit_bonus": 2,
            "skill": None,
        },
        "behavior": "Fights to eat; cowardly if outnumbered.",
    },
    "dog_guard": {
        "name": "Guard Hearth-hound",
        "category": "dogs",
        "attrs": {
            "attr_str": 7,
            "attr_dex": 5,
            "attr_con": 5,
            "attr_int": 3,
            "attr_cha": 5,
            "attr_wis": 4,
        },
        "proficiencies": ["intimidation", "tracking"],
        "attack": {
            "name": "Bite",
            "type": "bite",
            "die": 6,
            "flat_damage": 0,
            "hit_bonus": 0,
            "skill": "hunting",
        },
        "behavior": "Often deployed with other hearth-hounds.",
    },
    "dog_hunting": {
        "name": "Hunting Hearth-hound",
        "category": "dogs",
        "attrs": {
            "attr_str": 5,
            "attr_dex": 7,
            "attr_con": 8,
            "attr_int": 3,
            "attr_cha": 4,
            "attr_wis": 4,
        },
        "proficiencies": ["tracking", "survival"],
        "attack": {
            "name": "Bite",
            "type": "bite",
            "die": 4,
            "flat_damage": 0,
            "hit_bonus": 0,
            "skill": None,
        },
        "behavior": "Won't fight long; chases and bays to alert humans.",
    },
    "dog_fighting": {
        "name": "Fighting Hearth-hound",
        "category": "dogs",
        "attrs": {
            "attr_str": 8,
            "attr_dex": 6,
            "attr_con": 4,
            "attr_int": 2,
            "attr_cha": 3,
            "attr_wis": 3,
        },
        "proficiencies": ["hunting"],
        "attack": {
            "name": "Bite",
            "type": "bite",
            "die": 8,
            "flat_damage": 0,
            "hit_bonus": 2,
            "skill": "hunting",
            "on_hit": "Grapple; held in jaws.",
        },
        "behavior": "Fights to the death; avoid entirely.",
    },
    # --- Clan cats (Warrior Cats-style rivals) ---
    "clan_warrior": {
        "name": "Clan Warrior",
        "category": "cats",
        "attrs": {
            "attr_str": 5,
            "attr_dex": 8,
            "attr_con": 6,
            "attr_int": 5,
            "attr_cha": 5,
            "attr_wis": 6,
        },
        "proficiencies": ["stealth", "hunting"],
        "attack": {
            "name": "Claw Swipe",
            "type": "claw",
            "die": 6,
            "flat_damage": 0,
            "hit_bonus": 1,
            "skill": "hunting",
        },
        "behavior": "Territory patrol; fast, precise, fights in bursts then retreats to cover.",
    },
    "clan_deputy": {
        "name": "Clan Deputy",
        "category": "cats",
        "attrs": {
            "attr_str": 7,
            "attr_dex": 8,
            "attr_con": 7,
            "attr_int": 6,
            "attr_cha": 6,
            "attr_wis": 7,
        },
        "proficiencies": ["stealth", "hunting", "intimidation"],
        "attack": {
            "name": "Raking Claws",
            "type": "claw",
            "die": 8,
            "flat_damage": 1,
            "hit_bonus": 1,
            "skill": "hunting",
            "on_hit": "Rear-up rake; belly and flanks.",
        },
        "behavior": "Leads border patrols; will call for backup if outmatched.",
    },
    "rogue_cat": {
        "name": "Rogue Cat",
        "category": "cats",
        "attrs": {
            "attr_str": 6,
            "attr_dex": 7,
            "attr_con": 5,
            "attr_int": 4,
            "attr_cha": 3,
            "attr_wis": 5,
        },
        "proficiencies": ["stealth"],
        "attack": {
            "name": "Bite",
            "type": "bite",
            "die": 4,
            "flat_damage": 1,
            "hit_bonus": 0,
            "skill": None,
        },
        "behavior": "No clan loyalty; steals prey, ambushes lone wolves, flees if bloodied.",
    },
    "loner_cat": {
        "name": "Loner Cat",
        "category": "cats",
        "attrs": {
            "attr_str": 5,
            "attr_dex": 7,
            "attr_con": 5,
            "attr_int": 5,
            "attr_cha": 4,
            "attr_wis": 6,
        },
        "proficiencies": ["stealth", "survival"],
        "attack": {
            "name": "Claw",
            "type": "claw",
            "die": 4,
            "flat_damage": 0,
            "hit_bonus": 0,
            "skill": None,
        },
        "behavior": "Solitary hunter; usually backs off unless cornered or starving.",
    },
    "kittypet": {
        "name": "Kittypet",
        "category": "cats",
        "attrs": {
            "attr_str": 3,
            "attr_dex": 5,
            "attr_con": 4,
            "attr_int": 3,
            "attr_cha": 6,
            "attr_wis": 3,
        },
        "proficiencies": [],
        "attack": {
            "name": "Hiss and Swat",
            "type": "claw",
            "die": 3,
            "flat_damage": 0,
            "hit_bonus": -1,
            "skill": None,
        },
        "behavior": "Soft-pawed Twoleg pet; panics easily and bolts for a fence or nest.",
    },
    "fox": {
        "name": "Fox",
        "category": "predators",
        "attrs": {
            "attr_str": 4,
            "attr_dex": 8,
            "attr_con": 5,
            "attr_int": 5,
            "attr_cha": 4,
            "attr_wis": 6,
        },
        "proficiencies": ["stealth", "tracking"],
        "attack": {
            "name": "Snap",
            "type": "bite",
            "die": 4,
            "flat_damage": 0,
            "hit_bonus": 1,
            "skill": None,
            "on_hit": "Quick nip; then they dart away.",
        },
        "behavior": "Cunning scavenger; raids caches and kits; rarely stands ground.",
    },
    "water_snake": {
        "name": "Water Snake",
        "category": "reptiles",
        "attrs": {
            "attr_str": 3,
            "attr_dex": 9,
            "attr_con": 4,
            "attr_int": 2,
            "attr_cha": 2,
            "attr_wis": 6,
        },
        "proficiencies": ["stealth"],
        "attack": {
            "name": "Venom Bite",
            "type": "bite",
            "die": 4,
            "flat_damage": 0,
            "hit_bonus": 2,
            "skill": None,
            "on_hit": "Marsh venom; swelling may follow.",
        },
        "behavior": "Coils from reeds at the bank; strikes fast and slides away.",
    },
    "garter_snake": {
        "name": "Garter Snake",
        "category": "reptiles",
        "attrs": {
            "attr_str": 3,
            "attr_dex": 8,
            "attr_con": 4,
            "attr_int": 2,
            "attr_cha": 2,
            "attr_wis": 5,
        },
        "proficiencies": ["stealth"],
        "attack": {
            "name": "Bite",
            "type": "bite",
            "die": 4,
            "flat_damage": 0,
            "hit_bonus": 1,
            "skill": None,
            "on_hit": "Quick strike; mild venom on a bad day.",
        },
        "behavior": "Sun-warms on stone; bites when cornered, then flees.",
    },
    "skink": {
        "name": "Skink",
        "category": "reptiles",
        "attrs": {
            "attr_str": 2,
            "attr_dex": 9,
            "attr_con": 3,
            "attr_int": 2,
            "attr_cha": 2,
            "attr_wis": 4,
        },
        "proficiencies": ["stealth"],
        "attack": {
            "name": "Snap",
            "type": "bite",
            "die": 3,
            "flat_damage": 0,
            "hit_bonus": 0,
            "skill": None,
            "on_hit": "Tiny jaws; more insult than wound.",
        },
        "behavior": "Darts from sun-warmed rock; prey-sized, not a real threat alone.",
    },
    "spider": {
        "name": "Wolf Spider",
        "category": "reptiles",
        "attrs": {
            "attr_str": 2,
            "attr_dex": 10,
            "attr_con": 3,
            "attr_int": 1,
            "attr_cha": 1,
            "attr_wis": 5,
        },
        "proficiencies": ["stealth"],
        "attack": {
            "name": "Bite",
            "type": "bite",
            "die": 3,
            "flat_damage": 0,
            "hit_bonus": 2,
            "skill": None,
            "on_hit": "Irritating bite; welts and dread.",
        },
        "behavior": "Hunts in leaf litter; too many legs, too fast.",
    },
    "badger": {
        "name": "Badger",
        "category": "predators",
        "attrs": {
            "attr_str": 8,
            "attr_dex": 4,
            "attr_con": 9,
            "attr_int": 3,
            "attr_cha": 5,
            "attr_wis": 4,
        },
        "proficiencies": ["intimidation"],
        "attack": {
            "name": "Claw Rake",
            "type": "claw",
            "die": 8,
            "flat_damage": 2,
            "hit_bonus": 0,
            "skill": None,
            "on_hit": "Thick hide; your **Badger Defence** maneuver was made for this.",
        },
        "behavior": "Fears nothing in its sett; one of the deadliest fights in the forest.",
    },
}

NPC_CATEGORY_LABELS = {
    "predators": "predators & threats",
    "dogs": "hearth-hounds (twoleg hounds)",
    "cats": "clan cats & rivals",
    "reptiles": "Reptiles & Vermin",
}

HAZARD_TOPICS: dict[str, tuple[str, str]] = {
    "humans": (
        "Humans (Two-Legs)",
        "Slow, soft, nearly blind; but they carry **thundersticks**, set traps, "
        "and command hearth-hounds. Being seen is dangerous.\n\n"
        "**Adult, alert**; Stealth (sneak past) +0 · Perception +0 by day, −2 at night · "
        "Wisdom save vs. intimidation +3 · Hearth-hounds with them have +4 Perception.\n\n"
        "**Juvenile**; Stealth −1 · Perception −1 · Wisdom save vs. intimidation +1 "
        "(easily frightened).\n\n"
        "**Thunderstick (firearm):** If spotted while armed, human rolls **1d20+2**. "
        "On a hit: **2d6** damage and flee immediately. Critical hit: crippled "
        "(broken leg) or killed.\n\n"
        "**Escaping on foot:** Opposed; your Dexterity vs. their **1d20+0**. "
        "Loss means pursuit (may call others).\n\n"
        "**Hiding from search:** Opposed; your Dexterity + Stealth vs. their "
        "**1d20 + Perception**. Loss means spotted (roll for thunderstick).",
    ),
    "thunderpath": (
        "Thunderpath (Road)",
        "Black stone that reeks of oil and dead prey, traveled by **monsters** (vehicles).\n\n"
        "• **No monster coming**; DC 8 to cross.\n"
        "• **Monster heard, not seen**; opposed: Intelligence + Survival/Constitution vs. "
        "monster **1d20+8**. Failure: abort. Critical failure: on the path when it arrives.\n"
        "• **Monster visible, approaching fast**; DC 20 (Desperate), Dexterity + Sprint. "
        "Failure: hit. Critical failure: killed instantly.\n\n"
        "**Struck by a monster:** **4d6+5** damage. Survivors have multiple broken bones; "
        "pack must drag them off and treat for weeks.\n\n"
        "**Scent near Thunderpath:** All scent-based Perception at disadvantage.\n\n"
        "**Monster stats:**\n"
        "Small (car); Speed **1d20+8** · Damage **3d6+5** · Perception 0\n"
        "Large (truck); Speed **1d20+6** · Damage **5d6+8** · Perception 0\n"
        "Parked, no humans; no threat.\n\n"
        "**Stealing roadkill:** Opposed; Dexterity + Stealth vs. approaching monster speed. "
        "Failure: passing human spots you (roll for thunderstick).",
    ),
    "traps": (
        "Traps",
        "Hidden metal jaws that smell of iron and old blood.\n\n"
        "• **Spot before stepping**; DC 15 (Intelligence + Tracking).\n"
        "• **Caught**; **2d4+2** damage; held in place.\n"
        "• **Escape**; opposed: your Strength vs. trap **1d20+5**. Failure: remain trapped "
        "(may take damage again).\n"
        "• **Free a packmate**; DC 12 (Intelligence or Dexterity). Failure: trap snaps again.\n"
        "• **Untreated trapped leg**; treat as broken bone; infection may require amputation "
        "(Medic, DC 20, desperate).",
    ),
    "twoleg_nests": (
        "Two-Leg Nests (Buildings)",
        "• **Approach unseen**; Stealth DC 15.\n"
        "• **Forage in garbage**; DC 8 to find food; Survival/Constitution save DC 12 or poisoned.\n"
        "• **Escape if chased**; opposed: Dexterity vs. human **1d20+0**. Loss may bring hearth-hounds "
        "or thunderstick.",
    ),
    "fences": (
        "Fences",
        "• **Wooden**; climb (Dexterity) DC 10. Failure: catch fur, **1d4** damage, but over.\n"
        "• **Wire/chicken wire**; dig under (Strength + Survival/Constitution) DC 8. "
        "Critical failure: cut paw on wire.\n"
        "• **Electric (rare)**; find weak spot DC 18 (Desperate). Failure: **1d6** damage, "
        "cannot move 1 round.",
    ),
}


def format_npc_category(template_key: str) -> str:
    """Short category label for ambush and combat footers."""
    category = BESTIARY_NPCS.get(template_key, {}).get("category", "predators")
    return NPC_CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def build_npc_stats(template_key: str) -> dict:
    """Build a combat stat dict for resolve_attack from a bestiary key."""
    import json

    from engine.combat_size import size_class_for_template

    template = BESTIARY_NPCS[template_key]
    stats = dict(template["attrs"])
    stats["skill_proficiencies"] = json.dumps(template.get("proficiencies", []))
    stats["npc_attack_profile"] = template["attack"]
    stats["npc_template"] = template_key
    stats["size_class"] = size_class_for_template(template_key, template.get("category"))
    if "maneuvers" in template:
        stats["maneuvers"] = template["maneuvers"]
    if "maneuver_weight" in template:
        stats["maneuver_weight"] = template["maneuver_weight"]
    return stats


def stats_for_fighter(fighter) -> dict:
    """resolve npc stats from a combat_fighters row, or generic fallback."""
    key = None
    if fighter and "npc_template" in fighter.keys():
        key = fighter["npc_template"]
    if key and key in BESTIARY_NPCS:
        return build_npc_stats(key)
    return {
        "attr_str": 14,
        "attr_dex": 12,
        "attr_con": 10,
        "attr_int": 10,
        "attr_cha": 10,
        "attr_wis": 10,
        "skill_proficiencies": "[]",
        "size_class": "medium",
    }


def format_npc_summary(template_key: str) -> str:
    t = BESTIARY_NPCS[template_key]
    a = t["attrs"]
    hp = npc_hp(t)
    lines = [
        f"**hp:** {hp} ({format_max_hp_breakdown(a['attr_str'], a['attr_con'], max_hp=hp)})",
        (
            f"str {a['attr_str']} · dex {a['attr_dex']} · con {a['attr_con']} · "
            f"int {a['attr_int']} · cha {a['attr_cha']} · wis {a['attr_wis']}"
        ),
    ]
    atk = t["attack"]
    dmg = f"{atk['name']} 1d{atk['die']}"
    if atk.get("flat_damage"):
        dmg += f"+{atk['flat_damage']}"
    if atk.get("hit_bonus"):
        dmg += f" (+{atk['hit_bonus']} to hit)"
    lines.append(f"**attack:** {dmg}")
    if t.get("behavior"):
        lines.append(f"_{t['behavior']}_")
    return "\n".join(lines)


def npc_choices_for_category(category: str) -> list[tuple[str, str]]:
    return [
        (key, data["name"])
        for key, data in BESTIARY_NPCS.items()
        if data["category"] == category
    ]
