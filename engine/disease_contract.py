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
    conn=None,
) -> str | None:
    """
    Attempt to give a wolf a disease. Returns a player-facing note, or None.
    Won't replace an existing illness with a different one.

    Pass ``conn`` to write through an already-open connection (avoids a
    second connection deadlocking on the same database during rollover).
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
    if conn is not None:
        conn.execute(
            "UPDATE users SET disease = ? WHERE id = ?",
            (encoded, user["id"]),
        )
    else:
        db.set_user_conditions(user["discord_id"], wolf_id=user["id"], disease=encoded)
    return f"**{info['name']}**; {info['effect']}"


def try_poop_roll_exposure(user) -> str | None:
    """filth exposure; rolling in droppings (play, socialize, explore mishaps)."""
    return try_contract_disease(user, "diarrhea", chance=0.35)


def try_rotting_meat_exposure(user) -> str | None:
    """spoiled prey; gut sickness; rare mold-spore cough (warriors-style)."""
    if random.random() < 0.45:
        note = try_contract_disease(user, "diarrhea", chance=1.0)
        if note:
            return f"rotting meat: {note}"
    note = try_contract_disease(user, "cough", "mild", chance=0.12)
    if note:
        return f"mold spores in rotten meat; **green-cough** (spore-lung): {note}"
    return None


def try_carrion_exposure(user) -> str | None:
    roll = random.random()
    if roll < 0.12:
        return try_contract_disease(user, "hepatitis", chance=1.0)
    if roll < 0.22:
        note = try_contract_disease(user, "distemper", chance=1.0)
        if note:
            return f"carrion from a sick canid: {note}"
    if roll < 0.26:
        from engine.chronic_conditions import try_wasting_from_carrion

        return try_wasting_from_carrion(user)
    return None


def try_pupcough_exposure(user, chance: float = 0.12) -> str | None:
    """pup-susceptible cough; only wolves under one year."""
    age = int(user["age_months"]) if user and "age_months" in user.keys() else 24
    if age >= 12:
        return None
    if age < 6:
        chance = min(0.28, chance * 1.75)
    return try_contract_disease(user, "pupcough", "active", chance=chance)


def try_shock_emotional_from_trauma(user, chance: float = 0.15) -> str | None:
    return try_contract_disease(user, "shock_emotional", "active", chance=chance)


def try_grief_on_bond_loss(
    user, bond_type: str = "mate", *, chance: float = 0.55, conn=None
) -> str | None:
    if bond_type != "mate":
        return None
    note = try_contract_disease(
        user, "grief_melancholy", "mourning", chance=chance, conn=conn
    )
    if note:
        return f"mate lost: {note}"
    return None


def try_insomnia_from_distress(user, *, chance: float = 0.12, conn=None) -> str | None:
    mood = int(user["mood"]) if user and "mood" in user.keys() else 50
    distressed = int(user["distressed"]) if user and "distressed" in user.keys() else 0
    if mood >= 25 and not distressed:
        return None
    if distressed:
        chance = min(0.22, chance * 1.35)
    return try_contract_disease(user, "insomnia", "restless", chance=chance, conn=conn)


def try_night_terrors_from_trauma(user, chance: float = 0.12) -> str | None:
    return try_contract_disease(user, "night_terrors", "restless_nights", chance=chance)


def try_chronic_stress_from_low_mood(
    user, low_mood_days: int, *, chance: float = 0.12, conn=None
) -> str | None:
    if low_mood_days < 3:
        return None
    adjusted = min(0.45, chance + max(0, low_mood_days - 3) * 0.04)
    return try_contract_disease(user, "chronic_stress", "tense", chance=adjusted, conn=conn)


def try_eating_distress_from_hunger(user, *, chance: float = 0.14, conn=None) -> str | None:
    from config import HUNGER_LOW_THRESHOLD

    hunger = int(user["hunger"]) if user and "hunger" in user.keys() else 50
    if hunger > 20:
        return None
    if hunger <= 0:
        chance = min(0.35, chance * 2.0)
    elif hunger < HUNGER_LOW_THRESHOLD:
        chance = min(0.25, chance * 1.4)
    return try_contract_disease(user, "eating_distress", "picky", chance=chance, conn=conn)


def try_delirium_with_fever(user, *, chance: float = 0.35) -> str | None:
    """Fever delirium overlays an active physical illness (stored in herb_buffs)."""
    if not user or user["condition"] in ("dead", "dying"):
        return None
    from engine.diseases import is_mental_disease, parse_disease
    from engine.herb_buffs import get_buffs, merge_buff_fields

    key, _ = parse_disease(user["disease"] if "disease" in user.keys() else None)
    if not key or is_mental_disease(key):
        return None
    if get_buffs(user).get("mental_disease"):
        return None
    if chance < 1.0 and random.random() > chance:
        return None
    info = get_stage_info("delirium", "feverish")
    if not info:
        return None
    fields = merge_buff_fields(user, mental_disease=encode_disease("delirium", "feverish"))
    db.update_user(user["discord_id"], wolf_id=user["id"], herb_buffs=fields["herb_buffs"])
    return f"**{info['name']}**; {info['effect']}"


def try_pack_madness_from_den_stress(
    user, pack_unity: int, *, chance: float = 0.08, conn=None
) -> str | None:
    if pack_unity > 2:
        return None
    if pack_unity <= 0:
        chance = min(0.22, chance * 2.2)
    elif pack_unity <= 2:
        chance = min(0.15, chance * 1.5)
    note = try_contract_disease(user, "pack_madness", "wary", chance=chance, conn=conn)
    if note:
        return f"den stress: {note}"
    return None


def _fever_note_with_delirium(user, note: str | None) -> str | None:
    if not note:
        return None
    delirium = try_delirium_with_fever(user)
    if delirium:
        return f"{note}; {delirium}"
    return note


def try_den_filth_exposure(user, *, day: int | None = None) -> str | None:
    """nest filth and droppings; gi bugs and pup-susceptible viral illness."""
    from engine.herb_buffs import burial_scent_masked

    if day is None:
        day = int(user["last_rest_day"] if user and "last_rest_day" in user.keys() else 0)
    if burial_scent_masked(user, day) and random.random() < 0.5:
        return None

    age = int(user["age_months"]) if user and "age_months" in user.keys() else 24
    if age < 12:
        pup_note = try_pupcough_exposure(user)
        if pup_note:
            return pup_note
    pox_chance = 0.14 if age < 12 else 0.05
    if random.random() < pox_chance:
        note = try_contract_disease(user, "pox", chance=1.0)
        if note:
            return note
    return try_poop_roll_exposure(user)


def try_scavenge_canid_exposure(user) -> str | None:
    """scavenge near hearth-hound kills or mangy coyote leavings."""
    roll = random.random()
    if roll < 0.10:
        note = try_contract_disease(user, "distemper", chance=1.0)
        if note:
            return f"sick canid leavings: {note}"
    if roll < 0.16:
        note = try_contract_disease(user, "mange", chance=1.0)
        if note:
            return f"nest mites from a mangy den site: {note}"
    return None


def try_scavenge_filth_exposure(user, *, day: int | None = None) -> str | None:
    from engine.herb_buffs import burial_scent_masked

    if day is None:
        day = int(user["last_rest_day"] if user and "last_rest_day" in user.keys() else 0)
    flea_chance = 0.05 if burial_scent_masked(user, day) else 0.10
    if random.random() < flea_chance:
        return try_contract_disease(user, "fleas", chance=1.0)
    note = try_scavenge_canid_exposure(user)
    if note:
        return note
    return try_carrion_exposure(user)


def try_weather_fever_exposure(user) -> str | None:
    gp = user["great_pack"] if user and "great_pack" in user.keys() else None
    if gp == "mistmoor" and random.random() < 0.35:
        note = try_contract_disease(user, "rot_lung", "fever", chance=0.28)
        return _fever_note_with_delirium(user, note)
    note = try_contract_disease(user, "influenza", chance=0.25)
    return _fever_note_with_delirium(user, note)


def try_mistmoor_swamp_exposure(user, *, belly_rip: bool = False) -> str | None:
    """Belly-Rip vigils and swamp rot; Mistmoor only."""
    gp = user["great_pack"] if user and "great_pack" in user.keys() else None
    if gp != "mistmoor":
        return None
    if belly_rip:
        note = try_contract_disease(user, "shaking_sickness", "shaking", chance=0.16)
        if note:
            return f"belly-rip water: {note}"
        note = try_contract_disease(user, "rot_lung", "fever", chance=0.10)
        if note:
            return _fever_note_with_delirium(user, f"marsh rot: {note}")
        return None
    note = try_contract_disease(user, "rot_lung", "fever", chance=0.08)
    if note:
        return _fever_note_with_delirium(user, note)
    return None


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
            "**nursing strain**; heavy lactation may bring **milk-fever** tremors "
            "over the next few sunrises."
        )
    return (
        "**nursing watch**; peak lactation may bring **milk-fever** tremors "
        "1–3 sunrises after birth."
    )


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
                    "line": f"peak nursing: {note}",
                }
            )
    return notes


def try_contract_milk_fever(user, *, difficult_birth: bool = False) -> str | None:
    """deprecated alias; birth flow should call schedule_milk_fever_risk with the den day."""
    return None


def try_sick_traveler_exposure(user) -> str | None:
    """infected stranger near the border; warriors-style plague vector."""
    note = try_contract_disease(user, "yellowcough", chance=0.05)
    if note:
        return f"sick traveler: {note}"
    return None


def try_hunt_flea_exposure(user, *, day: int | None = None) -> str | None:
    from engine.herb_buffs import flea_ward_active

    if day is None:
        day = int(user["last_rest_day"] if user and "last_rest_day" in user.keys() else 0)
    if flea_ward_active(user, day):
        return None
    return try_contract_disease(user, "fleas", chance=0.06)


def try_insect_sting_exposure(user, *, chance: float = 0.08) -> str | None:
    """Wasps, hornets, horseflies while ranging, foraging, or digging."""
    note = try_contract_disease(user, "mild_poison", "stung", chance=chance)
    if note:
        return f"biting insects: {note}"
    return None


def try_snake_venom_exposure(user, *, chance: float = 0.06) -> str | None:
    """creek banks, marsh edges, and fishing strikes."""
    gp = user["great_pack"] if user and "great_pack" in user.keys() else None
    if gp in ("mistmoor", "silverrush"):
        chance = min(0.18, chance * 1.6)
    note = try_contract_disease(user, "mild_poison", "venom", chance=chance)
    if note:
        return f"snake strike: {note}"
    return None


def try_poison_ivy_exposure(user, *, chance: float = 0.09) -> str | None:
    """twoleg fence-lines and oily verge weeds."""
    note = try_contract_disease(user, "poison_ivy", chance=chance)
    if note:
        return f"contact rash: {note}"
    return None


def try_nettle_sting_exposure(user, *, chance: float = 0.55) -> str | None:
    """stinging nettle harvest; rash and welts even when you know the plant."""
    note = try_contract_disease(user, "mild_poison", "stung", chance=chance)
    if note:
        return f"nettle welts: {note}"
    return None


def try_verge_toxic_misid_exposure(user) -> str | None:
    """grabbed the wrong ditch plant on a verge critical failure."""
    roll = random.random()
    if roll < 0.45:
        note = try_contract_disease(user, "mild_poison", "stung", chance=1.0)
        if note:
            return f"toxic misidentification: {note}"
    if roll < 0.7:
        note = try_poison_ivy_exposure(user, chance=1.0)
        if note:
            return note
    return None


def try_mating_disease_spread(healthy, carrier) -> str | None:
    """mating; redscratch, respiratory illness, and other mating_contagious diseases."""
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
        return f"mating exposure: {note}"
    return None


def apply_mental_illness_rollover(conn, day: int) -> list[dict]:
    """after vitals decay; mood/hunger stress may trigger mental illness."""
    from config import MOOD_LOW_THRESHOLD
    from engine.herb_buffs import get_buffs, merge_buff_fields

    rows = conn.execute(
        """
        SELECT * FROM users
        WHERE condition NOT IN ('dead', 'dying')
        """
    ).fetchall()
    notes: list[dict] = []
    for user in rows:
        mood = int(user["mood"]) if user["mood"] is not None else 50
        buffs = get_buffs(user)
        low_mood_days = int(buffs.get("low_mood_days") or 0)
        if mood < MOOD_LOW_THRESHOLD:
            low_mood_days += 1
        else:
            low_mood_days = 0
        buff_fields = merge_buff_fields(user, low_mood_days=low_mood_days)
        conn.execute(
            "UPDATE users SET herb_buffs = ? WHERE id = ?",
            (buff_fields["herb_buffs"], user["id"]),
        )
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        if not user:
            continue

        note = try_insomnia_from_distress(user, conn=conn)
        if not note:
            note = try_chronic_stress_from_low_mood(user, low_mood_days, conn=conn)
        if not note:
            note = try_eating_distress_from_hunger(user, conn=conn)
        if not note and user["pack_id"]:
            pack = conn.execute(
                "SELECT pack_unity FROM packs WHERE id = ?", (user["pack_id"],)
            ).fetchone()
            unity = int(pack["pack_unity"]) if pack else 5
            note = try_pack_madness_from_den_stress(user, unity, conn=conn)
        if note:
            notes.append(
                {
                    "wolf_name": user["wolf_name"],
                    "discord_id": user["discord_id"],
                    "line": note,
                }
            )
    return notes


def try_spread_from_close_contact(healthy, carrier) -> str | None:
    """groom, socialize; immediate transmission roll at half pack contagion rate."""
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
        return f"close contact: {note}"
    return None
