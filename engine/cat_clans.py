"""Forest cat clans; Warrior Cats canon names for wolf–cat pacts."""

from __future__ import annotations

import random
import re

# Four lake-territory Clans (Warrior Cats canon).
KNOWN_CAT_CLANS: tuple[str, ...] = (
    "ThunderClan",
    "ShadowClan",
    "WindClan",
    "RiverClan",
)

# Older generic names → canon (existing DB pacts keep their stored name).
LEGACY_CAT_CLAN_ALIASES: dict[str, str] = {
    "mossclan": "ThunderClan",
    "pineclan": "ShadowClan",
    "ashclan": "WindClan",
    "streamclan": "RiverClan",
    "hollowclan": "ShadowClan",
    "mistclan": "RiverClan",
    "briarclan": "WindClan",
    "fernclan": "ThunderClan",
    "stoneclan": "ThunderClan",
    "skyclan": "ThunderClan",
}

# Lake-territory flavor (Warrior Cats setting).
CLAN_TERRITORY: dict[str, str] = {
    "ThunderClan": "the oak forest and Sunningrocks",
    "ShadowClan": "the pine shadows and marsh edge",
    "WindClan": "the open moors and rabbit runs",
    "RiverClan": "the river, gorge, and reed beds",
}

CLAN_PATROL_SCENT: dict[str, tuple[str, ...]] = {
    "ThunderClan": (
        "**ThunderClan** musk on the oaks; a patrol crossed the scent-line recently.",
        "Fresh claw-marks on the border trees; **ThunderClan** warriors were here at dawn.",
    ),
    "ShadowClan": (
        "Marsh-pine and sharp **ShadowClan** scent; something watches from the dark trees.",
        "The wind carries **ShadowClan** marks; patrol cats, not prey.",
    ),
    "WindClan": (
        "Open-moor scent and rabbit-trail dust; **WindClan** legs passed this ridge.",
        "**WindClan** musk on the heather; a border patrol is near.",
    ),
    "RiverClan": (
        "Fish-oil and river-silt on the wind; **RiverClan** patrol scent is fresh.",
        "Reed-bed musk and wet pawprints; **RiverClan** warriors marked the border.",
    ),
}

GENERIC_CAT_SCENT: tuple[str, ...] = (
    "Cat-musk on the wind; fresh marks on the border trees. A **Clan patrol** is watching.",
    "You catch forest-cat scent mixed with moss and claw-scratch. Warriors, not prey.",
    "The wind carries a sharp, alien musk; **cat territory** is close.",
    "A **Twoleg** trail lies far off; here, only Clan scent-marks and pine.",
)

ALLIED_STRAINED_SCENT: tuple[str, ...] = (
    "**{canon}** patrol scent on the wind; your treaty is strained and claws are close.",
    "A **{canon}** warrior's musk; allied on paper, hostile on the border tonight.",
    "You smell **{canon}** deputies before you see them; trust is thin and the patrol is tense.",
)

SETTING_TAGLINE = (
    "_Wolves share the lake territories with the warrior Clans; "
    "patrols, deputies, and the warrior code hold the forest._"
)

_CLAN_RE = re.compile(r"^[A-Za-z][A-Za-z\s\-']{1,22}[A-Za-z]$")


def format_four_clans() -> str:
    return ", ".join(f"**{c}**" for c in KNOWN_CAT_CLANS)


def normalize_clan_name(name: str) -> str:
    return name.strip()


def canon_clan_name(name: str) -> str | None:
    """return canonical clan spelling, or none if not a known clan."""
    raw = normalize_clan_name(name)
    if not raw:
        return None
    folded = raw.casefold().replace(" ", "")
    if folded in LEGACY_CAT_CLAN_ALIASES:
        return LEGACY_CAT_CLAN_ALIASES[folded]
    for clan in KNOWN_CAT_CLANS:
        if clan.casefold() == raw.casefold():
            return clan
    return None


def clan_territory_line(clan_name: str) -> str:
    canon = canon_clan_name(clan_name) or clan_name
    where = CLAN_TERRITORY.get(canon, "the forest")
    return f"**{canon}** holds {where}."


