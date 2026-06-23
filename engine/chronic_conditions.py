"""Chronic illness acquisition; rabies, wasting, cancer, dementia, feral shift."""

from __future__ import annotations

import random
import sqlite3

import database as db
from config import ELDER_MIN_MOONS
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

    if not attacker_f.get("discord_id"):
        return notes[0] if notes else None

    attacker = db.get_user(attacker_f["discord_id"])
    if not attacker:
        return notes[0] if notes else None
    a_key, a_stage = parse_disease(attacker["disease"] if "disease" in attacker.keys() else None)
    if a_key == "rabies" and a_stage in ("frenzy", "terminal"):
        note = try_rabies_bite_exposure(defender_user, chance=0.55)
        if note:
            notes.append(f"Rabid bite: {note}")
    return notes[0] if notes else None


def try_near_death_mental_trauma(user) -> str | None:
    """Dropping to dying can fracture the mind toward the wild."""
    return try_feral_shift_from_trauma(user, chance=0.08)


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
        if note:
            notes.append(
                {
                    "wolf_name": user["wolf_name"],
                    "discord_id": user["discord_id"],
                    "message": note,
                }
            )
    return notes
