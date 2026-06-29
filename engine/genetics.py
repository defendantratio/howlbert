"""Genetic conditions; Wolvden-style birth mutations and register-time RP traits."""



from __future__ import annotations



import json

import random



# Keys stored in users.genetic_conditions JSON array.

GENETIC_CONDITIONS: dict[str, dict] = {

    "blindness": {

        "name": "Blindness",

        "effect": "Milky eyes; cannot see; disadvantage on Perception and ranged awareness. Compensates with scent and hearing: no penalty, plus +2, on Tracking.",

        "hunt_mult": 0.65,

        "perception_penalty": 3,

        "wis_disadvantage": True,

        "non_visual_skills": ("tracking",),

        "non_visual_bonus": 2,

        "lethal_at_birth": False,

        "inherit_weight": 8,

        "random_weight": 4,

    },

    "partial_blindness": {

        "name": "Partial Blindness (Hereditary Cataracts)",

        "effect": "Clouded vision: −2 Perception; disadvantage on Wisdom (Perception) checks. Compensates with scent and hearing: no penalty, plus +1, on Tracking.",

        "hunt_mult": 0.85,

        "perception_penalty": 2,

        "wis_disadvantage": True,

        "non_visual_skills": ("tracking",),

        "non_visual_bonus": 1,

        "lethal_at_birth": False,

        "inherit_weight": 10,

        "random_weight": 5,

    },

    "deafness": {

        "name": "Deafness",

        "effect": "Cannot hear pack calls; disadvantage on Wisdom checks involving listening.",

        "hunt_mult": 0.9,

        "wis_disadvantage": True,

        "lethal_at_birth": False,

        "inherit_weight": 8,

        "random_weight": 4,

    },

    "brachycephaly": {

        "name": "Brachycephaly",

        "effect": "Flat skull; labored breathing; −35% hunt bones; often fatal in newborns.",

        "hunt_mult": 0.65,

        "physical_disadvantage": True,

        "lethal_at_birth": True,

        "inherit_weight": 6,

        "random_weight": 2,

    },

    "albinism": {

        "name": "Albinism",

        "effect": "Pale coat and pink eyes; easier to spot (−1 Stealth on hunts).",

        "hunt_mult": 1.0,

        "stealth_penalty": 1,

        "lethal_at_birth": False,

        "inherit_weight": 5,

        "random_weight": 1,

    },

    "melanism": {

        "name": "Melanism",

        "effect": "Darkened coat: +1 Stealth when stalking prey at night.",

        "hunt_mult": 1.0,

        "stealth_bonus": 1,

        "lethal_at_birth": False,

        "inherit_weight": 5,

        "random_weight": 1,

    },

    "conjoined": {

        "name": "Conjoined",

        "effect": "Fused twin; body cannot survive long outside the womb.",

        "lethal_at_birth": True,

        "inherit_weight": 0,

        "random_weight": 1,

    },

    "missing_foreleg": {

        "name": "Missing Foreleg",

        "effect": "Three-legged: −50% hunt bones; disadvantage on Strength and Dexterity checks.",

        "hunt_mult": 0.5,

        "physical_disadvantage": True,

        "lethal_at_birth": False,

        "inherit_weight": 0,

        "random_weight": 2,

    },

    "missing_hindleg": {

        "name": "Missing Hindleg",

        "effect": "Three-legged: −50% hunt bones; disadvantage on Strength and Dexterity checks.",

        "hunt_mult": 0.5,

        "physical_disadvantage": True,

        "lethal_at_birth": False,

        "inherit_weight": 0,

        "random_weight": 2,

    },

    "missing_tail": {

        "name": "Missing Tail",

        "effect": "No tail; poor balance; disadvantage on Dexterity checks.",

        "hunt_mult": 0.9,

        "physical_disadvantage": True,

        "lethal_at_birth": False,

        "inherit_weight": 0,

        "random_weight": 1,

    },

    "muteness": {

        "name": "Muteness",

        "effect": "No voice; cannot howl, call for help, or rally the pack; relies on others to relay messages.",

        "hunt_mult": 0.95,

        "blocks_howl": True,

        "lethal_at_birth": False,

        "inherit_weight": 8,

        "random_weight": 3,

    },

}



LETHAL_AT_BIRTH_KEYS = frozenset(

    k for k, v in GENETIC_CONDITIONS.items() if v.get("lethal_at_birth")

)



