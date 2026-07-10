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
    SOCIALIZE_UNITY_GOOD,
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

RIVAL_WARM_FLAVOR = (
    "something shifts; a rare unguarded moment with **{partner}**; neither of you will mention it.",
    "you and **{partner}** run the same trail at the same pace, for once. the silence isn't hostile.",
)
RIVAL_GOOD_FLAVOR = (
    "not warmth, exactly; but **{partner}** and you circle each other without teeth today.",
    "a truce in everything but name. you and **{partner}** share the ridge without incident.",
    "**{partner}** acknowledges you. you acknowledge them. the needle doesn't move; but it doesn't bite, either.",
)
RIVAL_AWKWARD_FLAVOR = (
    "old friction surfaces. you and **{partner}** manage not to draw blood, barely.",
    "the air between you and **{partner}** hasn't thawed. someone steps wrong; the other tenses.",
    "you and **{partner}** spend more energy not-fighting than anything else.",
)
RIVAL_SCRAP_FLAVOR = (
    "the grudge had to go somewhere. you and **{partner}** make sure it does.",
    "it was always going to end this way with **{partner}**. fur flies.",
    "you and **{partner}** settle nothing, except that it still isn't settled.",
)

KIN_WARM_FLAVOR = (
    "family; even the rough parts feel right. you and **{partner}** carry the same scent-line home.",
    "it's the kind of warmth that doesn't need naming. blood and all that.",
)
KIN_AWKWARD_FLAVOR = (
    "family is never simple. you and **{partner}** dance around something neither of you says.",
    "kin or not, **{partner}** hits a nerve. you part without closing it.",
)

MENTOR_WARM_FLAVOR = (
    "the old lesson is still in your bones. running beside **{partner}** feels like proof.",
    "some things stick. you and **{partner}** fall back into the rhythm without trying.",
)
MENTOR_AWKWARD_FLAVOR = (
    "the dynamic doesn't disappear just because the training is done. you and **{partner}** navigate the gap.",
    "mentors and mentees grow apart sometimes. today, you felt the distance.",
)


def _pick(pool: tuple[str, ...], partner: str) -> str:
    return random.choice(pool).format(partner=partner)


def _bond_flavor_pools(bond_type: str | None, bond_strength: int) -> dict[str, tuple]:
    if not bond_type or bond_strength < 30:
        return {}
    if bond_type == "rivalry":
        return {
            "warm": RIVAL_WARM_FLAVOR, "good": RIVAL_GOOD_FLAVOR,
            "awkward": RIVAL_AWKWARD_FLAVOR, "scrap": RIVAL_SCRAP_FLAVOR,
        }
    if bond_type == "kin":
        return {"warm": KIN_WARM_FLAVOR, "awkward": KIN_AWKWARD_FLAVOR}
    if bond_type == "mentor":
        return {"warm": MENTOR_WARM_FLAVOR, "awkward": MENTOR_AWKWARD_FLAVOR}
    return {}


def roll_socialize_outcome(bond_type: str | None = None, bond_strength: int = 0) -> str:
    """
    Weighted outcome roll; existing bonds shift the probability curve.
    Rivals are more likely to scrap; friends more likely to have warm moments;
    kin rarely truly brawl; mentor relationships default toward good.
    """
    s = max(0, min(100, bond_strength))
    if bond_type == "rivalry" and s >= 40:
        weight = min(1.0, s / 100)
        warm   = max(0.02, 0.12 - 0.10 * weight)
        good   = max(0.20, 0.46 - 0.26 * weight)
        awkward = 0.28 + 0.08 * weight
        # scrap = remainder
    elif bond_type in ("friendship", "romance") and s >= 40:
        weight = min(1.0, s / 100)
        warm   = min(0.35, 0.12 + 0.23 * weight)
        good   = min(0.55, 0.46 + 0.09 * weight)
        awkward = max(0.08, 0.24 - 0.16 * weight)
        # scrap = remainder
    elif bond_type == "kin":
        warm, good, awkward = 0.25, 0.50, 0.20
    elif bond_type == "mentor":
        warm, good, awkward = 0.20, 0.55, 0.22
    else:
        warm, good, awkward = 0.12, 0.46, 0.24

    roll = random.random()
    if roll < warm:
        return "warm"
    if roll < warm + good:
        return "good"
    if roll < warm + good + awkward:
        return "awkward"
    return "scrap"


def _expulsion_from_standing(kick: str, pack_id: int | None) -> str:
    from engine.broken_canine import standing_expulsion_note

    note = standing_expulsion_note(kick, pack_id)
    return f"\n\n{note}" if note else ""


