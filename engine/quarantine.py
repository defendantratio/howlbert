"""Sick-den isolation; blocks spread and most pack activities."""

from __future__ import annotations

from engine.pack_leadership import is_pack_officer
from engine.role_privileges import is_medic


def is_quarantined(user) -> bool:
    if not user:
        return False
    return bool(int(user["quarantined"])) if "quarantined" in user.keys() else False


def can_manage_quarantine(actor, pack) -> bool:
    """Medics, Alphas, and Advisors may isolate or release packmates."""
    if not actor or not pack:
        return False
    if actor["pack_id"] != pack["id"]:
        return False
    return is_medic(actor) or is_pack_officer(actor, pack)


def quarantine_activity_block(user) -> str | None:
    if not is_quarantined(user):
        return None
    return (
        "**Quarantined**; you stay in the sick den. No hunting, grooming, or mingling "
        "until a **Medic**, **Alpha**, or **Advisor** releases you with "
        "`/medic action:quarantine release:true`."
    )
