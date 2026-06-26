"""Apply canonical lore bonds when both wolves exist in the database."""

from __future__ import annotations

import logging

import database as db
from engine.canonical_bonds_data import CANONICAL_BONDS

logger = logging.getLogger("howlbert")


def apply_canonical_bond(spec: dict, *, refresh_notes: bool = True) -> bool:
    """Create or upgrade a canonical bond. Returns True if a new row was inserted."""
    a = db.get_wolf_by_name(spec["a"])
    b = db.get_wolf_by_name(spec["b"])
    if not a or not b:
        return False
    if int(a["id"]) == int(b["id"]):
        return False

    bond_type = spec["type"]
    strength = int(spec.get("strength", 40))
    note = (spec.get("note") or "").strip()[:120]
    existing = db.get_bond(int(a["id"]), int(b["id"]), bond_type)

    if existing:
        new_strength = max(int(existing["strength"]), strength)
        old_note = (existing["note"] or "").strip() if "note" in existing.keys() else ""
        new_note = note if (refresh_notes and note) else old_note
        if new_strength != int(existing["strength"]) or new_note != old_note:
            db.set_bond(
                int(a["id"]),
                int(b["id"]),
                bond_type,
                strength=new_strength,
                note=new_note,
                day=int(existing["created_day"] or 0),
            )
        return False

    db.set_bond(
        int(a["id"]),
        int(b["id"]),
        bond_type,
        strength=strength,
        note=note,
        day=0,
    )
    return True


def apply_canonical_bonds_for_wolf(wolf_id: int, *, refresh_notes: bool = True) -> int:
    """Apply every canonical bond touching this wolf. Returns count of new bonds."""
    wolf = db.get_user_by_id(wolf_id)
    if not wolf:
        return 0
    name = wolf["wolf_name"]
    added = 0
    for spec in CANONICAL_BONDS:
        if spec["a"].lower() != name.lower() and spec["b"].lower() != name.lower():
            continue
        if apply_canonical_bond(spec, refresh_notes=refresh_notes):
            added += 1
    return added


def backfill_all_canonical_bonds(*, refresh_notes: bool = True) -> int:
    """Apply all canonical bonds for registered pairs. Returns new bond count."""
    added = 0
    for spec in CANONICAL_BONDS:
        try:
            if apply_canonical_bond(spec, refresh_notes=refresh_notes):
                added += 1
        except Exception:
            logger.exception(
                "Canonical bond failed: %s ↔ %s (%s)",
                spec["a"],
                spec["b"],
                spec["type"],
            )
    return added
