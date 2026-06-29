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
    "you and **{partner}** tumble through the grass; breathless, laughing, the den feels whole.",
    "a rough-and-tumble that ends in shared tongues and dozing shoulder to shoulder.",
    "**{partner}** matches your energy stroke for stroke; even the elders glance over, pleased.",
)

GOOD_FLAVOR = (
    "you and **{partner}** wrestle and groom; easy, familiar warmth.",
    "nose to nose, then a playful snap at the ear. the pack scent-line feels stronger.",
    "You share a kill-story and a lazy roll in the pine needles.",
)

AWKWARD_FLAVOR = (
    "you misread **{partner}**'s mood; a snap, a flinch, and both of you slink away.",
    "**{partner}** turns cold mid-groom. the silence after hurts more than the nip.",
    "Your play gets too rough. **{partner}** leaves with flattened ears; the den feels smaller.",
    "A wrestling tumble sends you both rolling through old scat; the stink clings.",
)

SCRAP_FLAVOR = (
    "words become teeth; you and **{partner}** brawl until fur flies and blood salts the dust.",
    "an old grudge surfaces. you and **{partner}** snarl until someone has to pull you apart.",
    "**{partner}** won't yield space. The fight leaves both of you limping and the den on edge.",
)


def _pick(pool: tuple[str, ...], partner: str) -> str:
    return random.choice(pool).format(partner=partner)


def roll_socialize_outcome() -> str:
    """return warm, good, awkward, or scrap."""
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


def run_socialize(user, partner, *, pack_id: int, day: int = 0, cross_pack: bool = False) -> dict:
    """
    apply socialize effects. caller must set last_socialize_day first or after.
    cross_pack=True (secret/cross-den meetings) skips den unity changes; the
    rest of the den doesn't know it happened.
    returns dict: outcome, body, success (embed color hint), expulsion_note.
    """
    from config import STRANGER_SCENT_ABSENCE_DAYS, STRANGER_SCENT_MOOD_PENALTY

    name = partner["wolf_name"]
    lines: list[str] = []
    last_active = db.last_active_day(user)
    if day > 0 and last_active == 0:
        # brand new to the den; the pack hasn't had a chance to know them yet,
        # same wary-before-warming-up beat as a long-absent wolf gets.
        new_mood = db.adjust_mood(user["id"], -STRANGER_SCENT_MOOD_PENALTY)
        lines.append(
            f"_you're new enough to the den that **{name}** scents you like a stranger at first; "
            f"the pack is wary before warming up to someone they don't know yet. "
            f"**{STRANGER_SCENT_MOOD_PENALTY} mood** (now **{new_mood}**)._"
        )
    elif day > 0 and last_active > 0 and day - last_active >= STRANGER_SCENT_ABSENCE_DAYS:
        new_mood = db.adjust_mood(user["id"], -STRANGER_SCENT_MOOD_PENALTY)
        lines.append(
            f"_you've been gone long enough that **{name}** scents you like a stranger at first; "
            f"the den is wary before warming back up. **{STRANGER_SCENT_MOOD_PENALTY} mood** (now **{new_mood}**)._"
        )

    outcome = roll_socialize_outcome()
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
        standing_note = f"standing **+{SOCIALIZE_STANDING_GOOD}**."
        expulsion = _expulsion_from_standing(kick, pack_id)
        if pack_id and not cross_pack:
            db.adjust_pack_unity(pack_id, SOCIALIZE_UNITY_WARM)
            unity_note = f"den unity **+{SOCIALIZE_UNITY_WARM}**."

    elif outcome == "good":
        lines.append(_pick(GOOD_FLAVOR, name))
        mood = SOCIALIZE_MOOD_GOOD
        your_mood = db.adjust_mood(user["id"], mood)
        their_mood = db.adjust_mood(partner["id"], mood)
        lines.append(f"**+{mood} mood** each (you: **{your_mood}**, them: **{their_mood}**).")
        kick = db.adjust_wolf_standing(user["discord_id"], SOCIALIZE_STANDING_GOOD)
        standing_note = f"standing **+{SOCIALIZE_STANDING_GOOD}**."
        expulsion = _expulsion_from_standing(kick, pack_id)

    elif outcome == "awkward":
        lines.append(_pick(AWKWARD_FLAVOR, name))
        mood = SOCIALIZE_MOOD_AWKWARD
        your_mood = db.adjust_mood(user["id"], mood)
        their_mood = db.adjust_mood(partner["id"], mood)
        db.update_user(user["discord_id"], wolf_id=user["id"], distressed=1)
        lines.append(f"**{mood} mood** each (you: **{your_mood}**, them: **{their_mood}**).")
        if pack_id and not cross_pack:
            db.adjust_pack_unity(pack_id, SOCIALIZE_UNITY_AWKWARD)
            unity_note = f"den unity **{SOCIALIZE_UNITY_AWKWARD}**."
        from engine.disease_contract import try_den_filth_exposure

        for wolf, label in ((user, "You"), (partner, partner["wolf_name"])):
            filth = try_den_filth_exposure(wolf, day=day)
            if filth:
                verb = "tumble" if label == "You" else "tumbles"
                lines.append(f"{label} {verb} through old scat; {filth}")

    else:  # scrap
        lines.append(_pick(SCRAP_FLAVOR, name))
        mood = SOCIALIZE_MOOD_SCRAP
        your_mood = db.adjust_mood(user["id"], mood)
        their_mood = db.adjust_mood(partner["id"], mood)
        db.update_user(user["discord_id"], wolf_id=user["id"], distressed=1)
        db.update_user(partner["discord_id"], wolf_id=partner["id"], distressed=1)
        lines.append(f"**{mood} mood** each (you: **{your_mood}**, them: **{their_mood}**).")
        kick = db.adjust_wolf_standing(user["discord_id"], SOCIALIZE_STANDING_SCRAP)
        standing_note = f"standing **{SOCIALIZE_STANDING_SCRAP}**."
        expulsion = _expulsion_from_standing(kick, pack_id)
        if pack_id and not cross_pack:
            db.adjust_pack_unity(pack_id, SOCIALIZE_UNITY_SCRAP)
            unity_note = f"den unity **{SOCIALIZE_UNITY_SCRAP}**."
        from engine.disease_contract import try_den_filth_exposure

        for wolf, label in ((user, "You"), (partner, partner["wolf_name"])):
            filth = try_den_filth_exposure(wolf, day=day)
            if filth:
                verb = "tumble" if label == "You" else "tumbles"
                lines.append(f"{label} {verb} through old scat; {filth}")

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
