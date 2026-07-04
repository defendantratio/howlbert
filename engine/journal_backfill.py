"""Backfill wolf journals from lore, lineage, bonds, deaths, and other stored gameplay."""

from __future__ import annotations

import logging

import database as db
from config import GREAT_PACKS, LONER_KEY, ROGUE_KEY
from engine.character_lore import parse_character_lore
from engine.wolf_journal import _pack_label

logger = logging.getLogger("howlbert")

_BOND_TYPE_LABELS = {
    "friendship": "friendship",
    "rivalry": "rivalry",
    "kin": "kinship",
    "mentor": "mentor bond",
}
_BOND_STRENGTH_FLOOR = 30


def sync_lore_journal_entries(wolf_id: int) -> None:
    """Refresh lore journal rows from the full character sheet (fixes truncated backfill)."""
    wolf = db.get_user_by_id(wolf_id)
    if not wolf:
        return
    lore = parse_character_lore(
        wolf["character_lore"] if "character_lore" in wolf.keys() else None
    )
    if not lore:
        return
    if lore.get("backstory"):
        db.upsert_wolf_journal_entry(
            wolf_id,
            "lore:backstory",
            f"_from the den records:_ {lore['backstory']}",
        )
    if lore.get("family_ties"):
        db.upsert_wolf_journal_entry(
            wolf_id,
            "lore:family",
            f"_family on file:_ {lore['family_ties']}",
        )


def _partner_name(wolf_id: int, row) -> str | None:
    if int(row["wolf_a_id"]) == wolf_id:
        other_id = int(row["wolf_b_id"])
    else:
        other_id = int(row["wolf_a_id"])
    other = db.get_user_by_id(other_id)
    return other["wolf_name"] if other else None


def sync_bond_journal_entries(wolf_id: int) -> None:
    """refresh bond/rivalry journal lines (including notes) from current gameplay bonds."""
    for bond in db.get_bonds_for_wolf(wolf_id):
        strength = int(bond["strength"]) if "strength" in bond.keys() else 0
        if strength < _BOND_STRENGTH_FLOOR:
            continue
        partner = _partner_name(wolf_id, bond)
        if not partner:
            continue
        btype = bond["bond_type"]
        label = _BOND_TYPE_LABELS.get(btype, btype)
        other_id = (
            int(bond["wolf_b_id"])
            if int(bond["wolf_a_id"]) == wolf_id
            else int(bond["wolf_a_id"])
        )
        note = (bond["note"] or "").strip() if "note" in bond.keys() else ""
        line = f"**{label.title()}** with **{partner}** (strength {strength})"
        if note:
            line += f"; _{note[:120]}_"
        day = int(bond["created_day"]) if bond["created_day"] else 0
        db.upsert_wolf_journal_entry(
            wolf_id, f"bond:{btype}:{other_id}", line, day=day
        )