REGISTERABLE_GENETIC = frozenset(

    {

        "blindness",

        "partial_blindness",

        "deafness",

        "brachycephaly",

        "albinism",

        "melanism",

        "missing_foreleg",

        "missing_hindleg",

        "missing_tail",

        "muteness",

    }

)



# Birth / register genetics that herbs must never remove (splints don't regrow limbs).


HERB_INCURABLE_GENETICS = frozenset(

    {

        "missing_foreleg",

        "missing_hindleg",

        "missing_tail",

        "blindness",

        "deafness",

        "brachycephaly",

        "albinism",

        "melanism",

        "conjoined",

        "muteness",

    }

)



# Genetics herbs may ease (e.g. celandine on hereditary cataracts).

HERB_CURABLE_GENETICS = frozenset({"partial_blindness"})



GENETIC_ALIASES: dict[str, str] = {

    "blind": "blindness",

    "spontaneous_blindness": "blindness",

    "half_blind": "partial_blindness",

    "half_blindness": "partial_blindness",

    "partial_blind": "partial_blindness",

    "cataracts": "partial_blindness",

    "hereditary_cataracts": "partial_blindness",

    "deaf": "deafness",

    "brachy": "brachycephaly",

    "albino": "albinism",

    "melanistic": "melanism",

    "missing_leg": "missing_hindleg",

    "three_legged": "missing_hindleg",

    "three_leg": "missing_hindleg",

    "foreleg": "missing_foreleg",

    "hindleg": "missing_hindleg",

    "no_tail": "missing_tail",

    "tailless": "missing_tail",

    "mute": "muteness",

    "mutism": "muteness",

    "voiceless": "muteness",

    "no_voice": "muteness",

}





def parse_genetic_conditions(raw: str | None) -> list[str]:

    if not raw:

        return []

    try:

        data = json.loads(raw)

    except (json.JSONDecodeError, TypeError):

        return []

    if not isinstance(data, list):

        return []

    out: list[str] = []

    for key in data:

        if isinstance(key, str) and key in GENETIC_CONDITIONS and key not in out:

            out.append(key)

    return out





def encode_genetic_conditions(keys: list[str]) -> str:

    clean = [k for k in keys if k in GENETIC_CONDITIONS]

    return json.dumps(clean)





def parse_genetic_register_input(raw: str | None) -> tuple[list[str], str | None]:

    """parse `/register genetic:` comma-separated list. returns (keys, error)."""

    if not raw or not raw.strip():

        return [], None

    keys: list[str] = []

    for part in raw.replace(";", ",").split(","):

        token = part.strip().lower().replace(" ", "_").replace("-", "_")

        if not token:

            continue

        key = GENETIC_ALIASES.get(token, token)

        if key not in GENETIC_CONDITIONS:

            return [], f"unknown genetic condition **{part.strip()}**."

        if key not in REGISTERABLE_GENETIC:

            return [], f"**{GENETIC_CONDITIONS[key]['name']}** cannot be chosen at register; it only appears at birth."

        if key not in keys:

            keys.append(key)

    return keys, None





def format_genetic_conditions(user) -> str:

    keys = parse_genetic_conditions(

        user["genetic_conditions"] if user and "genetic_conditions" in user.keys() else None

    )

    if not keys:

        return ""

    lines = []

    for key in keys:

        info = GENETIC_CONDITIONS[key]

        lines.append(f"**{info['name']}**; {info['effect']}")

    return "\n".join(lines)





def genetic_check_adjustments(
    user, attr_keys: tuple[str, ...], *, skill_key: str | None = None
) -> tuple[int, bool]:

    keys = parse_genetic_conditions(

        user["genetic_conditions"] if user and "genetic_conditions" in user.keys() else None

    )

    if not keys:

        return 0, False

    attrs = set(attr_keys)

    penalty = 0

    disadvantage = False

    for key in keys:

        info = GENETIC_CONDITIONS[key]

        # Blindness's wis_disadvantage models losing sight-based perception;
        # it shouldn't also punish scent/sound-based skills, where a blind
        # wolf compensates rather than suffers (non_visual_skills below).
        non_visual = skill_key in info.get("non_visual_skills", ())
        if info.get("wis_disadvantage") and "attr_wis" in attrs and not non_visual:

            disadvantage = True

        if info.get("physical_disadvantage") and attrs & {"attr_str", "attr_dex", "attr_con"}:

            disadvantage = True

        if not non_visual:
            penalty -= int(info.get("perception_penalty", 0)) if "attr_wis" in attrs else 0

        if info.get("stealth_penalty") and "attr_dex" in attrs:

            penalty -= int(info["stealth_penalty"])

        if info.get("stealth_bonus") and "attr_dex" in attrs:

            penalty += int(info["stealth_bonus"])

        if non_visual:
            penalty += int(info.get("non_visual_bonus", 0))

    return penalty, disadvantage





