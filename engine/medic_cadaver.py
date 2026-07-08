# engine/medic_cadaver.py
"""Medic-apprentice cadaver dissection: learn anatomy by studying the dead.

A sanctioned part of an apprentice's training under the green tongue: with the
den's leave, the apprentice opens a fallen packmate to learn how the body is
built. Once per sunrise, capped at a handful of lessons per apprentice (there is
only so much a body can teach). Success deepens medicine skill; a slip risks
infection. All access to the ``users`` row is sqlite3.Row-safe (no ``.get``).
"""

from __future__ import annotations

import random

import database as db
from engine.character import attr_modifier, parse_proficiencies
from engine.character_traits import adjust_skill_trait_experience
from engine.dice import roll_d20
from engine.exhaustion_effects import EXHAUSTION_MAX, PAIN_EXHAUSTION_MAX
from engine.herb_buffs import get_buffs, herb_check_adjustments, merge_buff_fields
from engine.role_features import has_any_role

CADAVER_DISSECTION_DC = 14
MAX_DISSECTION_REWARDS = 3  # a body can only teach so much; lifetime cap per apprentice
CADAVER_DISSECTION_MOOD_COST = 5  # opening a packmate's body is grim, taboo work


def is_apprentice_medic(user) -> bool:
    return has_any_role(user, "medic_apprentice")


def _rv(row, key, default=0):
    """Row-safe read with an int-friendly default."""
    return db.row_val(row, key, default)


def get_dead_packmates(pack_id: int) -> list:
    """Dead wolves from the same pack that are still stored (not purged)."""
    if not pack_id:
        return []
    with db.get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM users
            WHERE pack_id = ? AND condition = 'dead'
            ORDER BY death_day DESC, id DESC
            """,
            (pack_id,),
        ).fetchall()


def can_dissect(apprentice, cadaver, *, day: int) -> tuple[bool, str]:
    """Whether ``apprentice`` may dissect ``cadaver`` this sunrise."""
    if not is_apprentice_medic(apprentice):
        return False, "only **medic apprentices** may dissect cadavers."
    if apprentice["id"] == cadaver["id"]:
        return False, "you cannot dissect yourself."
    if cadaver["condition"] != "dead":
        return False, "that wolf is not dead; only the dead can be studied."
    ap_pack = _rv(apprentice, "pack_id", None)
    if not ap_pack or ap_pack != _rv(cadaver, "pack_id", None):
        return False, "you can only study a cadaver from your own pack."
    buffs = get_buffs(apprentice)
    if int(buffs.get("last_dissect_day", 0)) >= day:
        return False, "you have already studied a cadaver this sunrise."
    if int(buffs.get("dissection_count", 0)) >= MAX_DISSECTION_REWARDS:
        return False, f"you have learned all a cadaver can teach (max {MAX_DISSECTION_REWARDS} lessons)."
    return True, ""


def perform_dissection(apprentice, cadaver, *, day: int) -> tuple[bool, str]:
    """Run the dissection check, update the apprentice, and return (success, message)."""
    ok, msg = can_dissect(apprentice, cadaver, day=day)
    if not ok:
        return False, msg

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

    # record the cooldown + lesson tally on every attempt (success or not).
    buffs["last_dissect_day"] = day
    buffs["dissection_count"] = int(buffs.get("dissection_count", 0)) + 1
    roll_line = (
        f"(roll {die} {mod:+} + prof {prof_bonus} + mentor {mentor_bonus}"
        f" + herbs {herb_mod} = **{total}** vs dc {CADAVER_DISSECTION_DC})"
    )
    # opening a packmate's body weighs on the apprentice no matter the outcome.
    db.adjust_mood(apprentice["id"], -CADAVER_DISSECTION_MOOD_COST)
    grim = f"\n_cutting into a packmate's body is grim, taboo work; it weighs on you (**-{CADAVER_DISSECTION_MOOD_COST} mood**)._"

    # natural 1: a slip of the paw, a nicked rib; infection and fatigue.
    if die == 1:
        new_ex = min(EXHAUSTION_MAX, int(_rv(apprentice, "exhaustion", 0)) + 1)
        new_pe = min(PAIN_EXHAUSTION_MAX, int(_rv(apprentice, "pain_exhaustion", 0)) + 1)
        fields = {"exhaustion": new_ex, "pain_exhaustion": new_pe}
        fields.update(merge_buff_fields(apprentice, **buffs))
        db.update_user_by_id(apprentice["id"], **fields)
        return False, (
            f"**dissection gone wrong:** you nick yourself on a sharp rib and the wound sours. "
            f"{roll_line} → **+1 exhaustion, +1 pain exhaustion**.{grim}"
        )

    success = total >= CADAVER_DISSECTION_DC
    db.update_user_by_id(apprentice["id"], **merge_buff_fields(apprentice, **buffs))

    if not success:
        db.adjust_mood(apprentice["id"], -2)
        return False, f"{roll_line}\n_the body keeps its secrets today; you sit back frustrated (**-2 mood**)._{grim}"

    # success: deepen medicine skill.
    _, xp_msg = adjust_skill_trait_experience(apprentice["id"], "medicine", 1)
    lines = [f"{roll_line}\n_you learn from the dead; the shape of the body settles into your understanding._"]
    if xp_msg:
        lines.append(f"_{xp_msg.strip('_')}_")

    # the gut sometimes holds what the wolf last ate: a common herb or a few bones.
    loot: list[str] = []
    if random.random() < 0.30:
        from herbs import HERBS

        common = [k for k, v in HERBS.items() if v.get("rarity") == "common" and not v.get("poison")]
        if common:
            item = db.get_item_by_key(f"herb_{random.choice(common)}")
            if item:
                db.grant_item(apprentice["discord_id"], item["id"], quantity=1)
                loot.append(item["name"])
    if random.random() < 0.20:
        bones = random.randint(3, 8)
        db.add_bones(apprentice["discord_id"], bones, wolf_id=apprentice["id"])
        loot.append(f"{bones} bones")
    if loot:
        lines.append(f"(from the gut: **{', '.join(loot)}**)")
    lines.append(grim.strip("\n"))

    return True, "\n".join(lines)


def get_last_dissect_day(apprentice) -> int:
    return int(get_buffs(apprentice).get("last_dissect_day", 0))
