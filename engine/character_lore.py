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
    "appearance": "appearance",
    "personality": "personality",
    "backstory": "backstory",
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


def _wolf_name(user) -> str:
    if hasattr(user, "keys") and "wolf_name" in user.keys():
        return user["wolf_name"] or ""
    if isinstance(user, dict):
        return user.get("wolf_name") or ""
    return ""


def lore_for_display(user) -> dict | None:
    """canonical lore sheet when on file; else the wolf's stored copy."""
    from engine.character_lore_data import CHARACTER_LORE_BY_NAME

    name = _wolf_name(user).lower()
    if name:
        for key, raw in CHARACTER_LORE_BY_NAME.items():
            if key.lower() == name:
                return parse_character_lore(raw)
    return parse_character_lore(_user_lore_raw(user))




def lore_embed_fields(user) -> list[tuple[str, str]]:
    """Return (name, value) pairs for Discord embed fields."""
    from engine.pronouns import adapt_text_for_user

    lore = lore_for_display(user)
    if not lore:
        return []
    out: list[tuple[str, str]] = []
    for key in LORE_FIELDS:
        text = lore.get(key)
        if not text:
            continue
        text = adapt_text_for_user(text, user)
        if len(text) > 1024:
            text = text[:1021] + "…"
        out.append((LORE_LABELS[key], text))
    return out
