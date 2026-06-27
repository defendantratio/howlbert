"""Pregnancy activity gates (Wolvden-style den rest in late gestation)."""

from __future__ import annotations

from engine.family import GESTATION_DAYS

# Final third of gestation: no strenuous field work (analog to nested den rest).
LATE_PREGNANCY_SUNRISES = max(14, GESTATION_DAYS // 3)

STRENUOUS_ACTIONS = frozenset(
    {"hunt", "combat", "crime", "patrol", "explore", "survey", "trail", "scavenge", "track", "fishing"}
)


def pregnancy_elapsed(user, day: int) -> int:
    if not user or not int(user["is_pregnant"] if "is_pregnant" in user.keys() else 0):
        return 0
    start = int(user["pregnancy_start_day"] if "pregnancy_start_day" in user.keys() else 0)
    if start <= 0 or day <= 0:
        return 0
    return max(0, day - start)


def in_late_pregnancy(user, day: int) -> bool:
    elapsed = pregnancy_elapsed(user, day)
    if elapsed <= 0:
        return False
    return elapsed >= GESTATION_DAYS - LATE_PREGNANCY_SUNRISES


def pregnancy_activity_block(user, action: str, day: int) -> str | None:
    """Block strenuous work for pregnant females in the final third of gestation."""
    if action not in STRENUOUS_ACTIONS:
        return None
    sex = user["birth_sex"] if user and "birth_sex" in user.keys() else None
    if sex != "female":
        return None
    if not in_late_pregnancy(user, day):
        return None
    elapsed = pregnancy_elapsed(user, day)
    remaining = max(0, GESTATION_DAYS - elapsed)
    name = user["wolf_name"] if user and "wolf_name" in user.keys() else "She"
    return (
        f"**{name}** is in late pregnancy (**{remaining}** sunrise(s) until birth). "
        "rest in the den; strenuous work risks the litter. "
        "Use `/pupcare action:pregnancy` to check gestation."
    )