def backfill_wolf_journal(wolf_id: int) -> int:
    """Add missing journal rows inferred from DB state. Returns count inserted."""
    wolf = db.get_user_by_id(wolf_id)
    if not wolf:
        return 0

    sync_lore_journal_entries(wolf_id)
    sync_bond_journal_entries(wolf_id)

    with db.get_db() as conn:
        conn.execute(
            """
            UPDATE wolf_journal_entries
            SET day = 0
            WHERE wolf_id = ? AND event_key = 'registered' AND day IS NULL
            """,
            (wolf_id,),
        )

    existing = db.get_wolf_journal_event_keys(wolf_id)
    added = 0
    wolf_name = wolf["wolf_name"]

    def put(key: str, summary: str, *, day: int | None = None, guild_id: int | None = None) -> None:
        nonlocal added
        if key in existing:
            return
        if db.add_wolf_journal_entry_if_new(wolf_id, key, summary, day=day, guild_id=guild_id):
            existing.add(key)
            added += 1

    lore = parse_character_lore(
        wolf["character_lore"] if "character_lore" in wolf.keys() else None
    )
    if lore:
        if lore.get("backstory"):
            put(
                "lore:backstory",
                f"_from the den records:_ {lore['backstory']}",
            )
        if lore.get("family_ties"):
            put(
                "lore:family",
                f"_family on file:_ {lore['family_ties']}",
            )

    is_pup = bool("is_born_pup" in wolf.keys() and wolf["is_born_pup"])
    mother_id = wolf["bio_parent_1_id"] if "bio_parent_1_id" in wolf.keys() else None
    father_id = wolf["bio_parent_2_id"] if "bio_parent_2_id" in wolf.keys() else None
    if is_pup or mother_id:
        mother = db.get_user_by_id(int(mother_id)) if mother_id else None
        father = db.get_user_by_id(int(father_id)) if father_id else None
        parents = " and ".join(
            p["wolf_name"] for p in (mother, father) if p
        ) or "the den"
        put("born", f"**{wolf_name}** was born to {parents}.")

    adopt_1 = wolf["adopt_parent_1_id"] if "adopt_parent_1_id" in wolf.keys() else None
    adopt_2 = wolf["adopt_parent_2_id"] if "adopt_parent_2_id" in wolf.keys() else None
    if adopt_1 or adopt_2:
        p1 = db.get_user_by_id(int(adopt_1)) if adopt_1 else None
        p2 = db.get_user_by_id(int(adopt_2)) if adopt_2 else None
        parents = " and ".join(p["wolf_name"] for p in (p1, p2) if p) or "the den"
        put("adopted", f"**{wolf_name}** was taken in by {parents}.")

    affiliation = wolf["great_pack"] if "great_pack" in wolf.keys() else None
    pack = _pack_label(affiliation)
    if "registered" not in existing:
        put("registered", f"joined the den as **{wolf_name}** ({pack}).", day=0)

    mate_id = wolf["bonded_mate_id"] if "bonded_mate_id" in wolf.keys() else None
    if mate_id and "bonded" not in existing:
        mate = db.get_user_by_id(int(mate_id))
        if mate:
            put("bonded", f"bonded with **{mate['wolf_name']}**.")

    if "blooded" not in existing and "has_blooding" in wolf.keys() and wolf["has_blooding"]:
        put("blooded", f"earned **blooding** on first kill; **{wolf_name}** is blooded.")

    for bond in db.get_bonds_for_wolf(wolf_id):
        strength = int(bond["strength"]) if "strength" in bond.keys() else 0
        if strength < _BOND_STRENGTH_FLOOR:
            continue
        partner = _partner_name(wolf_id, bond)
        if not partner:
            continue
        btype = bond["bond_type"]
        other_id = (
            int(bond["wolf_b_id"])
            if int(bond["wolf_a_id"]) == wolf_id
            else int(bond["wolf_a_id"])
        )
        if f"bond:{btype}:{other_id}" in existing:
            continue
        label = _BOND_TYPE_LABELS.get(btype, btype)
        note = (bond["note"] or "").strip() if "note" in bond.keys() else ""
        line = f"**{label.title()}** with **{partner}** (strength {strength})"
        if note:
            line += f"; _{note[:120]}_"
        day = int(bond["created_day"]) if bond["created_day"] else 0
        put(f"bond:{btype}:{other_id}", line, day=day)

    with db.get_db() as conn:
        courts = conn.execute(
            """
            SELECT target_wolf_id, day_number FROM court_history
            WHERE courter_wolf_id = ?
            ORDER BY day_number ASC
            """,
            (wolf_id,),
        ).fetchall()
    for row in courts:
        target = db.get_user_by_id(int(row["target_wolf_id"]))
        if not target:
            continue
        day = int(row["day_number"])
        put(
            f"court:{row['target_wolf_id']}:{day}",
            f"courted **{target['wolf_name']}**.",
            day=day,
        )

    family = db.get_wolf_family(wolf_id)
    if family:
        role_row = None
        with db.get_db() as conn:
            role_row = conn.execute(
                """
                SELECT role, joined_day FROM wolf_family_members
                WHERE family_id = ? AND wolf_id = ?
                """,
                (family["id"], wolf_id),
            ).fetchone()
        role = role_row["role"] if role_row else "member"
        day = int(role_row["joined_day"]) if role_row and role_row["joined_day"] else int(
            family["created_day"] or 0
        ) or None
        if role == "founder":
            line = f"founded found family **{family['name']}**."
        else:
            line = f"joined found family **{family['name']}** as {role}."
        put(f"family:{family['id']}", line, day=day)

    if "died" not in existing:
        with db.get_db() as conn:
            deaths = conn.execute(
                """
                SELECT id, cause, day, guild_id FROM wolf_death_log
                WHERE wolf_id = ?
                ORDER BY id ASC
                """,
                (wolf_id,),
            ).fetchall()

        if deaths:
            for row in deaths:
                cause = row["cause"] or "unknown"
                day = int(row["day"]) if row["day"] is not None else None
                gid = int(row["guild_id"]) if row["guild_id"] else None
                key = "died" if len(deaths) == 1 else f"died:{row['id']}"
                put(
                    key,
                    f"**{wolf_name}** died ({cause}).",
                    day=day,
                    guild_id=gid,
                )
        elif wolf["condition"] == "dead":
            cause = (
                wolf["cause_of_death"] if "cause_of_death" in wolf.keys() else None
            ) or "unknown"
            day = int(wolf["death_day"]) if "death_day" in wolf.keys() and wolf["death_day"] else None
            put("died", f"**{wolf_name}** died ({cause}).", day=day)

    return added


def backfill_all_wolf_journals() -> int:
    """backfill every wolf; returns total entries inserted."""
    total = 0
    with db.get_db() as conn:
        wolf_ids = [int(r["id"]) for r in conn.execute("SELECT id FROM users").fetchall()]
    for wid in wolf_ids:
        try:
            total += backfill_wolf_journal(wid)
        except Exception:
            logger.exception("Journal backfill failed for wolf_id=%s", wid)
    return total
