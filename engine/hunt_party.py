"""Pack hunt party chemistry (Wolvden-style synergy and personality friction)."""

from __future__ import annotations

import random

import database as db

HUNT_ROLES = ("leader", "chaser", "flank", "scout", "blocker")
ROLE_FROM_WOLF_ROLE = {
    "hunter": "chaser",
    "scout": "scout",
    "sentinel": "blocker",
    "diplomat": "flank",
    "caretaker": "flank",
    "elder": "flank",
    "omega": "blocker",
}


def assign_hunt_role(wolf, existing_roles: list[str], *, is_leader: bool = False) -> str:
    if is_leader:
        return "leader"
    preferred = ROLE_FROM_WOLF_ROLE.get(
        db.row_val(wolf, "wolf_role"),
        "flank",
    )
    if preferred != "leader" and preferred not in existing_roles:
        return preferred
    for role in HUNT_ROLES:
        if role != "leader" and role not in existing_roles:
            return role
    return "flank"


def hunt_role_synergy(members: list) -> tuple[int, str]:
    """bonus when party fills distinct hunt roles."""
    roles = []
    for m in members:
        role = m["hunt_role"] if "hunt_role" in m.keys() and m["hunt_role"] else "flank"
        roles.append(role)
    unique = set(roles)
    if len(unique) >= 5:
        return 8, "_full five-role drive; every jaw has a job._"
    if {"chaser", "scout", "blocker"}.issubset(unique):
        return 5, "_chaser, scout, and blocker in place; coordinated drive **+5%**._"
    if len(unique) >= 3:
        return 3, "_roles spread; the line holds shape._"
    return 0, ""


def breeding_pair_hunt_bonus(users: list, *, season: str | None) -> tuple[int, str]:
    """a bonded male hunting beside his pregnant mate sharpens the drive (any season)."""
    if len(users) < 2:
        return 0, ""
    party_ids = {u["id"] for u in users}
    for wolf in users:
        sex = wolf["birth_sex"] if wolf and "birth_sex" in wolf.keys() else None
        if sex != "male":
            continue
        mate = db.get_bonded_mate(wolf)
        if not mate or not int(mate["is_pregnant"] if "is_pregnant" in mate.keys() else 0):
            continue
        if mate["id"] in party_ids:
            return 4, "_breeding pair on the line; the drive to provide sharpens the hunt._"
    return 0, ""


def collab_hunt_bond_modifiers(
    users: list, members: list | None = None, *, season: str | None = None
) -> tuple[int, str]:
    """
    Friendship adds payout bonus; heated rivalries may spark a mid-hunt fight.
    Returns (bonus_percent, flavor note).
    """
    if len(users) < 2:
        return 0, ""

    friendship_total = 0
    rivalry_pairs = 0
    heated_rivalry = False
    pairs = 0

    for i, a in enumerate(users):
        for b in users[i + 1 :]:
            pairs += 1
            friend = db.get_bond(a["id"], b["id"], "friendship")
            if friend:
                friendship_total += int(friend["strength"])
            rival = db.get_bond(a["id"], b["id"], "rivalry")
            if rival and int(rival["strength"]) >= 20:
                rivalry_pairs += 1
                if int(rival["strength"]) >= 60:
                    heated_rivalry = True

    if not pairs:
        return 0, ""

    bonus = 0
    if friendship_total >= 80:
        bonus = 8
    elif friendship_total >= 40:
        bonus = 4

    role_bonus, role_note = hunt_role_synergy(members or [])
    bonus += role_bonus
    pair_bonus, pair_note = breeding_pair_hunt_bonus(users, season=season)
    bonus += pair_bonus

    notes: list[str] = []
    if bonus:
        notes.append(f"pack chemistry **+{bonus}%** bones")
    if role_note:
        notes.append(role_note.strip("_"))
    if pair_note:
        notes.append(pair_note.strip("_"))
    if heated_rivalry and random.random() < 0.35:
        return -100, (
            "_mid-hunt snarl: a **heated rivalry** in the party scatters the quarry "
            "and leaves everyone empty-pawed._"
        )
    if rivalry_pairs and random.random() < 0.2:
        return max(bonus - 5, -15), (
            "_tension on the line; grudges slow the drive._"
            + (f" chemistry **+{bonus}%**." if bonus else "")
        )

    return bonus, notes[0] if notes else ""
