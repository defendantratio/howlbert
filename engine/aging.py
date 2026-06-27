"""Wolf age in moons; life stages, milestones, and role sync."""

from __future__ import annotations

import json

from config import ELDER_MIN_MOONS, JUVENILE_MAX_MOONS, MAX_WOLF_AGE_MOONS, MOONS_PER_ROLLOVER, PUP_MAX_MOONS
from engine.apprentice_roles import APPRENTICE_ROLES
from engine.role_restrictions import AGE_OVERRIDE_ROLES, JUVENILE_ROLE, PUP_ROLE
from rpg_rules import ROLE_LABELS, ROLE_PROFICIENCIES

YOUNG_LIFE_ROLES = frozenset({PUP_ROLE, JUVENILE_ROLE})
ADULT_ROLES = frozenset(ROLE_PROFICIENCIES.keys()) - YOUNG_LIFE_ROLES

DEFAULT_AGE_BY_ROLE: dict[str, int] = {
    "pup": 3,
    "juvenile": 12,
    "elder": ELDER_MIN_MOONS,
    "drown_sick": 3,
    "hunter_apprentice": 12,
    "medic_apprentice": 12,
    "scout_apprentice": 12,
    "diplomat_apprentice": 12,
    "caretaker_apprentice": 12,
    "forager_apprentice": 12,
}

REGISTER_AGE_CHOICES: list[tuple[str, int]] = [
    ("Pup: 3 moons", 3),
    ("Pup: 5 moons", 5),
    ("Juvenile: 12 moons", 12),
    ("Juvenile: 18 moons", 18),
    ("Young adult: 24 moons", 24),
    ("Adult: 36 moons", 36),
    ("Adult: 48 moons", 48),
    ("Elder: 60 moons", 60),
    ("Elder: 72 moons", 72),
]


def default_age_for_role(role: str) -> int:
    return DEFAULT_AGE_BY_ROLE.get(role, 24)


def resolve_register_age(role: str, age_months: int | None) -> int:
    """pick starting moons for registration; elder role requires elder age."""
    role = role if role in ROLE_PROFICIENCIES else "hunter"
    months = age_months if age_months is not None else default_age_for_role(role)
    months = max(0, min(MAX_WOLF_AGE_MOONS, int(months)))
    if role == "elder" and months < ELDER_MIN_MOONS:
        months = ELDER_MIN_MOONS
    return months


def stage_for_age(age_moons: int) -> str:
    """life stage label: pup, juvenile, adult, or elder (by age only)."""
    if age_moons < PUP_MAX_MOONS:
        return "pup"
    if age_moons < JUVENILE_MAX_MOONS:
        return "juvenile"
    if age_moons < ELDER_MIN_MOONS:
        return "adult"
    return "elder"


def stage_label(stage: str) -> str:
    return {
        "pup": "pup",
        "juvenile": "juvenile",
        "adult": "adult",
        "elder": "elder",
    }.get(stage, stage.title())


def format_wolf_age(age_moons: int) -> str:
    age_moons = max(0, int(age_moons))
    return f"{age_moons} moon{'s' if age_moons != 1 else ''}"


def sync_role_to_age(age_moons: int, role: str) -> str:
    """pick a valid wolf_role for the given age and requested role."""
    role = role if role in ROLE_PROFICIENCIES else "hunter"
    if role in AGE_OVERRIDE_ROLES:
        return role

    stage = stage_for_age(age_moons)

    if stage == "pup":
        return PUP_ROLE

    if stage == "juvenile":
        if role == PUP_ROLE:
            return JUVENILE_ROLE
        if role == "elder":
            return JUVENILE_ROLE
        if role in APPRENTICE_ROLES:
            return role
        if role in ADULT_ROLES:
            return JUVENILE_ROLE
        return role

    if role == PUP_ROLE:
        return JUVENILE_ROLE
    return role


def proficiencies_for_role(role: str) -> str:
    return json.dumps(list(ROLE_PROFICIENCIES.get(role, ())))


def check_age_milestones(old_age: int, new_age: int, current_role: str) -> list[str]:
    """Return narrative lines for thresholds crossed (may imply role change)."""
    notes: list[str] = []
    if old_age < PUP_MAX_MOONS <= new_age and current_role == PUP_ROLE:
        notes.append(
            f"**naming day**; at **{PUP_MAX_MOONS} moons** you are no longer a pup. "
            f"role set to **{ROLE_LABELS[JUVENILE_ROLE]}**. "
            "set attraction with **`/setsexuality`** when you are ready."
        )
    if old_age < JUVENILE_MAX_MOONS <= new_age and current_role == JUVENILE_ROLE:
        notes.append(
            f"at **{format_wolf_age(JUVENILE_MAX_MOONS)}** you leave juvenile life; "
            "earn an adult role through role quests and `/role action:event`."
        )
    if old_age < ELDER_MIN_MOONS <= new_age:
        notes.append(
            f"**long in the tooth**; at **{format_wolf_age(ELDER_MIN_MOONS)}** the pack counts you "
            "among the **elders**."
        )
    if old_age < MAX_WOLF_AGE_MOONS <= new_age:
        notes.append(
            f"**ancient**; at **{format_wolf_age(MAX_WOLF_AGE_MOONS)}** the seasons finally catch up. "
            "You pass peacefully of old age this sunrise."
        )
    return notes


def apply_old_age_deaths_on_rollover(
    conn,
    *,
    guild_id: int | None = None,
    day: int | None = None,
) -> list[dict]:
    """Wolves at max age die peacefully of old age each sunrise."""
    import database as db

    rows = conn.execute(
        """
        SELECT id, discord_id, wolf_name, age_months
        FROM users
        WHERE condition NOT IN ('dead', 'dying')
          AND age_months >= ?
        """,
        (MAX_WOLF_AGE_MOONS,),
    ).fetchall()
    deaths: list[dict] = []
    for row in rows:
        grief = db.mark_wolf_dead(
            row["id"],
            f"old age ({row['age_months']} moons)",
            conn=conn,
            guild_id=guild_id,
            day=day,
        )
        deaths.append(
            {
                "wolf_name": row["wolf_name"],
                "discord_id": row["discord_id"],
                "cause": f"old age ({row['age_months']} moons)",
                "mate_grief": grief,
            }
        )
    return deaths


def role_after_milestones(new_age: int, current_role: str) -> str:
    """apply automatic role promotions from aging."""
    role = current_role if current_role in ROLE_PROFICIENCIES else "hunter"
    if role == PUP_ROLE and new_age >= PUP_MAX_MOONS:
        return JUVENILE_ROLE
    return role
