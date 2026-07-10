"""Enforce daily dose limits for herbs that have a maximum per sunrise.

Some herbs (e.g., labrador tea, valerian, poppy) have a maximum daily dose to
prevent toxicity. This module tracks usage in the ``daily_use_log`` column
(under a dedicated ``dose_counts`` key so it coexists with the diminishing
returns activity log) and reports a soft overdose (the wolf gets sick) when the
cap is exceeded, rather than hard-blocking the treatment.
"""

from __future__ import annotations

import json

# max doses per sunrise for specific herbs (herb_key -> max doses/day).
MAX_DAILY_DOSE: dict[str, int] = {
    "labrador_tea": 1,
    "valerian": 2,
    "poppy_seeds": 2,
    "dried_skullcap": 2,
    "snakeroot": 1,
}

# herbs that cause a disease if the daily limit is exceeded (herb_key -> disease key).
OVERDOSE_HERBS: dict[str, str] = {
    "labrador_tea": "diarrhea",
    "valerian": "insomnia",
    "poppy_seeds": "mild_poison",
    "dried_skullcap": "delirium",
    "snakeroot": "mild_poison",
}


def _load_dose_log(user) -> dict:
    raw = user["daily_use_log"] if user and "daily_use_log" in user.keys() else "{}"
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def get_todays_dose_count(user, herb_key: str, day: int) -> int:
    """How many doses of this herb the wolf has taken today."""
    counts = _load_dose_log(user).get("dose_counts", {})
    return int(counts.get(herb_key, {}).get(str(day), 0))


def record_herb_dose(user, herb_key: str, day: int) -> dict:
    """Record one dose of ``herb_key`` today. Returns db fields to persist
    (empty for herbs without a daily cap)."""
    if herb_key not in MAX_DAILY_DOSE:
        return {}
    log = _load_dose_log(user)
    counts = log.setdefault("dose_counts", {})
    herb_days = counts.setdefault(herb_key, {})
    day_str = str(day)
    herb_days[day_str] = int(herb_days.get(day_str, 0)) + 1
    return {"daily_use_log": json.dumps(log)}


def can_take_dose(user, herb_key: str, day: int) -> tuple[bool, str]:
    """Whether the wolf is still under the daily cap for this herb."""
    max_dose = MAX_DAILY_DOSE.get(herb_key)
    if max_dose is None:
        return True, ""
    if get_todays_dose_count(user, herb_key, day) >= max_dose:
        return False, f"daily limit reached for **{herb_key.replace('_', ' ')}** ({max_dose} per sunrise)."
    return True, ""


def check_herb_overdose(user, herb_key: str, day: int) -> tuple[bool, str, str]:
    """After a dose is recorded, report whether the wolf has exceeded the cap.
    Returns (overdosed, disease_key_or_empty, message)."""
    max_dose = MAX_DAILY_DOSE.get(herb_key)
    if max_dose is None:
        return False, "", ""
    if get_todays_dose_count(user, herb_key, day) > max_dose:
        disease = OVERDOSE_HERBS.get(herb_key, "")
        tail = f"{disease.replace('_', ' ')} sets in." if disease else "toxic effects set in."
        return True, disease, f"overdose of **{herb_key.replace('_', ' ')}**; {tail}"
    return False, "", ""
