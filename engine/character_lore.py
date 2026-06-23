"""Character lore; appearance, personality, backstory, family, RP sample (JSON on users)."""

from __future__ import annotations

import json

LORE_FIELDS = (
    "appearance",
    "personality",
    "backstory",
    "family_ties",
    "rp_sample",
    "open_plots",
)

LORE_LABELS = {
    "appearance": "Appearance",
    "personality": "Personality",
    "backstory": "Backstory",
    "family_ties": "Family",
    "rp_sample": "RP Sample",
    "open_plots": "Open Plots",
}


def _user_lore_raw(user) -> str | None:
    if not user:
        return None
    try:
        if hasattr(user, "keys") and "character_lore" in user.keys():
            return user["character_lore"]
        if isinstance(user, dict):
            return user.get("character_lore")
    except (KeyError, TypeError):
        return None
    return None


def parse_character_lore(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    clean = {k: str(v).strip() for k, v in data.items() if k in LORE_FIELDS and v}
    return clean or None


def encode_character_lore(**fields: str) -> str:
    payload = {k: fields[k].strip() for k in LORE_FIELDS if fields.get(k, "").strip()}
    return json.dumps(payload)


def has_character_lore(user) -> bool:
    return parse_character_lore(_user_lore_raw(user)) is not None


def format_lore_profile_hint(user) -> str | None:
    lore = parse_character_lore(_user_lore_raw(user))
    if not lore:
        return None
    parts = []
    if lore.get("appearance"):
        text = lore["appearance"]
        if len(text) > 180:
            text = text[:177] + "…"
        parts.append(text)
    return "\n".join(parts) if parts else "Lore on file; use `/profile sheet:true` for the full sheet."


def lore_embed_fields(user) -> list[tuple[str, str]]:
    """Return (name, value) pairs for Discord embed fields."""
    lore = parse_character_lore(_user_lore_raw(user))
    if not lore:
        return []
    out: list[tuple[str, str]] = []
    for key in LORE_FIELDS:
        text = lore.get(key)
        if not text:
            continue
        if len(text) > 1024:
            text = text[:1021] + "…"
        out.append((LORE_LABELS[key], text))
    return out
