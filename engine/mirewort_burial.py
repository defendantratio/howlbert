"""Mirewort's grave-planting habit (lore: pups buried under herb roots)."""

from __future__ import annotations

import random

from herbs import HERBS

MIREWORT_NAME = "mirewort"

# Herbs he presses into wolf graves and carcass mounds.
MIREWORT_GRAVE_HERBS: tuple[str, ...] = (
    "marsh_mallow",
    "lavender",
    "rosemary",
    "meadowsweet",
    "garden_mint",
    "yarrow",
    "stinging_nettle",
    "willow_bark",
    "sweet_sedge",
    "lungwort",
)

_MOURNING_LINES: tuple[str, ...] = (
    (
        "**{name}**'s mound is still wet when he presses **{herb}** into the soil and "
        "whispers their name; by next moon the grave will show green."
    ),
    (
        "He lays **{herb}** over **{name}**'s folded earth the way he buried pups in rot-season; "
        "medicine growing out of what the Maw took."
    ),
    (
        "Bitter roots go in last: **{herb}**, so **{name}**'s resting place will be "
        "easy to find when the swamp forgets everything else."
    ),
)


def is_mirewort(user) -> bool:
    name = (user["wolf_name"] if "wolf_name" in user.keys() else "") or ""
    return name.strip().casefold() == MIREWORT_NAME


def _herb_label(key: str) -> str:
    return HERBS.get(key, {}).get("name", key.replace("_", " ").title())


def _pick_grave_herb(herb_key: str | None = None) -> str:
    key = herb_key or random.choice(MIREWORT_GRAVE_HERBS)
    return _herb_label(key)


def mirewort_grave_rite(
    deceased_name: str,
    *,
    custom_words: str | None = None,
    herb_key: str | None = None,
) -> tuple[str, str]:
    """
    Mourning speech + short journal note when Mirewort leads a rite.
    Returns (embed_speech, journal_line).
    """
    herb = _pick_grave_herb(herb_key)
    plant_line = random.choice(_MOURNING_LINES).format(herb=herb, name=deceased_name)
    if custom_words and custom_words.strip():
        speech = f"{custom_words.strip()}\n\n{plant_line}"
    else:
        speech = plant_line
    journal = f"grave planted with **{herb}**."
    return speech, journal


def mirewort_carcass_burial_note(
    *,
    herb_key: str | None = None,
    ritual_herb_key: str | None = None,
) -> str:
    """Extra line on `/bury` when Mirewort scrapes earth over carrion."""
    if ritual_herb_key and ritual_herb_key in MIREWORT_GRAVE_HERBS:
        herb = _herb_label(ritual_herb_key)
        return (
            f"\n\n_habit from rot-lung seasons: **{herb}** takes on the mound; "
            f"the grave will green even though the carcass is gone._"
        )
    herb = _pick_grave_herb(herb_key)
    return (
        f"\n\n_without thinking, he tucks **{herb}** cuttings along the mound's edge; "
        f"respect for the hole, not the meat._"
    )
