"""Pilot: a handful of RP_LOCATIONS with real mechanical effects, not just
flavor text. Keyed by the exact strings in config.RP_LOCATIONS, matched
case-insensitively against a wolf's free-text ic_location (see cogs/rp.py;
ic_location isn't validated against RP_LOCATIONS, so unmatched text is
simply inert here).

Deliberately small: four locations, four different existing modifier shapes
(flat bonus, rollover exemption, disease multiplier, DC modifier) reusing
patterns already established elsewhere (engine.humidity, engine.pack_traits,
season_effects). Extend this dict rather than inventing new mechanisms.
"""

from __future__ import annotations

_SCAVENGE_BONUS_PCT = {
    "the ice caves": 15,  # cold naturally preserves a carrion cache
}

_WINTER_HUNGER_EXEMPT = {
    "the volcanic vents",  # warm ground; the season's cold-bite hunger decay doesn't apply
}

_DISEASE_MULT = {
    "the sog grave": 1.4,
    "the rotting mere": 1.4,
}

_SCENT_DC_MOD = {
    "the open moors": 2,  # wide, exposed; nothing to break scent or sightline
    "sunningrocks": 2,
}


def _normalize(location: str | None) -> str:
    return (location or "").strip().lower()


def location_scavenge_bonus_pct(location: str | None) -> int:
    return _SCAVENGE_BONUS_PCT.get(_normalize(location), 0)


def location_winter_hunger_exempt(location: str | None) -> bool:
    return _normalize(location) in _WINTER_HUNGER_EXEMPT


def location_disease_mult(location: str | None) -> float:
    return _DISEASE_MULT.get(_normalize(location), 1.0)


def location_scent_dc_mod(location: str | None) -> tuple[int, str]:
    mod = _SCENT_DC_MOD.get(_normalize(location), 0)
    if not mod:
        return 0, ""
    return mod, f"exposed open ground ({mod:+d} dc)"
