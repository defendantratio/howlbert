"""Two bonded lone wolves raise a den of their own; the end of the dispersal arc.

A founded den is a real pack row (shared pack_id: treasury, stash, collab hunts,
alpha) but keeps the founders' unaffiliated faction identity, so it does not
collide with the four canonical great-pack factions. The founder becomes alpha.
"""

from __future__ import annotations

import database as db
from config import NEW_PACK_FOUND_COST
from engine.pack_schism import SCHISM_BOND_THRESHOLD
from engine.role_features import is_loner_wolf


def _strong_bond(a_id: int, b_id: int) -> bool:
    for kind in ("romance", "friendship", "kin"):
        bond = db.get_bond(a_id, b_id, kind)
        if bond and int(bond["strength"]) >= SCHISM_BOND_THRESHOLD:
            return True
    return False


def found_pack(founder, partner, name: str) -> tuple[int | None, str | None]:
    """Validate and found a new den. Returns (new_pack_id, error)."""
    if not is_loner_wolf(founder):
        return None, "only a lone wolf (loner) can found a new pack; rogues and pack wolves cannot."
    if not partner:
        return None, "name a bonded partner to found the pack with."
    if int(partner["id"]) == int(founder["id"]):
        return None, "you need a second wolf to raise a den."
    if not is_loner_wolf(partner):
        return None, f"**{partner['wolf_name']}** must also be a lone wolf to found a pack with you."
    if not _strong_bond(founder["id"], partner["id"]):
        return None, (
            f"you must share a strong bond (**{SCHISM_BOND_THRESHOLD}+**) with "
            f"**{partner['wolf_name']}** to found a pack together; court, groom, and socialize first."
        )
    name = (name or "").strip()
    if not (2 <= len(name) <= 32):
        return None, "the pack name must be 2 to 32 characters."
    if int(founder["bones"]) < NEW_PACK_FOUND_COST or int(partner["bones"]) < NEW_PACK_FOUND_COST:
        return None, f"founding a den costs **{NEW_PACK_FOUND_COST}** bones from **each** founder."

    new_pack_id = db.create_pack(name, founder["id"])
    with db.get_db() as conn:
        conn.execute(
            "UPDATE users SET pack_id = ?, wolf_role = 'alpha' WHERE id = ?",
            (new_pack_id, founder["id"]),
        )
        conn.execute("UPDATE users SET pack_id = ? WHERE id = ?", (new_pack_id, partner["id"]))
        conn.execute("UPDATE packs SET pack_unity = 50 WHERE id = ?", (new_pack_id,))
    db.deduct_bones(founder["discord_id"], NEW_PACK_FOUND_COST)
    db.deduct_bones(partner["discord_id"], NEW_PACK_FOUND_COST)
    return new_pack_id, None
