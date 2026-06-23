"""Contract illnesses from filth, prey, weather, and close contact."""

from __future__ import annotations

import random

import database as db
from engine.diseases import DISEASES, encode_disease, get_stage_info, parse_disease


def has_disease(user) -> bool:
    key, _ = parse_disease(user["disease"] if user and "disease" in user.keys() else None)
    return key is not None


def try_contract_disease(
    user,
    disease_key: str,
    stage: str | None = None,
    *,
    chance: float = 1.0,
) -> str | None:
    """
    Attempt to give a wolf a disease. Returns a player-facing note, or None.
    Won't replace an existing illness with a different one.
    """
    if not user or user["condition"] in ("dead", "dying"):
        return None
    if chance < 1.0 and random.random() > chance:
        return None

    disease = DISEASES.get(disease_key)
    if not disease:
        return None

    stage = stage or disease.get("spread_stage") or next(iter(disease["stages"]))
    info = get_stage_info(disease_key, stage)
    if not info:
        return None

    existing_key, existing_stage = parse_disease(
        user["disease"] if "disease" in user.keys() else None
    )
    if existing_key:
        if existing_key == disease_key:
            return None
        return None

    encoded = encode_disease(disease_key, stage)
    db.set_user_conditions(user["discord_id"], wolf_id=user["id"], disease=encoded)
    return f"**{info['name']}**; {info['effect']}"


def try_poop_roll_exposure(user) -> str | None:
    """Filth exposure; rolling in droppings (play, socialize, explore mishaps)."""
    return try_contract_disease(user, "diarrhea", chance=0.35)


def try_rotting_meat_exposure(user) -> str | None:
    """Spoiled prey; gut sickness; rare mold-spore cough (Warriors-style)."""
    if random.random() < 0.45:
        note = try_contract_disease(user, "diarrhea", chance=1.0)
        if note:
            return f"Rotting meat: {note}"
    note = try_contract_disease(user, "cough", "mild", chance=0.12)
    if note:
        return f"Mold spores in rotten meat; **Green-cough** (spore-lung): {note}"
    return None


def try_carrion_exposure(user) -> str | None:
    roll = random.random()
    if roll < 0.12:
        return try_contract_disease(user, "hepatitis", chance=1.0)
    if roll < 0.22:
        note = try_contract_disease(user, "distemper", chance=1.0)
        if note:
            return f"Carrion from a sick canid: {note}"
    if roll < 0.26:
        from engine.chronic_conditions import try_wasting_from_carrion

        return try_wasting_from_carrion(user)
    return None


def try_den_filth_exposure(user) -> str | None:
    """Nest filth and droppings; GI bugs and pup-susceptible viral illness."""
    age = int(user["age_months"]) if user and "age_months" in user.keys() else 24
    pox_chance = 0.14 if age < 12 else 0.05
    if random.random() < pox_chance:
        note = try_contract_disease(user, "pox", chance=1.0)
        if note:
            return note
    return try_poop_roll_exposure(user)


def try_scavenge_canid_exposure(user) -> str | None:
    """Scavenge near hearth-hound kills or mangy coyote leavings."""
    roll = random.random()
    if roll < 0.10:
        note = try_contract_disease(user, "distemper", chance=1.0)
        if note:
            return f"Sick canid leavings: {note}"
    if roll < 0.16:
        note = try_contract_disease(user, "mange", chance=1.0)
        if note:
            return f"Nest mites from a mangy den site: {note}"
    return None


def try_scavenge_filth_exposure(user) -> str | None:
    if random.random() < 0.10:
        return try_contract_disease(user, "fleas", chance=1.0)
    note = try_scavenge_canid_exposure(user)
    if note:
        return note
    return try_carrion_exposure(user)


def try_weather_fever_exposure(user) -> str | None:
    gp = user["great_pack"] if user and "great_pack" in user.keys() else None
    if gp == "mistmoor" and random.random() < 0.35:
        return try_contract_disease(user, "rot_lung", "fever", chance=0.28)
    return try_contract_disease(user, "influenza", chance=0.25)


