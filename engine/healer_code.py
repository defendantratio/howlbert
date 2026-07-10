# healer_code.py
"""Medic / healer vows: RP law with standing loss and exile when caught or scandalous."""

from __future__ import annotations

import random

import database as db
from config import (
    MEDIC_MATE_CATCH_CHANCE,
    MEDIC_MATE_CAUGHT_STANDING,
    MEDIC_MATE_CAUGHT_TEXT,
    MEDIC_NEUTRAL_STANDING,
    MEDIC_PUP_SCANDAL_STANDING,
    MEDIC_PUP_SCANDAL_TEXT,
)
from engine.role_features import is_full_medic

HEALER_VIOLATION_REMINDER = (
    "_The **Healer's Code** forbids mates and pups: if the den learns, you lose standing; "
    "pups may be cast out._"
)


def healer_vow_reminder(user) -> str | None:
    if is_full_medic(user):
        return HEALER_VIOLATION_REMINDER
    return None


def roll_medic_violation_caught() -> bool:
    return random.random() < MEDIC_MATE_CATCH_CHANCE


def pick_medic_caught_flavor() -> str:
    return random.choice(MEDIC_MATE_CAUGHT_TEXT)


def pick_medic_pup_scandal_flavor() -> str:
    return random.choice(MEDIC_PUP_SCANDAL_TEXT)


def medic_dependents(medic_id: int) -> list:
    """biological offspring and adopted youth tied to this medic."""
    bio = db.get_lineage_children_for_wolf(medic_id, limit=20)
    adopted = db.get_adopted_youth_for_parent(medic_id)
    seen: set[int] = set()
    out = []
    for row in list(bio) + list(adopted):
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        out.append(row)
    return out


def _exile_wolf(wolf_id: int) -> bool:
    """cast wolf out of their great pack (loner). returns true if they had a pack."""
    wolf = db.get_user_by_id(wolf_id)
    if not wolf or not wolf["pack_id"]:
        return False
    with db.get_db() as conn:
        db._expel_wolf_from_pack_conn(conn, wolf_id, reset_standing=False)
    return True


def _exile_pups(pup_ids: list[int]) -> list[str]:
    lines: list[str] = []
    for pup_id in pup_ids:
        pup = db.get_user_by_id(pup_id)
        if not pup:
            continue
        if _exile_wolf(pup_id):
            lines.append(
                f"**{pup['wolf_name']}** is cast out: a healer's pup cannot stay in the den."
            )
        with db.get_db() as conn:
            conn.execute(
                """
                UPDATE users
                SET adopt_parent_1_id = NULL, adopt_parent_2_id = NULL
                WHERE id = ?
                """,
                (pup_id,),
            )
    return lines


def process_medic_violation(
    medic,
    *,
    violation: str,
    new_pup_ids: list[int] | None = None,
    partner=None,
) -> tuple[list[str], str | None]:
    """
    Apply healer-code consequences.
    violation: court | mate | birth | adopt
    Returns (embed lines, expulsion note for actor).
    """
    if not is_full_medic(medic):
        return [], None

    public_scandal = violation in ("birth", "adopt")
    if not public_scandal and not roll_medic_violation_caught():
        return [], None

    lines: list[str] = []
    penalty = (
        MEDIC_PUP_SCANDAL_STANDING if public_scandal else MEDIC_MATE_CAUGHT_STANDING
    )
    flavor = (
        pick_medic_pup_scandal_flavor() if public_scandal else pick_medic_caught_flavor()
    )
    label = {
        "court": "courtship",
        "mate": "mating",
        "birth": "bearing pups",
        "adopt": "adoption",
    }.get(violation, violation)

    lines.append(
        f"**healer's code broken ({label}):** {flavor}\n"
        f"standing **{penalty}** for **{medic['wolf_name']}**."
    )

    kick = db.adjust_wolf_standing_by_id(medic["id"], penalty)
    expulsion_note = None

    pup_ids: set[int] = set(new_pup_ids or [])
    for dep in medic_dependents(medic["id"]):
        pup_ids.add(dep["id"])

    if pup_ids:
        lines.extend(_exile_pups(list(pup_ids)))

    if public_scandal:
        if _exile_wolf(medic["id"]):
            expulsion_note = (
                f"**{medic['wolf_name']}** is **exiled**: a pack healer cannot keep pups in the den."
            )
            lines.append(expulsion_note)
    elif kick == "kicked":
        expulsion_note = "you were **cast out** of the pack."
        lines.append(expulsion_note)
    elif kick == "broken_rite":
        expulsion_note = "the **rite of the broken canine** awaits your alpha."
        lines.append(expulsion_note)

    if partner and is_full_medic(partner) and partner["id"] != medic["id"]:
        pass  # caller handles both medics separately

    return lines, expulsion_note


def apply_medic_neutrality_violated(attacker_discord_id: int, medic) -> str:
    """Standing penalty for hitting or stealing from a neutral medic. Returns a note line."""
    kick = db.adjust_wolf_standing(attacker_discord_id, MEDIC_NEUTRAL_STANDING)
    note = (
        f"violated **healer's neutrality**; the den does not forgive striking the healer; "
        f"standing **{MEDIC_NEUTRAL_STANDING}**"
    )
    if kick == "kicked":
        note += "; **cast out**"
    return note


def apply_medic_court_caught(user, target) -> list[str]:
    """after a successful court by or with a medic."""
    lines: list[str] = []
    for medic, other in ((user, target), (target, user)):
        if not is_full_medic(medic):
            continue
        vlines, _ = process_medic_violation(medic, violation="court", partner=other)
        lines.extend(vlines)
    return lines


def apply_medic_mate_caught(user, partner) -> tuple[str | None, list[str]]:
    lines: list[str] = []
    expulsion_note = None
    seen: set[int] = set()
    for medic in (user, partner):
        if not is_full_medic(medic) or medic["id"] in seen:
            continue
        seen.add(medic["id"])
        other = partner if medic["id"] == user["id"] else user
        vlines, note = process_medic_violation(medic, violation="mate", partner=other)
        lines.extend(vlines)
        if note:
            expulsion_note = note
    return expulsion_note, lines


def apply_medic_birth_scandal(mother, father, born_pup_ids: list[int]) -> list[str]:
    lines: list[str] = []
    seen: set[int] = set()
    for parent in (mother, father):
        if not parent or not is_full_medic(parent) or parent["id"] in seen:
            continue
        seen.add(parent["id"])
        other = father if parent["id"] == mother["id"] else mother
        vlines, _ = process_medic_violation(
            parent,
            violation="birth",
            new_pup_ids=born_pup_ids,
            partner=other,
        )
        lines.extend(vlines)
    return lines


def apply_medic_adopt_scandal(adopter1, adopter2, youth) -> list[str]:
    lines: list[str] = []
    seen: set[int] = set()
    for adopter in (adopter1, adopter2):
        if not is_full_medic(adopter) or adopter["id"] in seen:
            continue
        seen.add(adopter["id"])
        other = adopter2 if adopter["id"] == adopter1["id"] else adopter1
        vlines, _ = process_medic_violation(
            adopter,
            violation="adopt",
            new_pup_ids=[youth["id"]],
            partner=other,
        )
        lines.extend(vlines)
    return lines