def run_socialize(user, partner, *, pack_id: int, day: int = 0, cross_pack: bool = False, season: str | None = None) -> dict:
    """
    apply socialize effects. caller must set last_socialize_day first or after.
    cross_pack=True (secret/cross-den meetings) skips den unity changes; the
    rest of the den doesn't know it happened.
    returns dict: outcome, body, success (embed color hint), expulsion_note.
    """
    from config import STRANGER_SCENT_ABSENCE_DAYS, STRANGER_SCENT_MOOD_PENALTY

    name = partner["wolf_name"]
    lines: list[str] = []

    # Stranger-scent penalty is now pair-specific: only fires if THIS partner
    # hasn't seen the user in a long time, not just if the user was globally absent.
    # Old friends reuniting after absence should feel warm, not penalised.
    pair_bond = db.get_bond(user["id"], partner["id"], "friendship") or \
                db.get_bond(user["id"], partner["id"], "kin") or \
                db.get_bond(user["id"], partner["id"], "romance")
    pair_last_seen = int(pair_bond["updated_day"]) if pair_bond else 0
    pair_is_stranger = (day > 0) and (pair_last_seen == 0 or (day - pair_last_seen >= STRANGER_SCENT_ABSENCE_DAYS))
    last_active = db.last_active_day(user)

    if day > 0 and last_active == 0 and pair_is_stranger:
        new_mood = db.adjust_mood(user["id"], -STRANGER_SCENT_MOOD_PENALTY)
        lines.append(
            f"_you're new enough to the den that **{name}** scents you like a stranger at first; "
            f"the pack is wary before warming up to someone they don't know yet. "
            f"**{STRANGER_SCENT_MOOD_PENALTY} mood** (now **{new_mood}**)._"
        )
    elif day > 0 and last_active > 0 and day - last_active >= STRANGER_SCENT_ABSENCE_DAYS and pair_is_stranger:
        new_mood = db.adjust_mood(user["id"], -STRANGER_SCENT_MOOD_PENALTY)
        lines.append(
            f"_you've been gone long enough that **{name}** scents you like a stranger at first; "
            f"the den is wary before warming back up. **{STRANGER_SCENT_MOOD_PENALTY} mood** (now **{new_mood}**)._"
        )

    from engine.bonds import _pair_bond_kind
    existing_bond_type, _ = _pair_bond_kind(user, partner)
    bond_row = db.get_bond(user["id"], partner["id"], existing_bond_type) if existing_bond_type else None
    bond_strength = int(bond_row["strength"]) if bond_row else 0
    outcome = roll_socialize_outcome(existing_bond_type, bond_strength)
    # Grief suppresses warmth; a wolf still raw from mate-loss can't fully open up.
    grief = int(user["grief_sunrises"]) if "grief_sunrises" in user.keys() else 0
    if grief > 0 and outcome == "warm":
        outcome = "good"
    bond_pools = _bond_flavor_pools(existing_bond_type, bond_strength)

    unity_note = ""
    standing_note = ""
    expulsion = ""

    if outcome == "warm":
        lines.append(_pick(bond_pools.get("warm", WARM_FLAVOR), name))
        mood = SOCIALIZE_MOOD_WARM
        your_mood = db.adjust_mood(user["id"], mood)
        their_mood = db.adjust_mood(partner["id"], mood)
        lines.append(f"**+{mood} mood** each (you: **{your_mood}**, them: **{their_mood}**).")
        kick = db.adjust_wolf_standing_by_id(user["id"], SOCIALIZE_STANDING_GOOD)
        standing_note = f"standing **+{SOCIALIZE_STANDING_GOOD}**."
        expulsion = _expulsion_from_standing(kick, pack_id)
        if pack_id and not cross_pack:
            db.adjust_pack_unity(pack_id, SOCIALIZE_UNITY_WARM)
            unity_note = f"den unity **+{SOCIALIZE_UNITY_WARM}**."

    elif outcome == "good":
        lines.append(_pick(bond_pools.get("good", GOOD_FLAVOR), name))
        mood = SOCIALIZE_MOOD_GOOD
        your_mood = db.adjust_mood(user["id"], mood)
        their_mood = db.adjust_mood(partner["id"], mood)
        lines.append(f"**+{mood} mood** each (you: **{your_mood}**, them: **{their_mood}**).")
        kick = db.adjust_wolf_standing_by_id(user["id"], SOCIALIZE_STANDING_GOOD)
        standing_note = f"standing **+{SOCIALIZE_STANDING_GOOD}**."
        expulsion = _expulsion_from_standing(kick, pack_id)
        if pack_id and not cross_pack:
            db.adjust_pack_unity(pack_id, SOCIALIZE_UNITY_GOOD)
            unity_note = f"den unity **+{SOCIALIZE_UNITY_GOOD}**."

    elif outcome == "awkward":
        lines.append(_pick(bond_pools.get("awkward", AWKWARD_FLAVOR), name))
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
        lines.append(_pick(bond_pools.get("scrap", SCRAP_FLAVOR), name))
        mood = SOCIALIZE_MOOD_SCRAP
        your_mood = db.adjust_mood(user["id"], mood)
        their_mood = db.adjust_mood(partner["id"], mood)
        db.update_user(user["discord_id"], wolf_id=user["id"], distressed=1)
        db.update_user(partner["discord_id"], wolf_id=partner["id"], distressed=1)
        lines.append(f"**{mood} mood** each (you: **{your_mood}**, them: **{their_mood}**).")
        kick = db.adjust_wolf_standing_by_id(user["id"], SOCIALIZE_STANDING_SCRAP)
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

    spread_you = try_spread_from_close_contact(user, partner, season=season)
    spread_them = try_spread_from_close_contact(partner, user, season=season)
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
