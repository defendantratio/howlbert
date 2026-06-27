"""Finalize adoption after consent."""

from __future__ import annotations

import database as db
from engine.aging import stage_for_age, stage_label
from engine.attraction import are_bonded_mates
from engine.youth_lineage import adoption_eligibility_error


def accept_pending_adoption(pending_id: int) -> tuple[bool, str]:
    pending = db.get_pending_adoption(pending_id)
    if not pending or pending["status"] != "pending":
        return False, "this adoption request is no longer active."
    adopter1 = db.get_user_by_id(pending["adopter_1_wolf_id"])
    adopter2 = db.get_user_by_id(pending["adopter_2_wolf_id"])
    youth = db.get_user_by_id(pending["youth_wolf_id"])
    if not adopter1 or not adopter2 or not youth:
        db.set_pending_adoption_status(pending_id, "expired")
        return False, "one of the wolves no longer exists."
    if not are_bonded_mates(adopter1, adopter2):
        db.set_pending_adoption_status(pending_id, "expired")
        return False, "the adopters are no longer bonded mates."
    err = adoption_eligibility_error(youth, adopter1, adopter2)
    if err:
        db.set_pending_adoption_status(pending_id, "expired")
        return False, err
    day = pending["day_number"]
    db.set_adoptive_parents(youth["id"], adopter1["id"], adopter2["id"])
    db.update_user(adopter1["discord_id"], wolf_id=adopter1["id"], last_adopt_day=day)
    db.update_user(adopter2["discord_id"], wolf_id=adopter2["id"], last_adopt_day=day)
    if adopter1["pack_id"] and adopter1["pack_id"] == adopter2["pack_id"]:
        db.adjust_pack_unity(adopter1["pack_id"], 1)
    db.set_pending_adoption_status(pending_id, "accepted")
    stage = stage_label(stage_for_age(youth["age_months"]))
    body = (
        f"**{youth['wolf_name']}** ({stage}) joins **{adopter1['wolf_name']}** and "
        f"**{adopter2['wolf_name']}**'s den."
    )
    from engine.healer_code import apply_medic_adopt_scandal

    scandal = apply_medic_adopt_scandal(adopter1, adopter2, youth)
    if scandal:
        body += "\n\n" + "\n\n".join(scandal)
    return True, body


def decline_pending_adoption(pending_id: int) -> tuple[bool, str]:
    pending = db.get_pending_adoption(pending_id)
    if not pending or pending["status"] != "pending":
        return False, "this adoption request is no longer active."
    youth = db.get_user_by_id(pending["youth_wolf_id"])
    name = youth["wolf_name"] if youth else "The youth"
    db.set_pending_adoption_status(pending_id, "declined")
    return True, f"**{name}** stays in their current den."
