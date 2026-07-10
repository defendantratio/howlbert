"""Strenuous field-activity bookkeeping.

Historically this module applied a *second* throttle on top of energy: repeating
a field action in one sunrise directly piled on exhaustion. That double-counted
what the energy system already does, so the activity-driven exhaustion has been
retired. Energy is now the single activity throttle (see engine.energy):

  * each action spends energy (specialists tire slower at their craft), and
  * acting once energy is empty is what adds exhaustion + mood.

Exhaustion still comes from its real sources: running on empty, low
hunger/hydration/mood at rollover, forced marches, and injuries; just not from a
parallel per-activity counter. The lightweight counters below are kept because a
short/long rest still clears them and a couple of call sites read them.
"""

from __future__ import annotations

import database as db
from engine.character import is_skill_proficient
from engine.herb_buffs import buffs_json, get_buffs

ACTIVITY_SKILL: dict[str, str] = {
    "hunt": "hunting",
    "forage": "herblore",
    "track": "tracking",
    "fish": "survival",
    "scavenge": "survival",
    "explore": "survival",
    "rescout": "survival",
    "survey": "stealth",
    "trail": "tracking",
    "skill": "survival",
}

ACTIVITY_LABEL: dict[str, str] = {
    "hunt": "hunting",
    "forage": "foraging",
    "track": "tracking",
    "fish": "fishing",
    "scavenge": "scavenging",
    "explore": "ranging",
    "rescout": "rescouting",
    "survey": "surveying",
    "trail": "trailing",
    "skill": "field work",
}


def skill_for_activity(activity_key: str, user=None) -> str:
    if activity_key == "forage" and user:
        from engine.role_privileges import is_forager

        if is_skill_proficient(user, "herblore") or is_forager(user):
            return "herblore"
        return "survival"
    return ACTIVITY_SKILL.get(activity_key, "survival")


def _fatigue_state(user, day: int) -> tuple[dict, dict, int]:
    buffs = get_buffs(user)
    if buffs.get("activity_fatigue_day") != day:
        buffs["activity_fatigue_day"] = day
        buffs["activity_fatigue_total"] = 0
        buffs["activity_fatigue_by_key"] = {}
    by_key = buffs.setdefault("activity_fatigue_by_key", {})
    if not isinstance(by_key, dict):
        by_key = {}
        buffs["activity_fatigue_by_key"] = by_key
    total = int(buffs.get("activity_fatigue_total", 0))
    return buffs, by_key, total


def clear_activity_fatigue(user, day: int) -> None:
    """reset strenuous-activity counters after a rest break (short or long)."""
    if not user:
        return
    buffs = get_buffs(user)
    buffs["activity_fatigue_day"] = day
    buffs["activity_fatigue_total"] = 0
    buffs["activity_fatigue_by_key"] = {}
    db.update_user(user["discord_id"], wolf_id=user["id"], herb_buffs=buffs_json(buffs))




def apply_activity_fatigue(
    user,
    activity_key: str,
    skill_key: str | None,
    day: int,
    *,
    activity_count: int | None = None,
) -> str | None:
    """Retired: repeated field activity no longer adds exhaustion on top of the
    energy it already spent (energy is the single throttle now). Always returns
    None so the many call sites need no change and show no fatigue footer."""
    return None


def append_fatigue_to_footer(embed, note: str | None) -> None:
    if not note or not embed:
        return
    footer = embed.footer.text if embed.footer and embed.footer.text else ""
    embed.set_footer(text=f"{footer} · {note}" if footer else note)
