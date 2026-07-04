"""Fallback method requirements per disease — used when the herb itself has no override."""

from __future__ import annotations

DEFAULT_METHOD_REQS: dict[str, str] = {
    "cough": "tea",
    "leafbare_cough": "tea",
    "yellowcough": "tea",
    "rot_lung": "tea",
    "bronchitis": "tea",
    "asthma": "tea",
    "influenza": "tea",
    "hard_paw": "tea",
    "diarrhea": "tea",
    "constipation": "tea",
    "eating_distress": "tea",
    "wasting_sickness": "tea",
    "deep_gash": "poultice",
    "infected_wound": "poultice",
    "festering_wound": "poultice",
    "punctured_paw": "poultice",
    "torn_claw": "poultice",
    "scorched_hide": "ointment",
    "mild_poison": "juice",
    "poison_ivy": "sap",
    "mange": "ointment",
    "fleas": "rub",
    "anxiety": "tea",
    "insomnia": "tea",
    "night_terrors": "tea",
    "grief_melancholy": "tea",
    "shock_emotional": "tea",
}
