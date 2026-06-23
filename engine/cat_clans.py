"""Forest cat clans; names and validation for wolf-cat pacts."""

from __future__ import annotations

import re

# Generic clan names (not tied to copyrighted Warrior Cats clans).
KNOWN_CAT_CLANS: tuple[str, ...] = (
    "MossClan",
    "PineClan",
    "AshClan",
    "StreamClan",
    "HollowClan",
    "MistClan",
    "BriarClan",
    "FernClan",
    "StoneClan",
)

_CLAN_RE = re.compile(r"^[A-Za-z][A-Za-z\s\-']{1,22}[A-Za-z]$")


def normalize_clan_name(name: str) -> str:
    return name.strip()


def validate_clan_name(name: str) -> tuple[str | None, str | None]:
    name = normalize_clan_name(name)
    if len(name) < 3 or len(name) > 24:
        return None, "Clan name must be 3-24 characters."
    if not _CLAN_RE.match(name):
        return None, "Use letters, spaces, or hyphens only (e.g. **MossClan**)."
    return name, None


def rival_clans(allied_clan: str) -> list[str]:
    allied = allied_clan.casefold()
    return [c for c in KNOWN_CAT_CLANS if c.casefold() != allied]


def pick_rival_clan(allied_clan: str) -> str:
    import random

    rivals = rival_clans(allied_clan)
    if rivals:
        return random.choice(rivals)
    return allied_clan
