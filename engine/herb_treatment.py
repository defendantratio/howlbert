# herb_treatment.py
"""Mechanical outcomes for compendium herbs via `/medic action:treat` (delegates to engine.herb_buffs)."""

from __future__ import annotations

from engine.herb_buffs import apply_supplemental_herb


def apply_flavor_herb(herb_key: str, user, *, day: int | None = None, outcome: str = "no_effect") -> dict | None:
    """Returns an action dict for treat handlers, or None."""
    if day is None:
        day = int(user["last_rest_day"]) if "last_rest_day" in user.keys() else 0
    return apply_supplemental_herb(herb_key, user, day=day, outcome=outcome)