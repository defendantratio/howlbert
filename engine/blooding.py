"""Juvenile blooding; earned on first successful hunt kill (6 to 24 moons)."""

from __future__ import annotations

import database as db
from config import JUVENILE_MAX_MOONS, PUP_MAX_MOONS


def is_unblooded_juvenile(user) -> bool:
    age = int(user["age_months"]) if "age_months" in user.keys() else 24
    if age < PUP_MAX_MOONS or age >= JUVENILE_MAX_MOONS:
        return False
    if "has_blooding" in user.keys() and user["has_blooding"]:
        return False
    return True


def blooding_gate_message(user, *, action: str = "roleevent") -> str | None:
    if not is_unblooded_juvenile(user):
        return None
    if action == "roleevent":
        return (
            "you have not earned your **blooding** yet; bring down prey with a successful **`/bones action:hunt`** "
            "before your role's trials (`/role action:event`)."
        )
    return None


def format_blooding_status(user) -> str | None:
    """reminder for unblooded juveniles on profile, vitals, and cooldowns."""
    if not is_unblooded_juvenile(user):
        return None
    return (
        "**blooding:** not yet earned; first successful **`/bones action:hunt`** kill "
        "unlocks **`/role action:event`** (+8 mood, +1 standing)."
    )


def award_blooding_on_hunt(user) -> str | None:
    """Mark blooded after first hunt kill. Returns a line for the hunt embed footer."""
    if not is_unblooded_juvenile(user):
        return None
    db.update_user(user["discord_id"], wolf_id=user["id"], has_blooding=1)
    mood = db.adjust_mood(user["id"], 8)
    standing_note = ""
    if user["pack_id"]:
        new_standing = db.adjust_wolf_standing_by_id(user["id"], 1)
        standing_note = f" +1 standing ({new_standing})."
    from engine.wolf_journal import log_blooded

    log_blooded(user["id"], user["wolf_name"])
    return (
        f"first kill: {user['wolf_name']} is blooded. "
        f"+8 mood ({mood}).{standing_note}"
    )