def sniff_cat_scent_line(
    *,
    allied_clan: str | None = None,
    rival_clan: str | None = None,
    allied_patrol: bool = False,
) -> str:
    """Border scent before a /sniff cat fight."""
    if allied_patrol and allied_clan:
        canon = canon_clan_name(allied_clan) or allied_clan
        return random.choice(ALLIED_STRAINED_SCENT).format(canon=canon)
    if rival_clan:
        canon = canon_clan_name(rival_clan) or rival_clan
        lines = CLAN_PATROL_SCENT.get(canon)
        if lines:
            return random.choice(lines)
    if allied_clan:
        canon = canon_clan_name(allied_clan) or allied_clan
        return (
            f"rival **clan** scent cuts across **{canon}**'s border; "
            "a patrol blocks the trail."
        )
    return random.choice(GENERIC_CAT_SCENT)


def receive_border_flavor(clan_name: str, *, trust: int) -> str:
    canon = canon_clan_name(clan_name) or clan_name
    where = CLAN_TERRITORY.get(canon, "the border")
    if trust >= 75:
        return (
            f"a **{canon}** patrol left the bundle at the scent-line near {where}; "
            "the deputy nodded you through."
        )
    return f"**{canon}** warriors dropped goods at the border stones by {where}."


def barter_border_flavor(clan_name: str) -> str:
    canon = canon_clan_name(clan_name) or clan_name
    return (
        f"at the **{canon}** border, warriors trade spare prey and herbs "
        "for wolf hoard scraps; no blood, just barter."
    )


def forge_success_flavor(clan_name: str) -> str:
    canon = canon_clan_name(clan_name) or clan_name
    where = CLAN_TERRITORY.get(canon, "the forest")
    return (
        f"clan deputies and your **alpha** mark the stones between wolf runs and {where}."
    )


def validate_clan_name(name: str) -> tuple[str | None, str | None]:
    name = normalize_clan_name(name)
    if len(name) < 3 or len(name) > 24:
        return None, "clan name must be 3-24 characters."
    if not _CLAN_RE.match(name):
        return None, "use letters only (e.g. **thunderclan**)."
    canon = canon_clan_name(name)
    if canon:
        return canon, None
    # Allow legacy stored names (old pacts) but steer new treaties to canon.
    if name.casefold().replace(" ", "") in LEGACY_CAT_CLAN_ALIASES:
        return LEGACY_CAT_CLAN_ALIASES[name.casefold().replace(" ", "")], None
    return None, f"pick one of the four forest clans: {format_four_clans()}."


def rival_clans(allied_clan: str) -> list[str]:
    allied = canon_clan_name(allied_clan) or allied_clan
    return [c for c in KNOWN_CAT_CLANS if c.casefold() != allied.casefold()]


def pick_rival_clan(allied_clan: str) -> str:
    rivals = rival_clans(allied_clan)
    if rivals:
        return random.choice(rivals)
    return random.choice(KNOWN_CAT_CLANS)


# Original patrol cats (WC-style names; not canon characters).
CLAN_CAT_NAMES: dict[str, dict[str, tuple[str, ...]]] = {
    "ThunderClan": {
        "deputy": ("Bramblestripe", "Oakwhisker", "Fernlight"),
        "warrior": ("Mossclaw", "Thrushpaw", "Sorrelstripe", "Dustfern"),
    },
    "ShadowClan": {
        "deputy": ("Nightfern", "Russetfang", "Bogwhisker"),
        "warrior": ("Pinetail", "Marshstripe", "Crowfur", "Snaketooth"),
    },
    "WindClan": {
        "deputy": ("Heatherwind", "Gorsestep", "Rabbitear"),
        "warrior": ("Moorrunner", "Hareflight", "Breezetail", "Gorseclaw"),
    },
    "RiverClan": {
        "deputy": ("Reedshine", "Ottersplash", "Minnowstripe"),
        "warrior": ("Fishscale", "Ripplefur", "Duskstream", "Willowripple"),
    },
}

_ROLE_LABELS = {
    "clan_deputy": "deputy",
    "clan_warrior": "warrior",
}


def pick_border_cat_display_name(clan_name: str, template_key: str) -> str | None:
    """Return e.g. Bramblestripe (ThunderClan deputy), or None for rogues/loners."""
    role = _ROLE_LABELS.get(template_key)
    if not role:
        return None
    canon = canon_clan_name(clan_name) or clan_name
    pool = CLAN_CAT_NAMES.get(canon, {}).get(role)
    if not pool:
        return None
    cat = random.choice(pool)
    return f"{cat} ({canon} {role})"
