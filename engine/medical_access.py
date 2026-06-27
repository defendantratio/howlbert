"""Cross-pack medical treatment gates (rival standing)."""

from __future__ import annotations

import database as db

from config import (
    CROSS_PACK_STABILIZE_FAIL_STANDING,
    CROSS_PACK_STABILIZE_SUCCESS_STANDING,
    STABILIZE_LAY_FAIL_STANDING,
    STABILIZE_LAY_SUCCESS_STANDING,
    STABILIZE_MEDIC_FAIL_STANDING,
    STABILIZE_MEDIC_SUCCESS_STANDING,
)
from engine.pack_relations import HOSTILE_STANDING_THRESHOLD
from engine.role_features import has_any_role, is_full_medic


def _medic_is_neutral_healer(surgeon) -> bool:
    """Full Medics and apprentices may treat any pack; healers are neutral."""
    return is_full_medic(surgeon) or has_any_role(surgeon, "medic_apprentice")


def _pack_id(row) -> int:
    if not row or "pack_id" not in row.keys() or not row["pack_id"]:
        return 0
    return int(row["pack_id"])


def is_cross_pack_heal(healer, patient) -> bool:
    """true when healer and patient belong to different packs."""
    if not healer or not patient or healer["id"] == patient["id"]:
        return False
    healer_pack = _pack_id(healer)
    patient_pack = _pack_id(patient)
    return bool(healer_pack and patient_pack and healer_pack != patient_pack)


def is_same_pack_heal(healer, patient) -> bool:
    """True when healer and patient share a pack."""
    if not healer or not patient or healer["id"] == patient["id"]:
        return False
    healer_pack = _pack_id(healer)
    patient_pack = _pack_id(patient)
    return bool(healer_pack and patient_pack and healer_pack == patient_pack)


def _stabilize_wolf_standing_delta(healer, *, success: bool) -> int:
    if _medic_is_neutral_healer(healer):
        return (
            STABILIZE_MEDIC_SUCCESS_STANDING
            if success
            else STABILIZE_MEDIC_FAIL_STANDING
        )
    return STABILIZE_LAY_SUCCESS_STANDING if success else STABILIZE_LAY_FAIL_STANDING


def apply_cross_pack_stabilize_standing(
    healer,
    patient,
    guild_id: int,
    *,
    success: bool,
) -> str:
    """Raise or lower pack standing after cross-pack emergency stabilize."""
    if not guild_id or not is_cross_pack_heal(healer, patient):
        return ""
    healer_pack = _pack_id(healer)
    patient_pack = _pack_id(patient)
    delta = (
        CROSS_PACK_STABILIZE_SUCCESS_STANDING
        if success
        else CROSS_PACK_STABILIZE_FAIL_STANDING
    )
    new_standing = db.adjust_pack_relation(guild_id, healer_pack, patient_pack, delta)
    other = db.get_pack(patient_pack)
    name = other["name"] if other else "their den"
    outcome = "life saved" if success else "failed attempt"
    return (
        f"\n\n_cross-pack stabilize ({outcome}): **{name}** standing "
        f"**{delta:+d}** (now **{new_standing}/10**)._"
    )


def apply_same_pack_stabilize_standing(healer, patient, *, success: bool) -> str:
    """Raise or lower the healer's personal standing after same-pack emergency stabilize."""
    if not is_same_pack_heal(healer, patient):
        return ""
    delta = _stabilize_wolf_standing_delta(healer, success=success)
    kick = db.adjust_wolf_standing_by_id(healer["id"], delta)
    user = db.get_user_by_id(healer["id"])
    standing = int(user["standing"]) if user else "?"
    lay = not _medic_is_neutral_healer(healer)
    role = "lay healer" if lay else "medic"
    outcome = "packmate saved" if success else "failed attempt"
    note = (
        f"\n\n_stabilize ({outcome}, {role}): your standing "
        f"**{delta:+d}** (now **{standing}**)._"
    )
    if kick == "kicked":
        note += " You were **cast out** of the pack."
    return note


def apply_stabilize_standing(
    healer,
    patient,
    guild_id: int | None,
    *,
    success: bool,
) -> str:
    """Apply pack-relation or personal standing after emergency stabilize."""
    if guild_id and is_cross_pack_heal(healer, patient):
        return apply_cross_pack_stabilize_standing(
            healer, patient, guild_id, success=success
        )
    return apply_same_pack_stabilize_standing(healer, patient, success=success)


def can_medic_treat_cross_pack(
    surgeon,
    patient,
    guild_id: int,
    *,
    emergency_stabilize: bool = False,
) -> tuple[bool, str]:
    """
    Rival packs at standing ≤3 block routine care from non-medics.
    Medics and medic apprentices are neutral; cross-pack treat/surgery always allowed.
    Emergency stabilize (dying / 0 HP) is always permitted for anyone.
    """
    if emergency_stabilize:
        return True, ""
    if not surgeon or not patient:
        return False, "invalid healer or patient."
    if surgeon["id"] == patient["id"]:
        return True, ""
    if _medic_is_neutral_healer(surgeon):
        return True, ""
    surgeon_pack = int(surgeon["pack_id"]) if surgeon and "pack_id" in surgeon.keys() and surgeon["pack_id"] else 0
    patient_pack = int(patient["pack_id"]) if patient and "pack_id" in patient.keys() and patient["pack_id"] else 0
    if not surgeon_pack or not patient_pack or surgeon_pack == patient_pack:
        return True, ""
    standing = db.get_pack_relation(guild_id, surgeon_pack, patient_pack)
    if standing > HOSTILE_STANDING_THRESHOLD:
        return True, ""
    other = db.get_pack(patient_pack)
    name = other["name"] if other else "that den"
    return (
        False,
        f"**{name}** standing is **{standing}/10**; hostile packs won't accept "
        f"foreign care except from **medics** or **emergency stabilize**.",
    )
