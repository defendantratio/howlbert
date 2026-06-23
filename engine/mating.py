"""Shared mate resolution after consent."""

from __future__ import annotations

import database as db
from config import MATE_MOOD_GAIN
from engine.attraction import conception_parents, mate_pairing
from engine.family import GESTATION_DAYS, conception_check
from engine.infractions import apply_mate_infractions
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR


def mating_embed_title(body: str, *, hard_fail: bool) -> str:
    if hard_fail:
        return "Mating Failed"
    lower = body.lower()
    if "form a bond" in lower or ("bond" in lower and "conception roll" not in lower):
        return "Mating Bond"
    return "Mating"


def execute_mating(
    user,
    partner_user,
    *,
    day_number: int,
) -> tuple[bool, str, int, bool]:
    """
    Returns (completed, message, embed_color, hard_fail).
    hard_fail True means the attempt could not proceed (not a failed conception roll).
    """
    from engine.role_restrictions import young_wolf_block

    for wolf in (user, partner_user):
        block = young_wolf_block(wolf, action="mate")
        if block:
            return False, block, ERROR_COLOR, True

    mode, err = mate_pairing(user, partner_user)
    if mode == "error":
        return False, err or "Incompatible pairing.", ERROR_COLOR, True

    expulsion_note, caught_lines = apply_mate_infractions(user, partner_user)

    def mood_line() -> str:
        your_mood = db.adjust_mood(user["id"], MATE_MOOD_GAIN)
        their_mood = db.adjust_mood(partner_user["id"], MATE_MOOD_GAIN)
        return (
            f"\n**+{MATE_MOOD_GAIN} mood** each "
            f"(you: **{your_mood}**, them: **{their_mood}**)."
        )

    def caught_suffix() -> str:
        if not caught_lines:
            return ""
        body = "\n\n" + "\n\n".join(caught_lines)
        if expulsion_note:
            body += f"\n{expulsion_note}"
        return body

    if mode == "bond":
        db.set_bonded_mates(user["id"], partner_user["id"])
        if user["pack_id"] and user["pack_id"] == partner_user["pack_id"]:
            db.adjust_pack_unity(user["pack_id"], 1)
        body = (
            f"**{user['wolf_name']}** and **{partner_user['wolf_name']}** mate and form a bond.\n"
            "No pregnancy; biological pups require a female and male birth sex."
            + mood_line()
        )
        from engine.disease_contract import try_mating_disease_spread

        spread_notes = []
        for a, b in ((user, partner_user), (partner_user, user)):
            note = try_mating_disease_spread(a, b)
            if note:
                spread_notes.append(note)
        if spread_notes:
            body += "\n\n" + "\n".join(spread_notes)
        if caught_lines:
            body += caught_suffix()
        return True, body, SUCCESS_COLOR, False

    female, male = conception_parents(user, partner_user)
    if not female or not male:
        return False, "Cannot conceive.", ERROR_COLOR, True

    from engine.disease_contract import try_mating_disease_spread
    from engine.diseases import blocks_conception, parse_disease

    spread_notes: list[str] = []
    for a, b in ((user, partner_user), (partner_user, user)):
        note = try_mating_disease_spread(a, b)
        if note:
            spread_notes.append(note)

    if female["is_pregnant"]:
        return False, "Already pregnant.", ERROR_COLOR, True

    f_key, f_stage = parse_disease(female["disease"] if "disease" in female.keys() else None)
    m_key, m_stage = parse_disease(male["disease"] if "disease" in male.keys() else None)
    if blocks_conception(f_key, f_stage) or blocks_conception(m_key, m_stage):
        from engine.diseases import get_stage_info

        sick = female if blocks_conception(f_key, f_stage) else male
        s_key, s_stage = (f_key, f_stage) if sick is female else (m_key, m_stage)
        ill_name = get_stage_info(s_key, s_stage or "active")["name"] if s_key else "Redscratch"
        body = (
            f"**{sick['wolf_name']}** carries **{ill_name}**; "
            "conception is not safe until treated."
            + mood_line()
        )
        if spread_notes:
            body += "\n\n" + "\n".join(spread_notes)
        if caught_lines:
            body += caught_suffix()
        return True, body, ERROR_COLOR, False

    result = conception_check(female, male)
    if result["success"]:
        db.set_pregnancy(female["id"], male["id"], day_number)
        msg = f"**{female['wolf_name']}** is with pup. Gestation: **{GESTATION_DAYS}** in-game days."
        if result["outcome"] == "critical_success":
            msg += " Unusually healthy litter expected."
    else:
        db.set_bonded_mates(user["id"], partner_user["id"])
        msg = "No conception this time."
        if result["outcome"] == "complication":
            msg = "Complications; false pregnancy or illness."

    msg = f"Conception roll: **{result['total']}** vs DC 15.\n{msg}{mood_line()}"
    if spread_notes:
        msg += "\n\n" + "\n".join(spread_notes)
    if caught_lines:
        msg += caught_suffix()
    color = SUCCESS_COLOR if result["success"] else ERROR_COLOR
    return True, msg, color, False
