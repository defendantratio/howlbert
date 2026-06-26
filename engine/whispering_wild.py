"""Whispering Wild-inspired fog spirits, swamp whispers, and unease."""

from __future__ import annotations

import random

from config import WHISPERING_SNIFF_ANXIETY_CHANCE, WHISPERING_SPIRIT_LINES, WHISPERING_WEATHER
from engine.disease_contract import has_disease, try_contract_disease
from engine.role_features import has_any_role


def is_whispering_weather(weather: str | None) -> bool:
    return bool(weather and weather.lower() in WHISPERING_WEATHER)


def _whispering_affinity(user) -> bool:
    if not user:
        return False
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    if gp == "mistmoor":
        return True
    if has_any_role(user, "drown_sick"):
        return True
    return False


def spirit_whisper_on_sniff(user, *, weather: str) -> str | None:
    """
    Fog/rain/storm sniff: spirit flavor; Mistmoor & Drown-Sick may contract early anxiety.
    Returns extra embed lines or None.
    """
    if not is_whispering_weather(weather):
        return None
    line = random.choice(WHISPERING_SPIRIT_LINES)
    bits = [f"_{line}_"]
    if _whispering_affinity(user) and not has_disease(user):
        from engine.supernatural import has_spirit_curse, maybe_curse_from_whisper

        curse_note = maybe_curse_from_whisper(user, weather=weather)
        if curse_note:
            bits.append(f"\n\n**{curse_note}**")
        elif not has_spirit_curse(user):
            ill = try_contract_disease(
                user,
                "anxiety",
                "uneasy",
                chance=WHISPERING_SNIFF_ANXIETY_CHANCE,
            )
            if ill:
                bits.append(f"\n\n**Whispering unease**; {ill}")
        elif has_spirit_curse(user):
            bits.append("\n\n_The curse answers the fog; the whispers are louder tonight._")
    return "\n".join(bits)


def format_mental_rounds_line(user) -> str | None:
    """Medic rounds: flag wolves with mental illness (Warriors cough-check style)."""
    from engine.mental_effects import _parsed
    from engine.diseases import get_stage_info

    key, stage = _parsed(user)
    if not key or not stage:
        return None
    info = get_stage_info(key, stage)
    label = info["name"] if info else key.replace("_", " ").title()
    return f"**{user['wolf_name']}**: {label}"
