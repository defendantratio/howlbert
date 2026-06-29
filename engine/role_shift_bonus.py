"""First-action-of-sunrise bonuses by role."""

from __future__ import annotations

import database as db
from config import ROLE_SHIFT_HUNTER_MOOD, ROLE_SHIFT_MEDIC_STANDING, ROLE_SHIFT_SCOUT_MOOD
from engine.role_features import is_full_medic
from engine.role_privileges import is_hunter


def apply_first_hunt_bonus(user, day: int) -> str | None:
    from engine.role_privileges import hunts_used_today

    if not is_hunter(user):
        return None
    if hunts_used_today(user, day) != 1:
        return None
    new_mood = db.adjust_mood(user["id"], ROLE_SHIFT_HUNTER_MOOD)
    return f"hunter's opening chase; +{ROLE_SHIFT_HUNTER_MOOD} mood (now {new_mood})."


def apply_first_treat_bonus(user, treats_after: int) -> str | None:
    if treats_after != 1 or not is_full_medic(user):
        return None
    db.adjust_wolf_standing_by_id(user["id"], ROLE_SHIFT_MEDIC_STANDING)
    return f"medic's first treatment this sunrise; **+{ROLE_SHIFT_MEDIC_STANDING} standing**."


def apply_first_survey_bonus(user) -> str | None:
    if not user:
        return None
    new_mood = db.adjust_mood(user["id"], ROLE_SHIFT_SCOUT_MOOD)
    return f"scout's border sweep; **+{ROLE_SHIFT_SCOUT_MOOD} mood** (now **{new_mood}**)."
