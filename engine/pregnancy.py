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


def pregnancy_hunt_multiplier(user, day: int) -> tuple[float, str]:
    """Reduces hunt/fish/scavenge yield during pregnancy; gestation burns energy."""
    if not user or not int(user["is_pregnant"] if "is_pregnant" in user.keys() else 0):
        return 1.0, ""
    elapsed = pregnancy_elapsed(user, day)
    if elapsed <= 0:
        return 1.0, ""
    if elapsed >= GESTATION_DAYS - LATE_PREGNANCY_SUNRISES:
        # final third no longer blocked; heavy with pup the hunt barely works,
        # and pushing it risks the litter (see engine.strenuous_strain).
        return 0.65, "late pregnancy; heavy with pup, the hunt barely works (**−35%**) and risks the litter."
    if elapsed >= GESTATION_DAYS // 2:
        return 0.80, "mid-to-late pregnancy; carrying a litter slows the hunt (**−20%**)."
    return 0.90, "early pregnancy; the extra weight is already felt (**−10%**)."


