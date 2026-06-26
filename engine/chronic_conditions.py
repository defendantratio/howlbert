"""Chronic illness acquisition; rabies, wasting, cancer, dementia, feral shift."""

from __future__ import annotations

import random
import sqlite3

import database as db
from config import ELDER_MIN_MOONS
from engine.combat_display import fighter_val
from engine.conditions import parse_injuries
from engine.disease_contract import try_contract_disease
from engine.diseases import parse_disease

RABIES_BITE_SOURCES = frozenset({"dog_feral", "wolf", "wolf_rogue", "wolf_hostile"})
ELDER_CHRONIC_AGE = ELDER_MIN_MOONS + 12  # 72+ moons


def try_rabies_bite_exposure(user, *, chance: float = 0.22) -> str | None:
    return try_contract_disease(user, "rabies", "incubation", chance=chance)


def try_wasting_from_carrion(user) -> str | None:
    return try_contract_disease(user, "wasting_sickness", "waning", chance=0.04)


def try_feral_shift_from_trauma(user, *, chance: float = 0.08) -> str | None:
    return try_contract_disease(user, "feral_shift", "restless", chance=chance)


def try_dementia_from_age(user, *, chance: float = 0.06) -> str | None:
    return try_contract_disease(user, "dementia", "forgetful", chance=chance)


def try_cancer_from_age(user, *, chance: float = 0.04) -> str | None:
    return try_contract_disease(user, "cancer", "lump", chance=chance)


def try_dementia_from_concussion(user) -> str | None:
    injuries = parse_injuries(user["active_injuries"] if "active_injuries" in user.keys() else None)
    if "concussion" not in injuries:
        return None
    age = int(user["age_months"]) if "age_months" in user.keys() else 0
    if age < ELDER_MIN_MOONS:
        return None
    return try_contract_disease(user, "dementia", "forgetful", chance=0.12)


def try_combat_bite_disease(
    defender_user,
    attacker_f,
    *,
    action: str,
    maneuver_key: str | None,
    hit: bool,
) -> str | None:
    """Rabies from hearth-hound / hostile wolf bites; spread from rabid attackers."""
    if not hit or not defender_user or not attacker_f:
        return None
    bite = maneuver_key in (
        "killing_bite",
        "spine_bite",
        "neck_snap",
    ) or (not maneuver_key and action == "bite")
    if not bite:
        return None

    notes: list[str] = []
    npc_template = attacker_f["npc_template"] if "npc_template" in attacker_f.keys() else None
    if npc_template in RABIES_BITE_SOURCES:
        note = try_rabies_bite_exposure(defender_user, chance=0.28 if npc_template == "dog_feral" else 0.12)
        if note:
            notes.append(note)
        distemper = try_contract_disease(defender_user, "distemper", chance=0.10)
        if distemper:
            notes.append(f"Canid bite: {distemper}")

    from engine.reptile_fear import VENOMOUS_REPTILE_TEMPLATES

    if npc_template in VENOMOUS_REPTILE_TEMPLATES:
        from engine.disease_contract import try_snake_venom_exposure

        chance = 0.45 if npc_template == "water_snake" else 0.28
        venom = try_snake_venom_exposure(defender_user, chance=chance)
        if venom:
            notes.append(venom)
    elif npc_template == "skink":
        from engine.disease_contract import try_insect_sting_exposure

        sting = try_insect_sting_exposure(defender_user, chance=0.22)
        if sting:
            notes.append(sting)

    if not fighter_val(attacker_f, "discord_id"):
        return "; ".join(notes) if notes else None

    attacker = db.get_user(attacker_f["discord_id"])
    if not attacker:
        return "; ".join(notes) if notes else None
    a_key, a_stage = parse_disease(attacker["disease"] if "disease" in attacker.keys() else None)
    if a_key == "rabies" and a_stage in ("frenzy", "terminal"):
        note = try_rabies_bite_exposure(defender_user, chance=0.55)
        if note:
            notes.append(f"Rabid bite: {note}")
    return "; ".join(notes) if notes else None


def try_near_death_mental_trauma(user) -> str | None:
    """Dropping to dying can fracture the mind toward the wild."""
    from engine.disease_contract import (
        try_night_terrors_from_trauma,
        try_shock_emotional_from_trauma,
    )

    notes: list[str] = []
    shock = try_shock_emotional_from_trauma(user, chance=0.15)
    if shock:
        notes.append(shock)
    terrors = try_night_terrors_from_trauma(user, chance=0.12)
    if terrors:
        notes.append(terrors)
    feral = try_feral_shift_from_trauma(user, chance=0.08)
    if feral:
        notes.append(feral)
    return "; ".join(notes) if notes else None


def apply_elder_chronic_on_rollover(conn: sqlite3.Connection) -> list[dict]:
    """Elders may develop dementia, wasting, or cancer if not already ill."""
    rows = conn.execute(
        """
        SELECT * FROM users
        WHERE condition NOT IN ('dead', 'dying')
          AND age_months >= ?
          AND (disease IS NULL OR disease = '')
        """,
        (ELDER_CHRONIC_AGE,),
    ).fetchall()
    notes: list[dict] = []
    for user in rows:
        roll = random.random()
        note = None
        if roll < 0.015:
            note = try_cancer_from_age(user, chance=1.0)
        elif roll < 0.10:
            note = try_contract_disease(user, "wasting_sickness", "waning", chance=1.0)
        elif roll < 0.16:
            note = try_dementia_from_age(user, chance=1.0)
        elif roll < 0.20:
            note = try_dementia_from_concussion(user)
            if not note and "concussion" in parse_injuries(
                user["active_injuries"] if "active_injuries" in user.keys() else None
            ):
                note = try_contract_disease(user, "dementia", "forgetful", chance=1.0)
        if note:
            notes.append(
                {
                    "wolf_name": user["wolf_name"],
                    "discord_id": user["discord_id"],
                    "message": note,
                }
            )
    return notes
