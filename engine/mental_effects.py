"""Mental degeneration; dementia, feral shift, and sentience loss."""

from __future__ import annotations

from engine.diseases import (
    blocks_field,
    blocks_social,
    get_stage_info,
    parse_disease,
)

MENTAL_ATTRS = frozenset({"attr_int", "attr_wis", "attr_cha"})


def _parsed(user) -> tuple[str | None, str | None]:
    raw = user["disease"] if user and "disease" in user.keys() else None
    return parse_disease(raw)


def mental_activity_block(user) -> str | None:
    """No total command block for unsentient; field/social blocks are separate."""
    return None


def field_activity_block(user) -> str | None:
    """Block hunt, patrol, explore, combat, and collab when mind is lost to the wild."""
    key, stage = _parsed(user)
    if not key or not stage:
        return None
    if blocks_field(key, stage):
        info = get_stage_info(key, stage)
        label = info["name"] if info else "Mind-Fracture"
        return (
            f"**{label}**; your wolf's mind is lost to the wild. "
            "Hunt, patrol, explore, and combat are beyond them. "
            "Den care (`/eat`, `/drink`, `/vitals`) still works."
        )
    return None


def social_activity_block(user) -> str | None:
    """Block courtship, socialize, groom when mind is too far gone."""
    key, stage = _parsed(user)
    if not key or not stage:
        return None
    if blocks_social(key, stage):
        info = get_stage_info(key, stage)
        label = info["name"] if info else "Mind lost"
        return f"**{label}**; social and courtship commands are beyond this wolf now."
    return None


def mental_check_adjustments(user, attr_keys: tuple[str, ...]) -> tuple[int, bool]:
    """Flat penalty and disadvantage from mental illnesses."""
    key, stage = _parsed(user)
    if not key or not stage:
        return 0, False
    attrs = set(attr_keys)
    disadvantage = False
    if key == "rabies":
        if stage in ("prodrome", "frenzy", "terminal"):
            disadvantage = bool(attrs & MENTAL_ATTRS)
        if stage in ("frenzy", "terminal") and "attr_cha" in attrs:
            disadvantage = True
    elif key == "dementia":
        if stage == "forgetful" and "attr_int" in attrs:
            disadvantage = True
        if stage in ("confused", "lost") and bool(attrs & {"attr_int", "attr_wis"}):
            disadvantage = True
    elif key == "feral_shift":
        if stage == "restless" and "attr_cha" in attrs:
            disadvantage = True
        if stage in ("feral", "unsentient") and bool(attrs & MENTAL_ATTRS):
            disadvantage = True
    elif key == "insomnia" and stage in ("sleepless", "exhaustion_cascade"):
        if "attr_wis" in attrs:
            disadvantage = True
    elif key == "anxiety":
        if stage in ("anxious", "panic_prone") and bool(attrs & {"attr_wis", "attr_cha"}):
            disadvantage = True
    elif key == "grief_melancholy" and stage in ("melancholy", "hollow"):
        if "attr_cha" in attrs:
            disadvantage = True
    elif key == "delirium" and stage in ("wandering", "incoherent"):
        if bool(attrs & {"attr_int", "attr_wis"}):
            disadvantage = True
    elif key == "pack_madness" and stage in ("wary", "paranoid", "break"):
        if "attr_cha" in attrs:
            disadvantage = True
    elif key == "obsession":
        if stage in ("fixated", "compulsive", "tunnel_vision") and "attr_int" in attrs:
            disadvantage = True
        if stage == "tunnel_vision" and "attr_wis" in attrs:
            disadvantage = True
    elif key == "night_terrors" and stage in ("screaming_dreams", "sleep_panic"):
        if "attr_wis" in attrs:
            disadvantage = True
    elif key == "chronic_stress" and stage in ("strained", "frayed"):
        if bool(attrs & {"attr_wis", "attr_con"}):
            disadvantage = True
    elif key == "eating_distress" and stage in ("refusing", "wasting"):
        if "attr_con" in attrs:
            disadvantage = True
    elif key == "shock_emotional":
        if bool(attrs & {"attr_wis", "attr_cha"}):
            disadvantage = True
    return 0, disadvantage
