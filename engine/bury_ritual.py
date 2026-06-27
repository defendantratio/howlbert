"""Bury carcass with optional ritual herbs (lavender, rosemary, meadowsweet, mint)."""

from __future__ import annotations

import database as db
from engine.herb_buffs import grant_burial_scent_mask
from engine.mirewort_burial import is_mirewort, mirewort_carcass_burial_note
from engine.prey_items import prey_meta
from engine.surgery import consume_participant_herb, participant_has_herb
from herbs import HERBS

BURY_RITUAL_HERBS: frozenset[str] = frozenset(
    {"lavender", "rosemary", "meadowsweet", "garden_mint", "watermint"}
)


def _herb_label(key: str) -> str:
    return HERBS.get(key, {}).get("name", key.replace("_", " ").title())


def bury_carcass(
    user,
    stack_id: int,
    *,
    day: int,
    ritual_herb: str | None = None,
) -> tuple[bool, str]:
    stack = db.get_prey_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "you don't carry that carcass."

    meta = prey_meta(stack["prey_key"])
    ritual_note = ""
    mood_delta = 2
    db_fields: dict = {}

    key = (ritual_herb or "").strip().lower()
    if key and key not in ("none", ""):
        if key == "mint":
            key = "garden_mint"
        if key not in BURY_RITUAL_HERBS:
            allowed = ", ".join(_herb_label(k) for k in sorted(BURY_RITUAL_HERBS))
            return False, f"use **lavender**, **rosemary**, **meadowsweet**, or **mint** ({allowed})."
        if not participant_has_herb(user, key):
            return False, f"no **{_herb_label(key)}** in your herb bag or inventory."
        consume_participant_herb(user, key)
        mood_delta = 5
        db_fields.update(grant_burial_scent_mask(user, day=day, duration=3))
        ritual_note = (
            f"\n\n**{_herb_label(key)}** over the grave masks death-scent for **3 sunrises** "
            "(filth and flea exposure halved)."
        )

    db.remove_prey_stack(stack_id)
    new_mood = db.adjust_mood(user["id"], mood_delta)
    if db_fields:
        db.update_user_by_id(user["id"], **db_fields)

    mirewort_note = ""
    if is_mirewort(user):
        mirewort_note = mirewort_carcass_burial_note(ritual_herb_key=key if key else None)

    body = (
        f"you scrape earth over **{meta['label']}**; gone from your hoard.\n"
        f"_the den remembers the respect; mood **{new_mood}** (**+{mood_delta}**)._"
        f"{ritual_note}"
        f"{mirewort_note}"
    )
    return True, body
