"""
Humidity: derived from a Great Pack's terrain plus the day's weather, with
real effects on disease spread (rot thrives in wet air) and scent tracking
(humid air carries scent farther; arid air dries it fast). Not flavour-only.
"""

from __future__ import annotations

PACK_BASE_HUMIDITY = {
    "greyspire": "arid",  # mountain peaks; thin, dry air
    "silverrush": "humid",  # river banks
    "mistmoor": "humid",  # swamp; the Maw's belly never really dries out
    "thistlehide": "moderate",  # forest
}

HUMID_WEATHER = frozenset({"rain", "storm", "thunderstorm", "fog", "sleet"})
ARID_WEATHER = frozenset({"heatwave", "sunny", "wind"})

_LEVELS = ("arid", "moderate", "humid")

HUMIDITY_LABELS = {
    "arid": "arid",
    "moderate": "moderate humidity",
    "humid": "humid",
}


def humidity_level(great_pack: str | None, weather: str | None) -> str:
    base = PACK_BASE_HUMIDITY.get(great_pack, "moderate")
    idx = _LEVELS.index(base)
    if weather in HUMID_WEATHER:
        idx = min(2, idx + 1)
    elif weather in ARID_WEATHER:
        idx = max(0, idx - 1)
    return _LEVELS[idx]


def humidity_label(great_pack: str | None, weather: str | None) -> str:
    return HUMIDITY_LABELS[humidity_level(great_pack, weather)]


def humidity_disease_spread_mult(great_pack: str | None, weather: str | None) -> float:
    level = humidity_level(great_pack, weather)
    if level == "humid":
        return 1.25
    if level == "arid":
        return 0.8
    return 1.0


def humidity_scent_dc_modifier(great_pack: str | None, weather: str | None) -> int:
    """Humid air carries scent farther (easier tracking/sniffing); arid air dries it fast (harder)."""
    level = humidity_level(great_pack, weather)
    if level == "humid":
        return -1
    if level == "arid":
        return 1
    return 0
