"""Wolf pronouns: lore canon (incl. neopronouns), then birth sex; adapt displayed prose."""

from __future__ import annotations

import re

PRONOUNS_FOR_BIRTH_SEX = {
    "female": "she/her",
    "male": "he/him",
    "intersex": "they/them",
    "nonbinary": "they/them",
}

# Lore characters where prose inference is wrong or neopronouns are not she/he.
CHARACTER_PRONOUN_OVERRIDES: dict[str, str] = {
    "Rotteddust": "ey/em",
    "Stonepiercer": "xe/xir",
    "Frostburn": "ze/hir",
    "Ebb": "ae/aer",
    "Curlgrip": "fae/faer",
    "Gasp": "they/them",
    "Barkhollow": "he/she",
    "Ashbark": "he/him",
    "Mosspup": "he/him",
}

# Named roles: subject, object, possessive determiner, possessive pronoun, reflexive
_PRONOUN_FORMS: dict[str, dict[str, tuple[str, str]]] = {
    "he/him": {
        "subj": ("he", "He"),
        "obj": ("him", "Him"),
        "poss_det": ("his", "His"),
        "poss_pron": ("his", "His"),
        "refl": ("himself", "Himself"),
    },
    "she/her": {
        "subj": ("she", "She"),
        "obj": ("her", "Her"),
        "poss_det": ("her", "Her"),
        "poss_pron": ("hers", "Hers"),
        "refl": ("herself", "Herself"),
    },
    "they/them": {
        "subj": ("they", "They"),
        "obj": ("them", "Them"),
        "poss_det": ("their", "Their"),
        "poss_pron": ("theirs", "Theirs"),
        "refl": ("themselves", "Themselves"),
    },
    "ey/em": {
        "subj": ("ey", "Ey"),
        "obj": ("em", "Em"),
        "poss_det": ("eir", "Eir"),
        "poss_pron": ("eirs", "Eirs"),
    },
    "fae/faer": {
        "subj": ("fae", "Fae"),
        "obj": ("faer", "Faer"),
        "poss_det": ("faer", "Faer"),
        "poss_pron": ("faers", "Faers"),
    },
    "ae/aer": {
        "subj": ("ae", "Ae"),
        "obj": ("aer", "Aer"),
        "poss_det": ("aer", "Aer"),
        "poss_pron": ("aers", "Aers"),
    },
    "xe/xir": {
        "subj": ("xe", "Xe"),
        "obj": ("xir", "Xir"),
        "poss_det": ("xir", "Xir"),
        "poss_pron": ("xirs", "Xirs"),
    },
    "ze/hir": {
        "subj": ("ze", "Ze"),
        "obj": ("hir", "Hir"),
        "poss_det": ("hir", "Hir"),
        "poss_pron": ("hirs", "Hirs"),
    },
}

_ROLE_ORDER = ("refl", "poss_det", "poss_pron", "obj", "subj")

_APPEARANCE_PRONOUN_RE = re.compile(
    r"pronouns:\s*([a-z]{1,4}/[a-z]{1,4}(?:/[a-z]{1,4})?)",
    re.IGNORECASE,
)
_NONBINARY_PRONOUN_RE = re.compile(
    r"nonbinary\s*\(\s*([a-z]{1,4}/[a-z]{1,4}(?:/[a-z]{1,4})?)\s*\)",
    re.IGNORECASE,
)
_SHE_RE = re.compile(r"\b[Ss]he\b|\b[Hh]er\b|\b[Hh]ers\b")
_HE_RE = re.compile(r"\b[Hh]e\b|\b[Hh]is\b|\b[Hh]im\b")
_THEY_RE = re.compile(r"\b[Tt]hey\b|\b[Tt]heir\b|\b[Tt]hem\b")


def normalize_pronoun_key(pronouns: str | None) -> str | None:
    if not pronouns or not str(pronouns).strip():
        return None
    parts = str(pronouns).strip().lower().split("/")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def pronouns_for_birth_sex(birth_sex: str | None) -> str | None:
    if not birth_sex:
        return None
    return PRONOUNS_FOR_BIRTH_SEX.get(str(birth_sex).strip().lower())


def _parse_pronouns_from_appearance(text: str) -> str | None:
    if not text:
        return None
    for pattern in (_APPEARANCE_PRONOUN_RE, _NONBINARY_PRONOUN_RE):
        match = pattern.search(text)
        if match:
            return normalize_pronoun_key(match.group(1))
    return None


def _infer_pronouns_from_prose(blob: str) -> str | None:
    if not blob:
        return None
    she = len(_SHE_RE.findall(blob))
    he = len(_HE_RE.findall(blob))
    they = len(_THEY_RE.findall(blob))
    if max(she, he, they) == 0:
        return None
    if she >= 2 and he >= 2 and min(she, he) / max(she, he) >= 0.35:
        return "he/she"
    if she > he and she >= they:
        return "she/her"
    if he > she and he >= they:
        return "he/him"
    if they >= she and they >= he:
        return "they/them"
    return None


