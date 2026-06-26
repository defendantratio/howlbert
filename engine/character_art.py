"""Canonical character portrait files (pixel art, refs) shipped with the bot."""

from __future__ import annotations

from pathlib import Path

from config import BASE_DIR

ART_DIR = BASE_DIR / "assets" / "characters"

# Wolf name (case-insensitive) → filename under assets/characters/
CHARACTER_ART_FILES: dict[str, str] = {
    "Mirewort": "mirewort_small_pixels.png",
}


def canonical_art_path(wolf_name: str) -> Path | None:
    """Return the on-disk portrait for a canonical character, if present."""
    if not wolf_name:
        return None
    for key, filename in CHARACTER_ART_FILES.items():
        if key.lower() == wolf_name.strip().lower():
            path = ART_DIR / filename
            if path.is_file():
                return path
    return None
