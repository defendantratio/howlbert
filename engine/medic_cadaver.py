# engine/medic_cadaver.py
"""Medic-apprentice cadaver dissection: learn anatomy by studying the dead.

A sanctioned part of an apprentice's training under the green tongue: with a
superior's leave, the apprentice opens a fallen wolf (their own pack's dead, or
a rival's or loner's) to learn how the body is built. It is medical study, not
desecration, but cutting into a body is solemn work and weighs on the
apprentice. Requires an **alpha** or a **full medic** (the mentor) in the den to
sanction it. Once per sunrise, capped at a handful of lessons per apprentice.
Success deepens medicine skill; a slip risks infection. All ``users`` row access
is sqlite3.Row-safe (no ``.get``).
"""

from __future__ import annotations

import database as db
from engine.character import attr_modifier, parse_proficiencies
from engine.character_traits import adjust_skill_trait_experience
from engine.dice import roll_d20
from engine.exhaustion_effects import EXHAUSTION_MAX, PAIN_EXHAUSTION_MAX
from engine.herb_buffs import get_buffs, herb_check_adjustments, merge_buff_fields
from engine.role_features import has_any_role, is_full_medic

CADAVER_DISSECTION_DC = 14
MAX_DISSECTION_REWARDS = 3  # a body can only teach so much; lifetime cap per apprentice
CADAVER_DISSECTION_MOOD_COST = 5  # opening a packmate's body is solemn, heavy work
CADAVER_DISSECTION_MOOD_COST_RIVAL = 2  # a rival/loner's body weighs less on you


def is_apprentice_medic(user) -> bool:
    return has_any_role(user, "medic_apprentice")


def _rv(row, key, default=0):
    """Row-safe read with an int-friendly default."""
    return db.row_val(row, key, default)


def has_dissection_sanction(apprentice) -> bool:
    """A superior in the den authorizes the training: a living **alpha** or
    **full medic** (the apprentice's mentor) in the same pack."""
    pack_id = _rv(apprentice, "pack_id", None)
    if not pack_id:
        return False
    for member in db.get_pack_members(pack_id):
        if member["id"] == apprentice["id"]:
            continue
        if _rv(member, "condition", "") == "dead":
            continue
        if has_any_role(member, "alpha") or is_full_medic(member):
            return True
    return False


def pack_has_living_alpha(pack_id) -> bool:
    """A living alpha leads the given pack (to sanction releasing their dead)."""
    if not pack_id:
        return False
    for member in db.get_pack_members(pack_id):
        if _rv(member, "condition", "") == "dead":
            continue
        if has_any_role(member, "alpha"):
            return True
    return False




def can_dissect(apprentice, cadaver, *, day: int) -> tuple[bool, str]:
    """Whether ``apprentice`` may dissect ``cadaver`` this sunrise."""
    if not is_apprentice_medic(apprentice):
        return False, "only **medic apprentices** may dissect cadavers."
    if apprentice["id"] == cadaver["id"]:
        return False, "you cannot dissect yourself."
    if cadaver["condition"] != "dead":
        return False, "that wolf is not dead; only the dead can be studied."
    if not has_dissection_sanction(apprentice):
        return False, "you need an **alpha** or a **full medic** (your mentor) in your den to sanction the study."
    # a body from another pack also needs that pack's alpha to release it.
    cad_pack = _rv(cadaver, "pack_id", None)
    ap_pack = _rv(apprentice, "pack_id", None)
    if cad_pack and cad_pack != ap_pack and not pack_has_living_alpha(cad_pack):
        return False, "the dead wolf's pack has no living **alpha** to sanction releasing the body."
    buffs = get_buffs(apprentice)
    if int(buffs.get("last_dissect_day", 0)) >= day:
        return False, "you have already studied a cadaver this sunrise."
    if int(buffs.get("dissection_count", 0)) >= MAX_DISSECTION_REWARDS:
        return False, f"you have learned all a cadaver can teach (max {MAX_DISSECTION_REWARDS} lessons)."
    return True, ""


