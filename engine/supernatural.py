"""Spirit curses, Maw omens, and other supernatural marks."""

from __future__ import annotations

import json
import random

import database as db
from engine.long_term_injuries import add_long_term_injury, parse_long_term_injuries

SPIRIT_CURSE_KEY = "spirit_curse"

SPIRIT_CURSE_BLURB = (
    "The Maw's shadow clings; **−1** on spiritual checks, whispers bite harder in fog. "
    "Break with **wolfsbane**, **swamp milkweed**, a Medic cleansing ritual, or "
    "`/skills category:spiritual check:spirit_cleanse`."
)


def has_spirit_curse(user) -> bool:
    raw = user["long_term_injuries"] if user and "long_term_injuries" in user.keys() else None
    return SPIRIT_CURSE_KEY in parse_long_term_injuries(raw)




def apply_spirit_curse(wolf_id: int, *, source: str = "") -> tuple[bool, str]:
    wolf = db.get_user_by_id(wolf_id)
    if not wolf:
        return False, "wolf not found."
    if has_spirit_curse(wolf):
        return False, f"**{wolf['wolf_name']}** already bears a spirit curse."
    add_long_term_injury(wolf_id, SPIRIT_CURSE_KEY)
    tail = f" ({source})" if source else ""
    return True, f"**{wolf['wolf_name']}** is **spirit-cursed**{tail}."


def lift_spirit_curse(wolf_id: int) -> bool:
    wolf = db.get_user_by_id(wolf_id)
    if not wolf:
        return False
    entries = parse_long_term_injuries(
        wolf["long_term_injuries"] if "long_term_injuries" in wolf.keys() else None
    )
    if SPIRIT_CURSE_KEY not in entries:
        return False
    remaining = [entry for entry in entries if entry != SPIRIT_CURSE_KEY]
    db.update_user_by_id(wolf_id, long_term_injuries=json.dumps(remaining))
    return True


def spirit_curse_check_adjustment(
    user,
    *,
    attr_keys: tuple[str, ...],
    skill_key: str | None,
) -> tuple[int, str]:
    if not has_spirit_curse(user):
        return 0, ""
    spiritual = skill_key in ("medicine", "herblore", "tracking", "survival") or "attr_wis" in attr_keys
    if not spiritual:
        return 0, ""
    return -1, "spirit curse (−1)"


def maybe_curse_from_whisper(user, *, weather: str) -> str | None:
    """mistmoor / drown-sick fog sniff: rare direct curse instead of anxiety."""
    from engine.whispering_wild import is_whispering_weather, _whispering_affinity

    if not user or not is_whispering_weather(weather) or not _whispering_affinity(user):
        return None
    if has_spirit_curse(user):
        return None
    if random.random() > 0.07:
        return None
    ok, msg = apply_spirit_curse(user["id"], source="belly-rip whisper on the wind")
    return msg if ok else None
