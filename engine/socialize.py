"""Pack socialize; mood, standing, and unity with good and bad outcomes."""

from __future__ import annotations

import random

import database as db
from config import (
    SOCIALIZE_MOOD_AWKWARD,
    SOCIALIZE_MOOD_GOOD,
    SOCIALIZE_MOOD_SCRAP,
    SOCIALIZE_MOOD_WARM,
    SOCIALIZE_STANDING_GOOD,
    SOCIALIZE_STANDING_SCRAP,
    SOCIALIZE_UNITY_AWKWARD,
    SOCIALIZE_UNITY_SCRAP,
    SOCIALIZE_UNITY_WARM,
)

WARM_FLAVOR = (
    "You and **{partner}** tumble through the grass; breathless, laughing, the den feels whole.",
    "A rough-and-tumble that ends in shared tongues and dozing shoulder to shoulder.",
    "**{partner}** matches your energy stroke for stroke; even the elders glance over, pleased.",
)

GOOD_FLAVOR = (
    "You and **{partner}** wrestle and groom; easy, familiar warmth.",
    "Nose to nose, then a playful snap at the ear. The pack scent-line feels stronger.",
    "You share a kill-story and a lazy roll in the pine needles.",
)

AWKWARD_FLAVOR = (
    "You misread **{partner}**'s mood; a snap, a flinch, and both of you slink away.",
    "**{partner}** turns cold mid-groom. The silence after hurts more than the nip.",
    "Your play gets too rough. **{partner}** leaves with flattened ears; the den feels smaller.",
    "A wrestling tumble sends you both rolling through old scat; the stink clings.",
)

SCRAP_FLAVOR = (
    "Words become teeth; you and **{partner}** brawl until fur flies and blood salts the dust.",
    "An old grudge surfaces. You and **{partner}** snarl until someone has to pull you apart.",
    "**{partner}** won't yield space. The fight leaves both of you limping and the den on edge.",
)


def _pick(pool: tuple[str, ...], partner: str) -> str:
    return random.choice(pool).format(partner=partner)


def roll_socialize_outcome() -> str:
    """Return warm, good, awkward, or scrap."""
    roll = random.random()
    if roll < 0.12:
        return "warm"
    if roll < 0.58:
        return "good"
    if roll < 0.82:
        return "awkward"
    return "scrap"


def _expulsion_from_standing(kick: str, pack_id: int | None) -> str:
    from engine.broken_canine import standing_expulsion_note

    note = standing_expulsion_note(kick, pack_id)
    return f"\n\n{note}" if note else ""


def run_socialize(user, partner, *, pack_id: int, day: int = 0) -> dict:
    """
    Apply socialize effects. Caller must set last_socialize_day first or after.
    Returns dict: outcome, body, success (embed color hint), expulsion_note.
    """
    outcome = roll_socialize_outcome()
    name = partner["wolf_name"]
    lines: list[str] = []
    unity_note = ""
    standing_note = ""
    expulsion = ""

    if outcome == "warm":
        lines.append(_pick(WARM_FLAVOR, name))
        mood = SOCIALIZE_MOOD_WARM
        your_mood = db.adjust_mood(user["id"], mood)
        their_mood = db.adjust_mood(partner["id"], mood)
        lines.append(f"**+{mood} mood** each (you: **{your_mood}**, them: **{their_mood}**).")
        kick = db.adjust_wolf_standing(user["discord_id"], SOCIALIZE_STANDING_GOOD)
        standing_note = f"Standing **+{SOCIALIZE_STANDING_GOOD}**."
        expulsion = _expulsion_from_standing(kick, pack_id)
        if pack_id:
            db.adjust_pack_unity(pack_id, SOCIALIZE_UNITY_WARM)
            unity_note = f"Den unity **+{SOCIALIZE_UNITY_WARM}**."

    elif outcome == "good":
        lines.append(_pick(GOOD_FLAVOR, name))
        mood = SOCIALIZE_MOOD_GOOD
        your_mood = db.adjust_mood(user["id"], mood)
        their_mood = db.adjust_mood(partner["id"], mood)
        lines.append(f"**+{mood} mood** each (you: **{your_mood}**, them: **{their_mood}**).")
        kick = db.adjust_wolf_standing(user["discord_id"], SOCIALIZE_STANDING_GOOD)
        standing_note = f"Standing **+{SOCIALIZE_STANDING_GOOD}**."
        expulsion = _expulsion_from_standing(kick, pack_id)

    elif outcome == "awkward":
        lines.append(_pick(AWKWARD_FLAVOR, name))
        mood = SOCIALIZE_MOOD_AWKWARD
        your_mood = db.adjust_mood(user["id"], mood)
        their_mood = db.adjust_mood(partner["id"], mood)
        db.update_user(user["discord_id"], wolf_id=user["id"], distressed=1)
        lines.append(f"**{mood} mood** each (you: **{your_mood}**, them: **{their_mood}**).")
        if pack_id:
            db.adjust_pack_unity(pack_id, SOCIALIZE_UNITY_AWKWARD)
            unity_note = f"Den unity **{SOCIALIZE_UNITY_AWKWARD}**."
        from engine.disease_contract import try_den_filth_exposure

        filth = try_den_filth_exposure(user)
        if filth:
            lines.append(filth)

    else:  # scrap
        lines.append(_pick(SCRAP_FLAVOR, name))
        mood = SOCIALIZE_MOOD_SCRAP
        your_mood = db.adjust_mood(user["id"], mood)
        their_mood = db.adjust_mood(partner["id"], mood)
        db.update_user(user["discord_id"], wolf_id=user["id"], distressed=1)
        db.update_user(partner["discord_id"], wolf_id=partner["id"], distressed=1)
        lines.append(f"**{mood} mood** each (you: **{your_mood}**, them: **{their_mood}**).")
        kick = db.adjust_wolf_standing(user["discord_id"], SOCIALIZE_STANDING_SCRAP)
        standing_note = f"Standing **{SOCIALIZE_STANDING_SCRAP}**."
        expulsion = _expulsion_from_standing(kick, pack_id)
        if pack_id:
            db.adjust_pack_unity(pack_id, SOCIALIZE_UNITY_SCRAP)
            unity_note = f"Den unity **{SOCIALIZE_UNITY_SCRAP}**."

    from engine.disease_contract import try_spread_from_close_contact

    spread_you = try_spread_from_close_contact(user, partner)
    spread_them = try_spread_from_close_contact(partner, user)
    if spread_you:
        lines.append(spread_you)
    if spread_them:
        lines.append(spread_them)

    if standing_note:
        lines.append(standing_note)
    if unity_note:
        lines.append(unity_note)

    from engine.bonds import apply_socialize_bonds

    bond_note = apply_socialize_bonds(user, partner, outcome, day=day)
    if bond_note:
        lines.append(bond_note)

    return {
        "outcome": outcome,
        "body": "\n".join(lines) + expulsion,
        "success": outcome in ("warm", "good"),
        "expulsion_note": expulsion,
    }