def genetic_hunt_multiplier(user) -> tuple[float, str]:

    keys = parse_genetic_conditions(

        user["genetic_conditions"] if user and "genetic_conditions" in user.keys() else None

    )

    if not keys:

        return 1.0, ""

    mult = 1.0

    notes: list[str] = []

    for key in keys:

        info = GENETIC_CONDITIONS[key]

        m = float(info.get("hunt_mult", 1.0))

        if m < mult:

            mult = m

            notes.append(info["name"])

    if mult >= 1.0:
        return 1.0, ""

    pct = int((1 - mult) * 100)
    if len(notes) == 1:
        label = notes[0]
    elif len(notes) > 1:
        label = ", ".join(notes[:2]) + ("…" if len(notes) > 2 else "")
    else:
        label = "Genetic condition"
    return mult, f"{label}; −{pct}% hunt bones."





def genetic_blocks_howl(user) -> tuple[bool, str]:
    """true when a genetic condition (e.g. muteness) forbids howling/rallying."""
    keys = parse_genetic_conditions(
        user["genetic_conditions"] if user and "genetic_conditions" in user.keys() else None
    )
    for key in keys:
        info = GENETIC_CONDITIONS[key]
        if info.get("blocks_howl"):
            return True, info["name"]
    return False, ""


def genetic_perception_penalty(user) -> int:

    keys = parse_genetic_conditions(

        user["genetic_conditions"] if user and "genetic_conditions" in user.keys() else None

    )

    penalty = 0

    for key in keys:

        penalty += int(GENETIC_CONDITIONS[key].get("perception_penalty", 0))

    return -penalty if penalty else 0





def genetic_keys_matching_cures(user, cures: tuple) -> list[str]:

    if not cures:

        return []

    keys = parse_genetic_conditions(

        user["genetic_conditions"] if user and "genetic_conditions" in user.keys() else None

    )

    return [

        k

        for k in keys

        if k in cures and k in HERB_CURABLE_GENETICS and k not in HERB_INCURABLE_GENETICS

    ]





def remove_genetic_keys(user, remove: list[str]) -> str:

    keys = parse_genetic_conditions(

        user["genetic_conditions"] if user and "genetic_conditions" in user.keys() else None

    )

    remaining = [k for k in keys if k not in remove]

    return encode_genetic_conditions(remaining)





def _parent_genetic_keys(parent) -> list[str]:

    return parse_genetic_conditions(

        parent["genetic_conditions"] if parent and "genetic_conditions" in parent.keys() else None

    )





def roll_pup_genetic_conditions(

    mother,

    father,

    *,

    birth_outcome: str = "success",

) -> tuple[list[str], bool]:

    """

    Roll birth mutations for one pup.

    Returns (conditions, lethal_stillborn); lethal stillborns are not registered.

    """

    conditions: list[str] = []

    inherit_pool: list[str] = []

    for parent in (mother, father):

        if not parent:

            continue

        for key in _parent_genetic_keys(parent):

            weight = GENETIC_CONDITIONS[key].get("inherit_weight", 5)

            inherit_pool.extend([key] * weight)



    if inherit_pool and random.random() < 0.22:

        pick = random.choice(inherit_pool)

        if pick not in conditions:

            conditions.append(pick)



    base_chance = 0.04

    if birth_outcome in ("failure", "critical_failure"):

        base_chance += 0.06

    if birth_outcome == "critical_failure":

        base_chance += 0.04



    if random.random() < base_chance:

        random_pool: list[str] = []

        for key, info in GENETIC_CONDITIONS.items():

            w = int(info.get("random_weight", 0))

            if w > 0:

                random_pool.extend([key] * w)

        if random_pool:

            pick = random.choice(random_pool)

            if pick not in conditions:

                conditions.append(pick)



    lethal = False

    for key in conditions:

        if GENETIC_CONDITIONS[key].get("lethal_at_birth"):

            if random.random() < 0.75:

                lethal = True

                break

    return conditions, lethal

