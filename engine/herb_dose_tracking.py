# herb_dose_tracking.py
"""Enforce daily dose limits for herbs that have a maximum per sunrise.

Some herbs (e.g., labrador tea, valerian, poppy) have a maximum daily dose
to prevent toxicity or overdose. This module tracks usage and rejects
additional doses beyond the limit, with optional side effects if overdosed.
"""

from __future__ import annotations

import json

# Define max doses per sunrise for specific herbs.
# Key: herb_key, value: max doses per day.
MAX_DAILY_DOSE: dict[str, int] = {
    "labrador_tea": 1,
    "valerian": 2,
    "poppy_seeds": 2,
    "dried_skullcap": 2,
    "snakeroot": 1,
}

# Herb keys that cause an overdose if the limit is exceeded.
OVERDOSE_HERBS = {
    "labrador_tea": "diarrhea",  # disease to contract on overdose
    "valerian": "insomnia",      # or perhaps "confusion"
    "poppy_seeds": "mild_poison",
    "dried_skullcap": "delirium",
    "snakeroot": "mild_poison",
}


def record_herb_dose(user, herb_key: str, day: int) -> dict:
    """
    Record that a dose of herb was taken today.
    Returns db fields to update (daily_use_log JSON).
    """
    if herb_key not in MAX_DAILY_DOSE:
        return {}  # no tracking needed

    log = _load_dose_log(user)
    # counts live under a dedicated "dose_counts" key so they coexist with the
    # diminishing-returns activity log in the same daily_use_log column.
    if "dose_counts" not in log:
        log["dose_counts"] = {}
    if herb_key not in log["dose_counts"]:
        log["dose_counts"][herb_key] = {}
    # Increment count for today.
    day_str = str(day)
    count = log["dose_counts"][herb_key].get(day_str, 0) + 1
    log["dose_counts"][herb_key][day_str] = count
    return _save_dose_log(user, log)


def get_todays_dose_count(user, herb_key: str, day: int) -> int:
    """Return how many doses of this herb have been taken today."""
    log = _load_dose_log(user)
    if "dose_counts" not in log:
        return 0
    if herb_key not in log["dose_counts"]:
        return 0
    return int(log["dose_counts"][herb_key].get(str(day), 0))


def can_take_dose(user, herb_key: str, day: int) -> tuple[bool, str]:
    """Check if a wolf can take another dose of this herb today."""
    max_dose = MAX_DAILY_DOSE.get(herb_key)
    if max_dose is None:
        return True, ""
    count = get_todays_dose_count(user, herb_key, day)
    if count >= max_dose:
        return False, f"daily limit reached for **{herb_key.replace('_',' ')}** ({max_dose} per sunrise)."
    return True, ""


def check_herb_overdose(user, herb_key: str, day: int) -> tuple[bool, str, str]:
    """
    After taking a dose, check if the wolf has exceeded the limit.
    Returns (overdose_occurred, disease_to_contract, message).
    """
    max_dose = MAX_DAILY_DOSE.get(herb_key)
    if max_dose is None:
        return False, "", ""
    count = get_todays_dose_count(user, herb_key, day)
    if count > max_dose:
        overdose_disease = OVERDOSE_HERBS.get(herb_key)
        if overdose_disease:
            return True, overdose_disease, f"overdose of **{herb_key.replace('_',' ')}**; {overdose_disease} sets in."
        else:
            return True, "", f"overdose of **{herb_key.replace('_',' ')}**; toxic effects."
    return False, "", ""


def _load_dose_log(user) -> dict:
    raw = user["daily_use_log"] if user and "daily_use_log" in user.keys() else "{}"
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _save_dose_log(user, log: dict) -> dict:
    """Return a dict with the updated field."""
    return {"daily_use_log": json.dumps(log)}


def prune_old_dose_logs(user, current_day: int, keep_days: int = 7) -> dict:
    """
    Remove entries older than keep_days to prevent log bloat.
    Returns fields to update (if any).
    """
    log = _load_dose_log(user)
    if "dose_counts" not in log:
        return {}
    changed = False
    for herb_key, day_counts in list(log["dose_counts"].items()):
        for day_str in list(day_counts.keys()):
            day = int(day_str)
            if current_day - day > keep_days:
                del day_counts[day_str]
                changed = True
        if not day_counts:
            del log["dose_counts"][herb_key]
            changed = True
    if changed:
        return _save_dose_log(user, log)
    return {}