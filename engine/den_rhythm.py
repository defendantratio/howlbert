"""Pack-wide sunrise rhythm and caught cross-pack scandal fallout."""

from __future__ import annotations

import database as db
from config import (
    BOND_RELATION_FRIENDLY_FLOOR,
    BOND_RELATION_PRESSURE_DELTA,
    BOND_RELATION_PRESSURE_INTERVAL,
    BOND_SCANDAL_STRAIN_DELTA,
    DEN_RHYTHM_ACTIVITY_RATIO,
    DEN_RHYTHM_MIN_WOLVES,
    DEN_RHYTHM_UNITY_GAIN,
)

_BOND_TYPES = ("friendship", "rivalry", "kin", "mentor")


def apply_den_rhythm_unity(guild_id: int, completed_day: int) -> list[str]:
    """If enough packmates hunted, howled, and socialized on completed_day, +unity."""
    notes: list[str] = []
    with db.get_db() as conn:
        packs = conn.execute(
            "SELECT DISTINCT pack_id FROM users WHERE pack_id IS NOT NULL"
        ).fetchall()
        for prow in packs:
            pack_id = int(prow["pack_id"])
            members = conn.execute(
                "SELECT id, wolf_name, last_hunt_day, last_howl_day, last_socialize_day "
                "FROM users WHERE pack_id = ?",
                (pack_id,),
            ).fetchall()
            if len(members) < DEN_RHYTHM_MIN_WOLVES:
                continue
            triad = sum(
                1
                for m in members
                if int(m["last_hunt_day"]) >= completed_day
                and int(m["last_howl_day"]) >= completed_day
                and int(m["last_socialize_day"]) >= completed_day
            )
            if triad / len(members) < DEN_RHYTHM_ACTIVITY_RATIO:
                continue
            outcome = db.adjust_pack_unity(pack_id, DEN_RHYTHM_UNITY_GAIN)
            pack = db.get_pack(pack_id)
            label = pack["name"] if pack else "Pack"
            note = (
                f"**{label}** ran the full den rhythm (**{triad}/{len(members)}** wolves: "
                f"hunt · howl · socialize); **+{DEN_RHYTHM_UNITY_GAIN} unity**."
            )
            if outcome == "dissolved":
                note += " _(den fractured)_"
            notes.append(note)
    return notes


def _strain_bonds_between(wolf_a_id: int, wolf_b_id: int, day: int) -> list[str]:
    strained: list[str] = []
    for bond_type in _BOND_TYPES:
        row = db.adjust_bond_strength(
            wolf_a_id,
            wolf_b_id,
            bond_type,
            BOND_SCANDAL_STRAIN_DELTA,
            day=day,
        )
        if row:
            strained.append(f"{bond_type} **{int(row['strength'])}/100**")
    return strained


def apply_bond_relation_pressure(guild_id: int, day: int) -> list[str]:
    """after a *caught* cross-pack mating scandal, drag pack relations and bond strength."""
    notes: list[str] = []
    for row in db.list_cross_pack_scandals(guild_id):
        pa, pb = int(row["pack_a_id"]), int(row["pack_b_id"])
        standing = db.get_pack_relation(guild_id, pa, pb)
        if standing >= BOND_RELATION_FRIENDLY_FLOOR:
            db.clear_cross_pack_scandal(int(row["id"]))
            continue
        last = db.get_bond_relation_cooldown(guild_id, pa, pb)
        if day - last < BOND_RELATION_PRESSURE_INTERVAL:
            continue
        new_standing = db.adjust_pack_relation(
            guild_id, pa, pb, BOND_RELATION_PRESSURE_DELTA
        )
        db.set_bond_relation_cooldown(guild_id, pa, pb, day)
        wolf_a, wolf_b = int(row["wolf_a_id"]), int(row["wolf_b_id"])
        strained = _strain_bonds_between(wolf_a, wolf_b, day)
        a = db.get_user_by_id(wolf_a)
        b = db.get_user_by_id(wolf_b)
        na = a["wolf_name"] if a else "Wolf"
        nb = b["wolf_name"] if b else "Wolf"
        pack_a = db.get_pack(pa)
        pack_b = db.get_pack(pb)
        den_a = pack_a["name"] if pack_a else "Pack"
        den_b = pack_b["name"] if pack_b else "Pack"
        bond_note = ""
        if strained:
            bond_note = f" bond strain: {', '.join(strained)}."
        notes.append(
            f"cross-pack scandal (**{na}** ↔ **{nb}**): "
            f"**{den_a}**/**{den_b}** standing **{BOND_RELATION_PRESSURE_DELTA}** "
            f"(now **{new_standing}/10**).{bond_note}"
        )
    return notes
