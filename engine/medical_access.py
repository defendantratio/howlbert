"""Cross-pack medical treatment gates (rival standing)."""

from __future__ import annotations

import database as db

from engine.pack_relations import HOSTILE_STANDING_THRESHOLD


def can_medic_treat_cross_pack(
    surgeon,
    patient,
    guild_id: int,
    *,
    emergency_stabilize: bool = False,
) -> tuple[bool, str]:
    """
    Rival packs at standing ≤3 may not receive routine care from foreign Medics.
    Emergency stabilize (dying / 0 HP) is always permitted.
    """
    if emergency_stabilize:
        return True, ""
    if not surgeon or not patient:
        return False, "Invalid healer or patient."
    if surgeon["id"] == patient["id"]:
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
        f"foreign Medics except **emergency stabilize**.",
    )
