"""Season modifiers for hunts and foraging."""

from __future__ import annotations

from config import SEASON_FORAGE_DC_MOD, SEASON_HUNT_MODIFIERS, WINTER_FORAGE_SPOIL_CHANCE
from engine.lexicon import season_display

# Tracking / small-prey hunt DC by season (matches season_activity_blurb)
SEASON_TRACK_DC_MOD = {
    "spring": 0,
    "summer": -2,
    "autumn": -1,
    "winter": 2,
}


def apply_season_hunt(amount: int, season: str) -> int:
    if amount <= 0:
        return 0
    modifier = SEASON_HUNT_MODIFIERS.get(season, 0)
    if modifier == 0:
        return amount
    return max(0, int(amount * (100 + modifier) / 100))


def season_forage_dc_mod(season: str) -> int:
    return SEASON_FORAGE_DC_MOD.get(season, 0)


def season_track_dc_mod(season: str) -> int:
    return SEASON_TRACK_DC_MOD.get(season, 0)


def season_track_dc_label(season: str) -> str | None:
    mod = season_track_dc_mod(season)
    if mod == 0:
        return None
    name = season_display(season)
    if mod > 0:
        return f"+{mod} track dc ({name})"
    return f"{mod} track dc ({name})"


def season_hunt_modifier_label(season: str) -> str:
    mod = SEASON_HUNT_MODIFIERS.get(season, 0)
    if mod == 0:
        return "no hunt payout change"
    name = season_display(season)
    return f"{mod:+d}% hunt bones ({name})"


def season_forage_modifier_label(season: str) -> str:
    mod = SEASON_FORAGE_DC_MOD.get(season, 0)
    if mod == 0:
        return "normal forage dc"
    name = season_display(season)
    if mod > 0:
        return f"+{mod} forage dc ({name}; scarcer plants)"
    return f"{mod} forage dc ({name}; easier pickings)"


def season_activity_blurb(season: str) -> str:
    hunt = season_hunt_modifier_label(season)
    forage = season_forage_modifier_label(season)
    extras = {
        "spring": (
            "River crossings **+2 DC** (melt floods). Herbs plentiful (**−2** forage DC)."
        ),
        "summer": (
            "Heat waves possible (`/world action:hazard hazard:extreme_heat`). Small prey hunting **−2 DC**. "
            "Wildfire smoke may appear on travel rolls."
        ),
        "autumn": (
            "Prey fat and slow (**−1** hunt DC). After first frost, forage **+2 DC**. "
            "Successful hunts may cache **+1 day** food."
        ),
        "winter": (
            "Forage **+5 DC** (snow). Hunting **+2 DC**. Blizzards double travel hazard checks. "
            "Wolves need **1.5×** food to avoid exhaustion. "
            f"failed forage may spoil a herb stack (**{int(WINTER_FORAGE_SPOIL_CHANCE * 100)}%**)."
        ),
    }
    extra = extras.get(season, "")
    base = f"**hunts:** {hunt} · **herbs:** {forage}"
    return f"{base}\n{extra}" if extra else base


def winter_forage_fail_spoil_chance(season: str) -> float:
    return WINTER_FORAGE_SPOIL_CHANCE if season == "winter" else 0.0


def maybe_spoil_herb_on_forage_fail(user, *, season: str) -> str:
    """On failed winter forage, chance to destroy a random herb stack."""
    import random

    import database as db

    chance = winter_forage_fail_spoil_chance(season)
    if chance <= 0 or random.random() >= chance:
        return ""
    stacks = db.get_herb_stacks(user["id"])
    if not stacks:
        return "\n_snow ruined what little you had gathered._"
    stack = random.choice(stacks)
    db.remove_herb_stack(stack["id"])
    from herbs import HERBS

    name = HERBS.get(stack["herb_key"], {}).get("name", stack["herb_key"])
    return f"\n_winter spoil; **{name}** froze in your bag._"
