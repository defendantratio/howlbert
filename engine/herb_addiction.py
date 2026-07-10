# herb_addiction.py
"""Herb addiction / dependence.

Sedative and opioid-adjacent herbs build tolerance and dependence with repeated
use. A dependent wolf that goes a full sunrise without its herb suffers
withdrawal (low mood, restlessness, pain). Staying clean lets dependence fade.

Doses are tracked per wolf in the ``herb_use_log`` JSON column:
    {"poppy_seeds": {"doses": 4, "last_day": 12}, ...}

Flow:
 ; register_herb_dose()  called on every treat use (builds tolerance)
 ; herb_withdrawal_at_rollover()  called once per wolf at sunrise (penalties/decay)
"""

from __future__ import annotations

import json

import database as db

# herb_key -> dependence threshold (doses before withdrawal bites)
ADDICTIVE_HERBS: dict[str, int] = {
    "poppy_seeds": 3,
    "valerian": 4,
    "willow_bark": 5,
    "wild_cherry_bark": 4,
    "snakeroot": 4,
}

DOSE_CAP = 10  # tolerance stops climbing here


def _load_log(user) -> dict:
    raw = user["herb_use_log"] if "herb_use_log" in user.keys() else None
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _save_log(user, log: dict) -> None:
    db.update_user(user["discord_id"], wolf_id=user["id"], herb_use_log=json.dumps(log))


def register_herb_dose(user, herb_key: str, *, day: int) -> str:
    """Record a dose of an addictive herb. Returns a note when dependence forms
    or deepens, else ''."""
    threshold = ADDICTIVE_HERBS.get(herb_key)
    if threshold is None:
        return ""
    log = _load_log(user)
    entry = log.get(herb_key, {"doses": 0, "last_day": 0})
    was_dependent = entry["doses"] >= threshold
    entry["doses"] = min(DOSE_CAP, int(entry["doses"]) + 1)
    entry["last_day"] = day
    log[herb_key] = entry
    _save_log(user, log)
    name = herb_key.replace("_", " ")
    if not was_dependent and entry["doses"] >= threshold:
        return f"\n_the body has learned to crave **{name}**; dependence has set in._"
    if was_dependent:
        return f"\n_the craving for **{name}** deepens._"
    return ""


def herb_withdrawal_at_rollover(user, day: int) -> tuple[dict, str]:
    """Compute withdrawal for a dependent wolf that skipped its herb this sunrise,
    and decay tolerance for herbs left alone. Returns (fields_to_update, note).

    Connection-safe: this NEVER writes to the database itself. The updated
    ``herb_use_log`` JSON is included in ``fields_to_update`` so the caller can
    persist everything through its own open connection. Dependence decays one
    dose per clean sunrise.
    """
    log = _load_log(user)
    if not log:
        return {}, ""
    notes: list[str] = []
    mood_delta = 0
    ex_gain = 0
    pe_gain = 0
    changed = False

    for herb_key, entry in list(log.items()):
        threshold = ADDICTIVE_HERBS.get(herb_key)
        if threshold is None:
            continue
        doses = int(entry.get("doses", 0))
        last_day = int(entry.get("last_day", 0))
        used_today = last_day >= day
        if doses >= threshold and not used_today:
            # withdrawal: severity scales with how deep the dependence runs
            severity = 1 + (doses - threshold) // 3
            mood_delta -= 4 * severity
            ex_gain += severity
            pe_gain += 1
            name = herb_key.replace("_", " ")
            notes.append(f"**{name}** withdrawal: shaking, low spirits")
        if not used_today:
            # clean sunrise: tolerance fades
            entry["doses"] = max(0, doses - 1)
            if entry["doses"] == 0:
                log.pop(herb_key, None)
            changed = True

    fields: dict = {}
    if changed:
        fields["herb_use_log"] = json.dumps(log)

    if notes:
        if mood_delta:
            base_mood = int(user["mood"]) if "mood" in user.keys() else 50
            fields["mood"] = max(0, base_mood + mood_delta)
        if ex_gain:
            from engine.exhaustion_effects import EXHAUSTION_MAX
            old_ex = int(user["exhaustion"]) if "exhaustion" in user.keys() else 0
            fields["exhaustion"] = min(EXHAUSTION_MAX, old_ex + ex_gain)
        if pe_gain:
            from engine.exhaustion_effects import PAIN_EXHAUSTION_MAX
            old_pe = int(user["pain_exhaustion"]) if "pain_exhaustion" in user.keys() else 0
            fields["pain_exhaustion"] = min(PAIN_EXHAUSTION_MAX, old_pe + pe_gain)

    note = ("; ".join(notes) + ".") if notes else ""
    return fields, note