def perform_dissection(apprentice, cadaver, *, day: int) -> tuple[bool, bool, str]:
    """Run the dissection. Returns (dissected, success, message).

    ``dissected`` is False when the attempt was blocked (not an apprentice, no
    sanction, cooldown, cap, wrong pack) and no body was opened; True when the
    study actually happened (whether or not the medicine check passed)."""
    ok, msg = can_dissect(apprentice, cadaver, day=day)
    if not ok:
        return False, False, msg

    buffs = get_buffs(apprentice)
    wis = int(_rv(apprentice, "attr_wis", 3))
    mod = attr_modifier(wis)
    die = roll_d20()
    profs = parse_proficiencies(_rv(apprentice, "skill_proficiencies", "[]"))
    prof_bonus = 2 if "medicine" in profs else 0
    mentor_bonus = 0
    if buffs.get("mentor_bonus_skill") == "medicine":
        mentor_bonus = int(buffs.get("mentor_bonus_value", 0))
    herb_mod, _ = herb_check_adjustments(apprentice, ("attr_wis",), skill_key="medicine")
    total = die + mod + prof_bonus + mentor_bonus + herb_mod

    # record the cooldown + lesson tally on every study (success or not).
    buffs["last_dissect_day"] = day
    buffs["dissection_count"] = int(buffs.get("dissection_count", 0)) + 1
    roll_line = (
        f"(roll {die} {mod:+} + prof {prof_bonus} + mentor {mentor_bonus}"
        f" + herbs {herb_mod} = **{total}** vs dc {CADAVER_DISSECTION_DC})"
    )
    # cutting into a fallen wolf is solemn work; a packmate's body weighs more
    # than a rival's or a loner's.
    ap_pack = _rv(apprentice, "pack_id", None)
    cad_pack = _rv(cadaver, "pack_id", None)
    same_pack = bool(ap_pack) and ap_pack == cad_pack
    mood_cost = CADAVER_DISSECTION_MOOD_COST if same_pack else CADAVER_DISSECTION_MOOD_COST_RIVAL
    db.adjust_mood(apprentice["id"], -mood_cost)
    whose = "a packmate's" if same_pack else "a fallen wolf's"
    solemn = (
        f"\n_studying {whose} body is solemn work; it weighs on you "
        f"(**-{mood_cost} mood**)._"
    )

    # natural 1: a slip of the paw, a nicked rib; infection and fatigue.
    if die == 1:
        new_ex = min(EXHAUSTION_MAX, int(_rv(apprentice, "exhaustion", 0)) + 1)
        new_pe = min(PAIN_EXHAUSTION_MAX, int(_rv(apprentice, "pain_exhaustion", 0)) + 1)
        fields = {"exhaustion": new_ex, "pain_exhaustion": new_pe}
        fields.update(merge_buff_fields(apprentice, **buffs))
        db.update_user_by_id(apprentice["id"], **fields)
        return True, False, (
            f"**dissection gone wrong:** you nick yourself on a sharp rib and the wound sours. "
            f"{roll_line} → **+1 exhaustion, +1 pain exhaustion**.{solemn}"
        )

    success = total >= CADAVER_DISSECTION_DC
    db.update_user_by_id(apprentice["id"], **merge_buff_fields(apprentice, **buffs))

    if not success:
        db.adjust_mood(apprentice["id"], -2)
        return True, False, f"{roll_line}\n_the body keeps its secrets today; you sit back frustrated (**-2 mood**)._{solemn}"

    # success: deepen medicine skill.
    _, xp_msg = adjust_skill_trait_experience(apprentice["id"], "medicine", 1)
    lines = [f"{roll_line}\n_you learn from the dead; the shape of the body settles into your understanding._"]
    if xp_msg:
        lines.append(f"_{xp_msg.strip('_')}_")
    lines.append(solemn.strip("\n"))
    return True, True, "\n".join(lines)


