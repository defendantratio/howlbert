"""Soft costs of doing strenuous field work with a body that should be resting.

Only full paralysis hard-blocks field commands now. A spinal injury, a fresh
post-surgery bone set, and a late-term pregnancy no longer forbid hunting,
patrolling, or ranging; instead each exacts a price the moment a wolf pushes
through it:

  * **spinal injury**  -> severe pain exhaustion, and a chance the strained cord
    tears the rest of the way into permanent **paralysis**.
  * **post-surgery bone rest** -> pain, and a chance the mending bone re-breaks,
    undoing the surgery.
  * **late pregnancy** -> a chance the strain costs the litter (miscarriage),
    on top of the steepened yield penalty in ``pregnancy_hunt_multiplier``.

``apply_strenuous_strain`` is called once, on the allow-path of a strenuous
action, and returns a player-facing note (or None).
"""

from __future__ import annotations

import json
import random

import database as db
from engine.pregnancy import STRENUOUS_ACTIONS, in_late_pregnancy

SPINAL_WORSEN_CHANCE = 0.15
BONE_REBREAK_CHANCE = 0.25
PREGNANCY_LOSS_CHANCE = 0.15
SPINAL_PAIN_GAIN = 2
BONE_REST_PAIN_GAIN = 1
BONE_REBREAK_REST_SUNRISES = 5


def _add_pain(discord_id: int, wolf_id: int, amount: int) -> None:
    from engine.exhaustion_effects import PAIN_EXHAUSTION_MAX

    fresh = db.get_user(discord_id)
    if not fresh:
        return
    cur = int(fresh["pain_exhaustion"] or 0) if "pain_exhaustion" in fresh.keys() else 0
    db.update_user(discord_id, wolf_id=wolf_id, pain_exhaustion=min(PAIN_EXHAUSTION_MAX, cur + amount))


def apply_strenuous_strain(user, day: int, action: str) -> str | None:
    """Apply the soft costs of pushing a body that should rest; return a note."""
    if not user or action not in STRENUOUS_ACTIONS:
        return None
    from engine.conditions import add_injury, parse_injuries

    fresh = db.get_user(user["discord_id"])
    if not fresh:
        return None
    did = fresh["discord_id"]
    wid = fresh["id"]
    injuries = parse_injuries(fresh["active_injuries"] if "active_injuries" in fresh.keys() else None)
    notes: list[str] = []

    # 1) spinal injury: severe pain, and a chance of tipping into paralysis.
    if "spinal_injury" in injuries and "paralyzed" not in injuries:
        _add_pain(did, wid, SPINAL_PAIN_GAIN)
        if random.random() < SPINAL_WORSEN_CHANCE:
            f = db.get_user(did)
            inj = parse_injuries(f["active_injuries"] if f and "active_injuries" in f.keys() else None)
            inj = [i for i in inj if i != "spinal_injury"]
            inj = add_injury(inj, "paralyzed")
            db.set_user_conditions(did, wolf_id=wid, active_injuries=json.dumps(inj))
            notes.append(
                "**the strained spine gives way; the cord tears through; you are now permanently paralyzed.**"
            )
        else:
            notes.append(
                f"_you drag the hurt spine out anyway; the pain flares (**+{SPINAL_PAIN_GAIN} pain exhaustion**)._"
            )

    # 2) post-surgery bone rest: pain, and a chance the mending bone re-breaks.
    from engine.injury_effects import bone_rest_activity_block

    if bone_rest_activity_block(fresh, day=day):
        _add_pain(did, wid, BONE_REST_PAIN_GAIN)
        if random.random() < BONE_REBREAK_CHANCE:
            f = db.get_user(did)
            inj = parse_injuries(f["active_injuries"] if f and "active_injuries" in f.keys() else None)
            inj = add_injury(inj, "fractured_rib")
            db.set_user_conditions(did, wolf_id=wid, active_injuries=json.dumps(inj))
            db.update_user(did, wolf_id=wid, bone_rest_until=day + BONE_REBREAK_REST_SUNRISES)
            notes.append(
                "**the set bone gives way under the strain; the fracture re-opens and the surgery is undone.**"
            )
        else:
            notes.append(
                f"_you strain the mending bone; it holds, but aches (**+{BONE_REST_PAIN_GAIN} pain exhaustion**)._"
            )

    # 3) late pregnancy: a chance the strain costs the litter.
    sex = fresh["birth_sex"] if "birth_sex" in fresh.keys() else None
    if sex == "female" and in_late_pregnancy(fresh, day):
        if random.random() < PREGNANCY_LOSS_CHANCE:
            db.clear_pregnancy(wid)
            db.adjust_mood(wid, -20)
            notes.append("**the strain is too much; she loses the litter.** (**-20 mood**)")
        else:
            notes.append("_heavy with pup, she pushes through; the litter holds this time, but it is a gamble._")

    return " ".join(notes) if notes else None


def strain_footer(embed, user, day: int, action: str) -> None:
    """Apply strenuous strain and append its note to an embed footer, if any."""
    note = apply_strenuous_strain(user, day, action)
    if not note or embed is None:
        return
    footer = embed.footer.text if embed.footer and embed.footer.text else ""
    embed.set_footer(text=f"{footer} · {note}" if footer else note)