def canonical_pronouns_for_name(wolf_name: str) -> str | None:
    """pronouns from lore for a canonical character name, or none if not on file."""
    key = (wolf_name or "").strip()
    if not key:
        return None
    for name, pronouns in CHARACTER_PRONOUN_OVERRIDES.items():
        if name.lower() == key.lower():
            return pronouns

    from engine.character_lore import parse_character_lore
    from engine.character_lore_data import CHARACTER_LORE_BY_NAME

    lore_raw = None
    for name, raw in CHARACTER_LORE_BY_NAME.items():
        if name.lower() == key.lower():
            lore_raw = raw
            break
    if not lore_raw:
        return None

    lore = parse_character_lore(lore_raw) or {}
    appearance = lore.get("appearance", "")
    parsed = _parse_pronouns_from_appearance(appearance)
    if parsed:
        return parsed

    blob = " ".join(
        lore.get(field, "")
        for field in ("personality", "backstory", "rp_sample", "family_ties")
    )
    return _infer_pronouns_from_prose(blob)


def lore_baseline_pronouns(user) -> str | None:
    """pronouns the wolf's lore/trait text was written with."""
    wolf_name = None
    birth_sex = None
    if hasattr(user, "keys"):
        if "wolf_name" in user.keys():
            wolf_name = user["wolf_name"]
        if "birth_sex" in user.keys():
            birth_sex = user["birth_sex"]
    elif isinstance(user, dict):
        wolf_name = user.get("wolf_name")
        birth_sex = user.get("birth_sex")
    canon = canonical_pronouns_for_name(wolf_name or "")
    if canon:
        return canon
    return pronouns_for_birth_sex(birth_sex)


def resolve_wolf_pronouns(
    wolf_name: str | None,
    *,
    birth_sex: str | None = None,
    explicit: str | None = None,
) -> str | None:
    """Profile/display pronouns: manual override, lore canon, then birth sex."""
    if explicit and str(explicit).strip():
        return str(explicit).strip()
    canon = canonical_pronouns_for_name(wolf_name or "")
    if canon:
        return canon
    return pronouns_for_birth_sex(birth_sex)


def wolf_pronouns(user) -> str | None:
    explicit = None
    birth_sex = None
    wolf_name = None
    if hasattr(user, "keys"):
        if "pronouns" in user.keys():
            explicit = user["pronouns"]
        if "birth_sex" in user.keys():
            birth_sex = user["birth_sex"]
        if "wolf_name" in user.keys():
            wolf_name = user["wolf_name"]
    elif isinstance(user, dict):
        explicit = user.get("pronouns")
        birth_sex = user.get("birth_sex")
        wolf_name = user.get("wolf_name")
    return resolve_wolf_pronouns(wolf_name, birth_sex=birth_sex, explicit=explicit)


def _substitution_source_keys(source: str, target: str) -> list[str]:
    source = normalize_pronoun_key(source) or source
    target = normalize_pronoun_key(target) or target
    if source == target:
        return []
    if source == "he/she":
        if target == "she/her":
            return ["he/him"]
        if target == "he/him":
            return ["she/her"]
        return ["he/him", "she/her"]
    return [source]


def _replace_word(text: str, old: str, new: str) -> str:
    if old == new:
        return text

    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        if word[0].isupper():
            return new[0].upper() + new[1:]
        return new

    return re.sub(rf"\b{re.escape(old)}\b", repl, text)


def adapt_prose_pronouns(
    text: str,
    target: str | None,
    *,
    source: str | None,
) -> str:
    """Rewrite third-person pronouns in lore/trait blurbs for display."""
    if not text or not target or not source:
        return text
    target_key = normalize_pronoun_key(target)
    if not target_key or target_key not in _PRONOUN_FORMS:
        return text
    target_forms = _PRONOUN_FORMS[target_key]
    out = text
    for source_key in _substitution_source_keys(source, target_key):
        source_key = normalize_pronoun_key(source_key)
        if not source_key or source_key not in _PRONOUN_FORMS:
            continue
        source_forms = _PRONOUN_FORMS[source_key]
        for role in _ROLE_ORDER:
            if role not in source_forms or role not in target_forms:
                continue
            old_lower, old_title = source_forms[role]
            new_lower, new_title = target_forms[role]
            out = _replace_word(out, old_title, new_title)
            out = _replace_word(out, old_lower, new_lower)
    if target_key != normalize_pronoun_key(source):
        out = _APPEARANCE_PRONOUN_RE.sub(f"pronouns: {target}.", out)
        out = _NONBINARY_PRONOUN_RE.sub(f"nonbinary ({target})", out)
    return out


def adapt_text_for_user(text: str, user) -> str:
    """rewrite lore/trait prose when display pronouns differ from the written baseline."""
    baseline = lore_baseline_pronouns(user)
    target = wolf_pronouns(user)
    if not baseline or not target:
        return text
    base_key = normalize_pronoun_key(baseline) or baseline
    target_key = normalize_pronoun_key(target) or target
    if base_key == target_key and baseline != "he/she":
        return text
    if baseline == "he/she" and target == "he/she":
        return text
    return adapt_prose_pronouns(text, target, source=baseline)
