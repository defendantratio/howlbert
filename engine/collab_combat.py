"""Pack party enrollment in combat and assist bonuses."""

from __future__ import annotations


import database as db

COLLAB_ASSIST_PER_ALLY = 1
COLLAB_ASSIST_CAP = 3


def is_collab_encounter(enc) -> bool:
    if not enc:
        return False
    hunt = int(enc["collab_hunt_id"]) if "collab_hunt_id" in enc.keys() and enc["collab_hunt_id"] else 0
    patrol = int(enc["collab_patrol_id"]) if "collab_patrol_id" in enc.keys() and enc["collab_patrol_id"] else 0
    return bool(hunt or patrol)


def collab_assist_bonus(encounter_id: int, attacker_fighter_id: int) -> int:
    """+1 attack per other living packmate in a collab fight (max +3)."""
    enc = db.get_encounter(encounter_id)
    if not is_collab_encounter(enc):
        return 0
    alive = [
        f
        for f in db.get_combat_fighters(encounter_id)
        if not f["npc_name"] and f["hp"] > 0
    ]
    allies = len(alive) - 1
    return min(COLLAB_ASSIST_CAP, max(0, allies)) * COLLAB_ASSIST_PER_ALLY


def enroll_collab_party_in_encounter(
    encounter_id: int,
    party_users: list,
    *,
    leader_wolf_id: int,
) -> int:
    """Add party wolves to an encounter and rebuild initiative. Returns wolves added."""
    existing = {
        f["wolf_id"]
        for f in db.get_combat_fighters(encounter_id)
        if f["wolf_id"]
    }
    added = 0
    for user in party_users:
        if user["id"] in existing:
            continue
        db.add_combat_fighter(
            encounter_id,
            discord_id=user["discord_id"],
            wolf_id=user["id"],
            hp=user["hp"],
            max_hp=user["max_hp"],
        )
        added += 1
    if added:
        db.rebuild_encounter_initiative(encounter_id)
    return added
