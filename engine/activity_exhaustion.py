"""Repeated field activity fatigue; untrained wolves tire faster."""

from __future__ import annotations

import sqlite3

import database as db
from config import ACTIVITY_FATIGUE_CROSS_TOTAL_THRESHOLD
from engine.character import is_skill_proficient
from engine.exhaustion_effects import EXHAUSTION_MAX, consume_march_exhaustion_skip
from engine.herb_buffs import buffs_json, get_buffs

ACTIVITY_SKILL: dict[str, str] = {
    "hunt": "hunting",
    "forage": "survival",
    "track": "tracking",
    "fish": "survival",
    "scavenge": "survival",
    "explore": "survival",
    "rescout": "survival",
    "survey": "stealth",
    "trail": "tracking",
    "skill": "survival",
    "work": "survival",
    "crime": "stealth",
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
    "work": "labor",
    "crime": "sneaking",
}


def skill_for_activity(activity_key: str, user=None) -> str:
    key = ACTIVITY_SKILL.get(activity_key, "survival")
    if activity_key == "forage" and user and is_skill_proficient(user, "herblore"):
        return "herblore"
    return key


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


def _db_activity_count(user, activity_key: str, day: int) -> int | None:
    from engine.role_privileges import hunts_used_today, rescout_uses_today

    if activity_key == "hunt":
        return hunts_used_today(user, day)
    if activity_key == "rescout":
        return rescout_uses_today(user, day)
    return None


def _exhaustion_gain(activity_count: int, total_count: int, proficient: bool, current_ex: int) -> int:
    gain = 0
    if activity_count >= 2:
        if proficient:
            if activity_count == 3:
                gain = 1
            elif activity_count >= 4:
                gain = 1 + (activity_count - 3) // 2
        else:
            if activity_count == 2:
                gain = 1
            elif activity_count == 3:
                gain = 2
            else:
                gain = 2 + (activity_count - 3)
    if total_count >= ACTIVITY_FATIGUE_CROSS_TOTAL_THRESHOLD and gain == 0:
        gain = 1
    elif total_count > ACTIVITY_FATIGUE_CROSS_TOTAL_THRESHOLD:
        gain += 1
    room = max(0, EXHAUSTION_MAX - current_ex)
    return min(gain, room)


def record_strenuous_activity(
    user,
    activity_key: str,
    day: int,
    *,
    activity_count: int | None = None,
) -> tuple[int, int]:
    """Record one strenuous action; return (activity_count, total_count) after."""
    buffs, by_key, total = _fatigue_state(user, day)
    if activity_count is None:
        activity_count = int(by_key.get(activity_key, 0)) + 1
        by_key[activity_key] = activity_count
    else:
        by_key[activity_key] = activity_count
    total += 1
    buffs["activity_fatigue_total"] = total
    db.update_user(user["discord_id"], wolf_id=user["id"], herb_buffs=buffs_json(buffs))
    return activity_count, total


def apply_activity_fatigue(
    user,
    activity_key: str,
    skill_key: str | None,
    day: int,
    *,
    activity_count: int | None = None,
) -> str | None:
    """Increment counters and apply exhaustion. Returns player-facing note or None."""
    if not user:
        return None
    if activity_count is None:
        db_count = _db_activity_count(user, activity_key, day)
        if db_count is not None:
            activity_count = db_count
    activity_count, total_count = record_strenuous_activity(
        user, activity_key, day, activity_count=activity_count
    )
    if activity_count < 2 and total_count < ACTIVITY_FATIGUE_CROSS_TOTAL_THRESHOLD:
        return None

    skill = skill_key or skill_for_activity(activity_key, user)
    proficient = is_skill_proficient(user, skill)
    current_ex = int(user["exhaustion"]) if "exhaustion" in user.keys() else 0
    gain = _exhaustion_gain(activity_count, total_count, proficient, current_ex)
    if gain <= 0:
        return None

    with db.get_db() as conn:
        fresh = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user["id"],),
        ).fetchone()
        if not fresh:
            return None
        gain, skipped = consume_march_exhaustion_skip(conn, fresh, gain)
        if gain <= 0:
            if skipped:
                return "_Burnet eases the worst of the strain — no exhaustion this time._"
            return None
        new_ex = min(EXHAUSTION_MAX, int(fresh["exhaustion"]) + gain)
        db.set_user_conditions(user["discord_id"], wolf_id=user["id"], exhaustion=new_ex)

    label = ACTIVITY_LABEL.get(activity_key, activity_key)
    if proficient:
        reason = f"repeated {label} ({activity_count}×) without rest"
    else:
        reason = f"repeated {label} ({activity_count}×) — you're not trained for this"
    note = f"**+{gain} exhaustion** — {reason}"
    if skipped:
        note += " _(Burnet softened the worst of it)_"
    return note


def append_fatigue_to_footer(embed, note: str | None) -> None:
    if not note or not embed:
        return
    footer = embed.footer.text if embed.footer and embed.footer.text else ""
    embed.set_footer(text=f"{footer} · {note}" if footer else note)
