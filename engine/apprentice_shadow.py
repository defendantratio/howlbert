"""Apprentice shadowing; the non-medic equivalent of `/medic action:observe`.

Medic apprentices already got a real mechanic from observing a case
(see engine.medical_care.run_observe_apprentice): a mentor-bonus buff on
their next medicine check. This gives the same mechanic to every other
apprentice track (hunter, scout, forager, diplomat, caretaker) by shadowing
a full-ranked mentor of the matching role.
"""

from __future__ import annotations

import database as db
from config import MENTOR_BONUS_VALUE
from rpg_rules import ROLE_PROFICIENCIES

SHADOWABLE_APPRENTICES: dict[str, str] = {
    "hunter_apprentice": "hunter",
    "scout_apprentice": "scout",
    "forager_apprentice": "forager",
    "diplomat_apprentice": "diplomat",
    "caretaker_apprentice": "caretaker",
}


def focus_skill_for_apprentice(apprentice_role: str) -> str | None:
    skills = ROLE_PROFICIENCIES.get(apprentice_role)
    return skills[0] if skills else None


def run_apprentice_shadow(apprentice, mentor, *, day: int) -> tuple[bool, str]:
    role = apprentice["wolf_role"] if "wolf_role" in apprentice.keys() else None
    mentor_role_required = SHADOWABLE_APPRENTICES.get(role)
    if not mentor_role_required:
        return False, (
            "only **hunter**, **scout**, **forager**, **diplomat**, or **caretaker** "
            "apprentices may shadow a mentor (medics use `/medic action:observe`)."
        )
    if apprentice["id"] == mentor["id"]:
        return False, "shadow another wolf's work; not your own."
    mentor_role = mentor["wolf_role"] if "wolf_role" in mentor.keys() else None
    if mentor_role != mentor_role_required:
        from rpg_rules import ROLE_LABELS

        label = ROLE_LABELS.get(mentor_role_required, mentor_role_required.title())
        return False, f"that wolf isn't a full **{label}**; pick a packmate who's earned the rank."
    if apprentice["pack_id"] != mentor["pack_id"] or not apprentice["pack_id"]:
        return False, "shadow a mentor in your own den."
    last = int(apprentice["last_shadow_day"]) if "last_shadow_day" in apprentice.keys() else 0
    if last >= day:
        return False, "you already shadowed a mentor this sunrise."

    focus = focus_skill_for_apprentice(role)
    from engine.herb_buffs import merge_buff_fields

    fields = {"last_shadow_day": day}
    fields.update(merge_buff_fields(apprentice, mentor_bonus_skill=focus, mentor_bonus_value=MENTOR_BONUS_VALUE))
    db.update_user_by_id(apprentice["id"], **fields)
    return True, (
        f"**{apprentice['wolf_name']}** shadows **{mentor['wolf_name']}** at work, watching close.\n"
        f"_apprentice paws; watch and learn before you hold the rank._\n"
        f"next **{focus}** check: **+{MENTOR_BONUS_VALUE}**."
    )
