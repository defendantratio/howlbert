"""Parse a Discord-exported RP character sheet into /register fields.

Staff write character sheets as plain markdown in a wolf's dedicated channel
(``**Name:**``, ``**Pack:**``, ``**Rank:**``, ...). This turns that text into
the same arguments ``database.register_user`` takes, so importing a sheet is
one admin command instead of a one-off script. Canonical lore/skills/role
overrides/bonds still attach automatically inside ``register_user`` by exact
wolf-name match; this module only resolves *which* name to register under.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from config import GREAT_PACKS, LONER_KEY, ROGUE_KEY

ROLE_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("alpha", "alpha"),
    ("second", "advisor"),
    ("beta", "advisor"),
    ("advisor", "advisor"),
    ("elder", "elder"),
    ("medic apprentice", "medic_apprentice"),
    ("healer apprentice", "medic_apprentice"),
    ("medic", "medic"),
    ("healer", "medic"),
    ("scout apprentice", "scout_apprentice"),
    ("scout", "scout"),
    ("forager apprentice", "forager_apprentice"),
    ("forager", "forager"),
    ("diplomat apprentice", "diplomat_apprentice"),
    ("diplomat", "diplomat"),
    ("caretaker apprentice", "caretaker_apprentice"),
    ("caretaker", "caretaker"),
    ("hunter apprentice", "hunter_apprentice"),
    ("hunter", "hunter"),
    ("drown-sick", "drown_sick"),
    ("drown sick", "drown_sick"),
    ("bog-born", "bog_born"),
    ("bog born", "bog_born"),
    ("rogue", "rogue"),
    ("lowbelly", "lowbelly"),
    ("pup", "pup"),
    ("juvenile", "juvenile"),
    ("guard", "guard"),
)

SEXUALITY_MAP: dict[str, str] = {
    "heterosexual": "heterosexual",
    "straight": "heterosexual",
    "homosexual": "homosexual",
    "gay": "homosexual",
    "bisexual": "bisexual",
    "pansexual": "pansexual",
    "asexual": "asexual",
    "demisexual": "demisexual",
    "demiromantic": "demiromantic",
}

# Sheet "Name:" text that doesn't reduce to its canonical engine key by simple
# punctuation-stripping (full titles, working titles). Keys here must already
# be run through _normalize() (lowercase, non-alnum stripped). Checked after
# the generic punctuation-insensitive match in resolve_canonical_name.
KNOWN_NAME_ALIASES: dict[str, str] = {
    "ladysyphadelarosa": "Sypha",
    "sootpaw": "Soot",
}


@dataclass
class ParsedSheet:
    raw_name: str
    wolf_name: str
    canonical_match: bool
    pack_text: str | None
    rank_text: str | None
    age_text: str | None
    sexuality_text: str | None
    gender_text: str | None
    affiliation: str | None
    role: str
    age_months: int | None
    birth_sex: str | None
    sexuality: str | None
    avatar_url: str | None


def field(text: str, label: str) -> str | None:
    """Read a sheet field; supports ``**Label:** value`` and bare ``Label: value``."""
    m = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.+)", text)
    if m:
        return m.group(1).strip().rstrip("\\").strip()
    m = re.search(rf"(?m)^{re.escape(label)}:\s*(.+)$", text)
    if m:
        return m.group(1).strip().rstrip("\\").strip()
    return None


def detect_role(rank_text: str | None) -> str:
    if not rank_text:
        return "hunter"
    low = rank_text.lower()
    for kw, role in ROLE_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", low):
            return role
    return "hunter"


def detect_age_months(age_text: str | None) -> int | None:
    if not age_text:
        return None
    low = age_text.lower()
    m = re.search(r"(\d+)\s*(years?|yrs?)", low)
    if m:
        return int(m.group(1)) * 12
    m = re.search(r"(\d+)\s*(moons?|months?)", low)
    if m:
        return int(m.group(1))
    return None


def detect_birth_sex(gender_text: str | None) -> str | None:
    if not gender_text:
        return None
    low = gender_text.lower()
    if "nonbinary" in low or "non-binary" in low or "non binary" in low:
        return "nonbinary"
    if "female" in low or "she-wolf" in low or low.startswith("she"):
        return "female"
    if "male" in low or "he-wolf" in low or low.startswith("he"):
        return "male"
    return None


def detect_sexuality(sex_text: str | None) -> str | None:
    if not sex_text:
        return None
    low = sex_text.lower()
    for key, val in SEXUALITY_MAP.items():
        if key in low:
            return val
    return None


def detect_pack(pack_text: str | None) -> str | None:
    """Best-effort pack affiliation from the sheet's own Pack field text."""
    if not pack_text:
        return None
    low = pack_text.lower()
    if "rogue" in low:
        return ROGUE_KEY
    if "none" in low or "loner" in low or "lone wolf" in low:
        return LONER_KEY
    for key in GREAT_PACKS:
        if key in low:
            return key
    return None


def extract_avatar_url(text: str) -> str | None:
    m = re.search(
        r"https://cdn\.discordapp\.com/attachments/\S+\.(?:png|jpg|jpeg|gif|webp)\S*",
        text,
    )
    return m.group(0) if m else None


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def resolve_canonical_name(raw_name: str) -> tuple[str, bool]:
    """
    Match a sheet's parsed name against the bot's built-in canon names
    (engine.character_lore_data.CHARACTER_LORE_BY_NAME), so registering
    under the right spelling auto-attaches lore/skills/bonds.

    Returns (name_to_register_as, matched_canon).
    """
    from engine.character_lore_data import CHARACTER_LORE_BY_NAME

    name = raw_name.split(" (")[0].strip().strip("“”\"")

    def _display_case(key: str) -> str:
        # a couple of canon keys (e.g. "mirewort") are stored all-lowercase;
        # title-case those for nicer display, everything else keeps its
        # canon casing exactly (RiverShroud, Pale'Step, Finnpelt, ...).
        return key.capitalize() if key.islower() else key

    alias = KNOWN_NAME_ALIASES.get(_normalize(raw_name)) or KNOWN_NAME_ALIASES.get(
        _normalize(name)
    )
    if alias:
        return alias, True

    for key in CHARACTER_LORE_BY_NAME:
        if key.lower() == name.lower():
            return _display_case(key), True

    target = _normalize(name)
    for key in CHARACTER_LORE_BY_NAME:
        if _normalize(key) == target:
            return _display_case(key), True

    return name[:32], False


def parse_character_sheet(text: str) -> ParsedSheet | None:
    """Parse a pasted/attached sheet's text. Returns None if no Name field found."""
    raw_name = field(text, "Name")
    if not raw_name or raw_name.startswith("**"):
        return None

    wolf_name, canonical_match = resolve_canonical_name(raw_name)

    pack_text = field(text, "Pack")
    rank_text = field(text, "Rank")
    age_text = field(text, "Age")
    sexuality_text = field(text, "Sexuality")
    gender_text = field(text, "Gender/Pronouns") or field(text, "Gender")

    return ParsedSheet(
        raw_name=raw_name,
        wolf_name=wolf_name,
        canonical_match=canonical_match,
        pack_text=pack_text,
        rank_text=rank_text,
        age_text=age_text,
        sexuality_text=sexuality_text,
        gender_text=gender_text,
        affiliation=detect_pack(pack_text),
        role=detect_role(rank_text),
        age_months=detect_age_months(age_text),
        birth_sex=detect_birth_sex(gender_text),
        sexuality=detect_sexuality(sexuality_text),
        avatar_url=extract_avatar_url(text),
    )
