"""Pup training; `/pupcare action:train`; a deliberate, capped attribute nudge.

Distinct from feed (hunger/thirst upkeep), save (stillborn rescue), and adopt
(family placement): this is a real skill-check action with a permanent but
capped payoff, mirroring how the rest of the bot avoids flavor-only signals.
"""

from __future__ import annotations

import database as db
from config import (
    PUP_TRAIN_MAX_LIFETIME_BONUS,
    PUP_TRAIN_MOOD_CONSOLATION,
    PUP_TRAIN_SUCCESS_DC,
)
from engine.aging import stage_for_age
from engine.character import attr_modifier

TRAINABLE_ATTRS: dict[str, str] = {
    "str": "attr_str",
    "dex": "attr_dex",
    "con": "attr_con",
    "int": "attr_int",
    "cha": "attr_cha",
    "wis": "attr_wis",
}


def _trained_total(pup) -> int:
    return int(pup["trained_attr_total"]) if "trained_attr_total" in pup.keys() else 0


def train_pup(trainer, pup, *, attribute: str, day: int) -> tuple[bool, str]:
    attr_col = TRAINABLE_ATTRS.get(attribute)
    if not attr_col:
        return False, "pick a valid attribute to train: str, dex, con, int, cha, or wis."
    if trainer["id"] == pup["id"]:
        return False, "a pup can't train themself."
    age = int(pup["age_months"]) if "age_months" in pup.keys() else 0
    stage = stage_for_age(age)
    if stage not in ("pup", "juvenile"):
        return False, f"**{pup['wolf_name']}** is grown; training only helps pups and juveniles."
    total = _trained_total(pup)
    if total >= PUP_TRAIN_MAX_LIFETIME_BONUS:
        return False, (
            f"**{pup['wolf_name']}** has learned all training can teach "
            f"(+{PUP_TRAIN_MAX_LIFETIME_BONUS} lifetime cap reached)."
        )

    # unlimited; the lifetime cap is the real ceiling. repeat lessons are
    # throttled by the trainer's energy (see engine.energy), not a climbing dc.
    from engine.diminishing import record_use

    effective_dc = PUP_TRAIN_SUCCESS_DC
    record_use(trainer, f"trainpup:{pup['id']}", day)

    from engine.dice import roll_d20

    die = roll_d20()
    mod = attr_modifier(int(trainer["attr_cha"])) if "attr_cha" in trainer.keys() else 0
    total_roll = die + mod
    label = attribute.upper()
    tired = ""

    if total_roll >= effective_dc:
        new_val = int(pup[attr_col]) + 1
        new_total = total + 1
        db.update_user_by_id(
            pup["id"], **{attr_col: new_val, "trained_attr_total": new_total, "last_train_day": day}
        )
        msg = (
            f"**{trainer['wolf_name']}** drills **{pup['wolf_name']}** "
            f"({die}+{mod}={total_roll} vs dc {effective_dc}){tired}.\n"
            f"**{label}** rises to **{new_val}** ({new_total}/{PUP_TRAIN_MAX_LIFETIME_BONUS} lifetime)."
        )
        if new_total >= PUP_TRAIN_MAX_LIFETIME_BONUS:
            from engine.wolf_journal import log_trained

            log_trained(pup["id"], pup["wolf_name"])
            msg += "\n_their training is complete; no further lessons will help._"
        return True, msg

    new_mood = db.adjust_mood(pup["id"], PUP_TRAIN_MOOD_CONSOLATION)
    db.update_user_by_id(pup["id"], last_train_day=day)
    return False, (
        f"**{trainer['wolf_name']}** drills **{pup['wolf_name']}** "
        f"({die}+{mod}={total_roll} vs dc {effective_dc}){tired}; the lesson doesn't land today, "
        f"but **{pup['wolf_name']}** enjoyed the attention (mood **{new_mood}**)."
    )