def try_mistmoor_swamp_exposure(user, *, belly_rip: bool = False) -> str | None:
    """Belly-Rip vigils and swamp rot; Mistmoor only."""
    gp = user["great_pack"] if user and "great_pack" in user.keys() else None
    if gp != "mistmoor":
        return None
    if belly_rip:
        note = try_contract_disease(user, "shaking_sickness", "shaking", chance=0.16)
        if note:
            return f"Belly-Rip water: {note}"
        note = try_contract_disease(user, "rot_lung", "fever", chance=0.10)
        if note:
            return f"Marsh rot: {note}"
        return None
    return try_contract_disease(user, "rot_lung", "fever", chance=0.08)


def schedule_milk_fever_risk(
    user,
    *,
    day: int,
    difficult_birth: bool = False,
    litter_size: int = 1,
) -> str | None:
    """Schedule eclampsia risk 1-3 sunrises after whelping (peak lactation)."""
    from engine.attraction import get_birth_sex

    if get_birth_sex(user) != "female":
        return None
    due = day + random.randint(1, 3)
    db.update_user(user["discord_id"], wolf_id=user["id"], milk_fever_due_day=due)
    if difficult_birth or litter_size >= 4:
        return (
            "**Nursing strain**; heavy lactation may bring **milk-fever** tremors "
            "over the next few sunrises."
        )
    return None


def apply_pending_milk_fever_on_rollover(conn, day: int) -> list[dict]:
    """Roll milk-fever when scheduled due day arrives."""
    rows = conn.execute(
        """
        SELECT * FROM users
        WHERE milk_fever_due_day > 0
          AND milk_fever_due_day <= ?
          AND condition NOT IN ('dead', 'dying')
        """,
        (day,),
    ).fetchall()
    notes: list[dict] = []
    for user in rows:
        conn.execute(
            "UPDATE users SET milk_fever_due_day = 0 WHERE id = ?",
            (user["id"],),
        )
        if user["disease"]:
            continue
        chance = 0.28
        note = try_contract_disease(user, "milk_fever", chance=chance)
        if note:
            notes.append(
                {
                    "wolf_name": user["wolf_name"],
                    "discord_id": user["discord_id"],
                    "line": f"Peak nursing: {note}",
                }
            )
    return notes


def try_contract_milk_fever(user, *, difficult_birth: bool = False) -> str | None:
    """Deprecated alias; birth flow should call schedule_milk_fever_risk with the den day."""
    return None


def try_sick_traveler_exposure(user) -> str | None:
    """Infected stranger near the border; Warriors-style plague vector."""
    note = try_contract_disease(user, "yellowcough", chance=0.05)
    if note:
        return f"Sick traveler: {note}"
    return None


def try_hunt_flea_exposure(user) -> str | None:
    return try_contract_disease(user, "fleas", chance=0.06)


def try_mating_disease_spread(healthy, carrier) -> str | None:
    """Mating; redscratch, respiratory illness, and other mating_contagious diseases."""
    from engine.diseases import mating_contagious_rate, spread_stage_for
    from engine.quarantine import is_quarantined

    if is_quarantined(carrier) or is_quarantined(healthy):
        return None
    key, _ = parse_disease(carrier["disease"] if "disease" in carrier.keys() else None)
    if not key:
        return None
    rate = mating_contagious_rate(key)
    if rate <= 0:
        return None
    spread = spread_stage_for(key)
    note = try_contract_disease(healthy, key, spread, chance=rate)
    if note:
        return f"Mating exposure: {note}"
    return None


def try_spread_from_close_contact(healthy, carrier) -> str | None:
    """Groom, socialize; immediate transmission roll at half pack contagion rate."""
    from engine.quarantine import is_quarantined

    if is_quarantined(carrier) or is_quarantined(healthy):
        return None
    key, stage = parse_disease(carrier["disease"] if "disease" in carrier.keys() else None)
    if not key:
        return None
    from engine.diseases import contagious_rate, spread_stage_for

    rate = contagious_rate(key) * (1.0 if key == "yellowcough" else 0.5)
    if rate <= 0:
        return None
    spread = spread_stage_for(key)
    note = try_contract_disease(healthy, key, spread, chance=rate)
    if note:
        return f"Close contact: {note}"
    return None
