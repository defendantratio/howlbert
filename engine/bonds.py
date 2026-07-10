"""Wolf bonds; friendships, rivalries, kin, mentors, and found families."""

from __future__ import annotations

import random

import database as db
from config import (
    BOND_DECAY_IDLE_DAYS,
    JEALOUSY_MOOD_PENALTY,
    JEALOUSY_RIVALRY_GAIN,
    KIN_REUNION_BOND_GAIN,
    KIN_REUNION_MOOD_BONUS,
    MENTOR_MATE_CATCH_CHANCE,
    MENTOR_MATE_CAUGHT_STANDING,
    MENTOR_MATE_CAUGHT_TEXT,
)

BOND_TYPES = frozenset({"friendship", "rivalry", "kin", "mentor", "romance", "fling"})

BOND_LABELS = {
    "friendship": "friendship",
    "rivalry": "rivalry",
    "kin": "kin",
    "mentor": "mentor",
    "romance": "romance",
    "fling": "fling",
}

FAMILY_ROLES = frozenset({"founder", "parent", "sibling", "cub", "member"})

FAMILY_ROLE_LABELS = {
    "founder": "founder",
    "parent": "parent",
    "sibling": "sibling",
    "cub": "cub",
    "member": "member",
}


POSITIVE_BOND_TYPES = ("friendship", "romance", "kin", "mentor")
STRONG_BOND_THRESHOLD = 60


def has_romance_bond(wolf_a_id: int, wolf_b_id: int) -> bool:
    """True if these two wolves have an active romance bond (strength > 0)."""
    if not wolf_a_id or not wolf_b_id:
        return False
    bond = db.get_bond(wolf_a_id, wolf_b_id, "romance")
    return bool(bond and int(bond["strength"]) > 0)


def has_strong_positive_bond(wolf_a_id: int, wolf_b_id: int) -> bool:
    """
    True if these two wolves share a deep enough friendship/romance/kin/mentor
    bond that it should matter beyond the bond list; personal trust
    outweighing pack politics, not just a number on a sheet.
    """
    if not wolf_a_id or not wolf_b_id:
        return False
    for bond_type in POSITIVE_BOND_TYPES:
        bond = db.get_bond(wolf_a_id, wolf_b_id, bond_type)
        if bond and int(bond["strength"]) >= STRONG_BOND_THRESHOLD:
            return True
    return False


def is_mentor_bond(wolf_a_id: int, wolf_b_id: int) -> bool:
    if not wolf_a_id or not wolf_b_id:
        return False
    return db.get_bond(wolf_a_id, wolf_b_id, "mentor") is not None


MENTOR_MATE_NOTICED_TEXT = (
    "a shape slips away from the clearing before you see who; someone saw something.",
    "you catch a rustle in the brush as you part ways. probably nothing. probably.",
    "a pair of eyes that weren't there a moment ago. gone before you can place them.",
)


def _is_former_mentor_pair(wolf_a_id: int, wolf_b_id: int) -> bool:
    """True if the pair graduated from a mentorship (friendship bond note = 'former mentor')."""
    bond = db.get_bond(wolf_a_id, wolf_b_id, "friendship")
    return bool(bond and str(bond["note"] or "").strip().lower() == "former mentor")


def apply_mentor_mate_caught(user, target, *, guild_id: int | None, day: int) -> str | None:
    """
    Mentor/mentee courtship and mating aren't blocked outright; the den isn't
    that squeamish; but it's an abuse of trust and standing, not power, is
    the in-fiction currency here. If caught, the standing hit and public
    scandal don't land immediately; it queues as a rumor (engine.rumor_mill)
    that breaks at the den a couple sunrises later, same as real gossip.
    Former mentor-mentee pairs (after graduation) carry the same taboo at
    reduced catch chance; the history still casts a shadow.
    Returns an immediate "someone may have seen" notice if caught, else None.
    """
    current_mentor = is_mentor_bond(user["id"], target["id"])
    former_mentor = not current_mentor and _is_former_mentor_pair(user["id"], target["id"])
    if not current_mentor and not former_mentor:
        return None
    catch_chance = MENTOR_MATE_CATCH_CHANCE if current_mentor else MENTOR_MATE_CATCH_CHANCE * 0.6
    if random.random() >= catch_chance:
        return None
    if random.random() >= MENTOR_MATE_CATCH_CHANCE:
        return None
    if guild_id is not None:
        from engine.rumor_mill import queue_rumor

        flavor = random.choice(MENTOR_MATE_CAUGHT_TEXT)
        queue_rumor(
            guild_id=guild_id,
            wolf_a_id=user["id"],
            wolf_b_id=target["id"],
            kind="mentor_mate",
            standing_delta=MENTOR_MATE_CAUGHT_STANDING,
            flavor_text=f"{flavor}\n**{user['wolf_name']}** and **{target['wolf_name']}**; standing **{MENTOR_MATE_CAUGHT_STANDING}** for both, the truth catching up with them.",
            queued_day=day,
        )
        return random.choice(MENTOR_MATE_NOTICED_TEXT)
    db.adjust_wolf_standing_by_id(user["id"], MENTOR_MATE_CAUGHT_STANDING)
    db.adjust_wolf_standing_by_id(target["id"], MENTOR_MATE_CAUGHT_STANDING)
    flavor = random.choice(MENTOR_MATE_CAUGHT_TEXT)
    return f"{flavor}\nstanding **{MENTOR_MATE_CAUGHT_STANDING}** for both of you."


def strength_tier(strength: int, *, rivalry: bool = False, romance: bool = False) -> str:
    s = max(0, min(100, int(strength)))
    if rivalry:
        if s >= 80:
            return "bitter enemies"
        if s >= 60:
            return "heated feud"
        if s >= 40:
            return "grudge"
        if s >= 20:
            return "tension"
        return "mild friction"
    if romance:
        if s >= 80:
            return "devoted"
        if s >= 60:
            return "smitten"
        if s >= 40:
            return "courting"
        if s >= 20:
            return "drawn together"
        return "a spark"
    if s >= 80:
        return "unshakable"
    if s >= 60:
        return "close"
    if s >= 40:
        return "steady"
    if s >= 20:
        return "growing"
    return "faint"


def strength_bar(strength: int) -> str:
    s = max(0, min(100, int(strength)))
    filled = round(s / 10)
    return "●" * filled + "○" * (10 - filled)


def _format_bond_note(partner_name: str, bond_type: str, row, *, label: str | None = None) -> str:
    display = label or BOND_LABELS.get(bond_type, bond_type.title()).lower()
    rival = bond_type == "rivalry"
    romantic = bond_type in ("romance", "fling")
    return (
        f"bond; **{partner_name}**: {display} **{strength_bar(row['strength'])}** "
        f"({strength_tier(row['strength'], rivalry=rival, romance=romantic)})"
    )


def _pair_bond_kind(user, partner) -> tuple[str, str | None]:
    """Bond type and display label for socialize/groom adjustments."""
    from engine.attraction import are_bonded_mates

    if are_bonded_mates(user, partner):
        return "romance", "mate"

    best = None
    for bond_type in ("kin", "mentor", "romance", "fling", "friendship", "rivalry"):
        row = db.get_bond(user["id"], partner["id"], bond_type)
        if not row:
            continue
        if best is None or int(row["strength"]) > int(best["strength"]):
            best = row
    if best:
        bt = best["bond_type"]
        return bt, BOND_LABELS.get(bt, bt.title()).lower()
    return "friendship", None


def _jealousy_note(jealous_wolf, flirt_wolf, partner_name: str, *, day: int) -> str | None:
    """A bonded mate isn't present for the interaction, but their jealousy is real
    even so: a small mood hit plus a faint rivalry seed toward the new warmth."""
    mood = db.adjust_mood(jealous_wolf["id"], -JEALOUSY_MOOD_PENALTY)
    db.adjust_bond_strength(jealous_wolf["id"], flirt_wolf["id"], "rivalry", JEALOUSY_RIVALRY_GAIN, day=day)
    return (
        f"_word reaches **{jealous_wolf['wolf_name']}** of how warm things got with "
        f"**{partner_name}**; their mood drops to **{mood}**, and something prickles._"
    )


def _check_jealousy(user, partner, *, day: int) -> list[str]:
    notes: list[str] = []
    user_mate = db.get_bonded_mate(user)
    if user_mate and user_mate["id"] != partner["id"]:
        note = _jealousy_note(user_mate, partner, user["wolf_name"], day=day)
        if note:
            notes.append(note)
    partner_mate = db.get_bonded_mate(partner)
    if partner_mate and partner_mate["id"] != user["id"]:
        note = _jealousy_note(partner_mate, user, partner["wolf_name"], day=day)
        if note:
            notes.append(note)
    return notes


def _check_kin_reunion(user, partner, bond_type: str, *, day: int) -> str | None:
    """A kin bond that's gone quiet a long while (decayed from neglect, not
    just never grown) gets a real "after all this time" bonus on the next
    warm reconnection, instead of treating long-separated family as strangers."""
    if bond_type != "kin":
        return None
    existing = db.get_bond(user["id"], partner["id"], "kin")
    if not existing or day - int(existing["updated_day"]) < BOND_DECAY_IDLE_DAYS:
        return None
    db.adjust_bond_strength(user["id"], partner["id"], "kin", KIN_REUNION_BOND_GAIN, day=day)
    your_mood = db.adjust_mood(user["id"], KIN_REUNION_MOOD_BONUS)
    their_mood = db.adjust_mood(partner["id"], KIN_REUNION_MOOD_BONUS)
    return (
        f"_it's been a long while since **{user['wolf_name']}** and **{partner['wolf_name']}** "
        f"crossed paths; family, even after all this time. **+{KIN_REUNION_MOOD_BONUS} mood** each "
        f"(you: **{your_mood}**, them: **{their_mood}**)._"
    )


def apply_socialize_bonds(user, partner, outcome: str, *, day: int = 0) -> str | None:
    """adjust bond strength from /socialize; returns optional note line."""
    notes: list[str] = []
    bond_type, label = _pair_bond_kind(user, partner)
    if outcome == "warm":
        reunion_note = _check_kin_reunion(user, partner, bond_type, day=day)
        row = db.adjust_bond_strength(user["id"], partner["id"], bond_type, 10, day=day)
        if row:
            notes.append(_format_bond_note(partner["wolf_name"], bond_type, row, label=label))
        if reunion_note:
            notes.append(reunion_note)
        if bond_type == "friendship":
            notes.extend(_check_jealousy(user, partner, day=day))
        user_grief = int(user["grief_sunrises"]) if "grief_sunrises" in user.keys() else 0
        partner_grief = int(partner["grief_sunrises"]) if "grief_sunrises" in partner.keys() else 0
        if not user_grief:
            db.update_user(user["discord_id"], wolf_id=user["id"], distressed=0)
        if not partner_grief:
            db.update_user(partner["discord_id"], wolf_id=partner["id"], distressed=0)
    elif outcome == "good":
        row = db.adjust_bond_strength(user["id"], partner["id"], bond_type, 5, day=day)
        if row:
            if row["strength"] >= 40:
                notes.append(f"bond with **{partner['wolf_name']}** grows warmer.")
            else:
                notes.append(_format_bond_note(partner["wolf_name"], bond_type, row, label=label))
    elif outcome == "awkward":
        db.adjust_bond_strength(user["id"], partner["id"], "rivalry", 5, day=day)
        if bond_type == "friendship":
            db.adjust_bond_strength(user["id"], partner["id"], "friendship", -3, day=day)
        notes.append(f"tension with **{partner['wolf_name']}**; rivalry stirs.")
    elif outcome == "scrap":
        r = db.adjust_bond_strength(user["id"], partner["id"], "rivalry", 12, day=day)
        if bond_type == "friendship":
            db.adjust_bond_strength(user["id"], partner["id"], "friendship", -8, day=day)
        if r and r["strength"] >= 40:
            notes.append(
                f"**{partner['wolf_name']}**; rivalry **{strength_bar(r['strength'])}** "
                f"({strength_tier(r['strength'], rivalry=True)})"
            )
    return "\n".join(notes) if notes else None


_GRIEF_GROOM_LINES = (
    "_there's a weight in their fur today. you groom carefully, saying nothing._",
    "_they lean into it more than usual. sometimes this is all there is._",
    "_something is missing from their scent; or maybe from yours. you stay close anyway._",
)


def apply_groom_bonds(user, partner, *, day: int = 0) -> str | None:
    bond_type, label = _pair_bond_kind(user, partner)
    row = db.adjust_bond_strength(user["id"], partner["id"], bond_type, 3, day=day)
    if not row:
        return None
    bond_note = _format_bond_note(partner["wolf_name"], bond_type, row, label=label)
    # Grooming removes fleas from the partner; picking out parasites is exactly what this does.
    from engine.diseases import parse_disease
    partner_disease_raw = partner["disease"] if "disease" in partner.keys() else None
    flea_key, _ = parse_disease(partner_disease_raw)
    if flea_key == "fleas":
        db.set_user_conditions(partner["discord_id"], clear_disease=True, wolf_id=partner["id"])
        bond_note = (bond_note + "\n_parasites gone; careful grooming cleared the fleas._") if bond_note else "_careful grooming cleared the fleas._"
    # Mutual: also clear groomer's fleas
    user_disease_raw = user["disease"] if "disease" in user.keys() else None
    user_flea_key, _ = parse_disease(user_disease_raw)
    if user_flea_key == "fleas":
        db.set_user_conditions(user["discord_id"], clear_disease=True, wolf_id=user["id"])
        bond_note = (bond_note + "\n_the grooming works both ways; your own coat is clear too._") if bond_note else "_the grooming works both ways; your own coat is clear too._"
    distressed = int(partner.get("distressed", 0) if hasattr(partner, "get") else partner["distressed"] if "distressed" in partner.keys() else 0)
    partner_grief = int(partner["grief_sunrises"]) if "grief_sunrises" in partner.keys() else 0
    if distressed:
        import random
        grief_line = bond_note + "\n" + random.choice(_GRIEF_GROOM_LINES)
        if not partner_grief:
            db.update_user(partner["discord_id"], wolf_id=partner["id"], distressed=0)
        return grief_line
    return bond_note


def format_bonds_embed_body(user) -> str:
    sections: list[str] = []

    mate = db.get_bonded_mate(user)
    if mate:
        sections.append(f"**bonded mate**; {mate['wolf_name']}")

    lineage = db.format_lineage_for_profile(user)
    if lineage:
        sections.append(lineage)

    family = db.get_wolf_family(user["id"])
    if family:
        members = db.get_family_members(family["id"])
        lines = []
        for m in members[:12]:
            role = FAMILY_ROLE_LABELS.get(m["role"], m["role"].title())
            lines.append(f"**{m['wolf_name']}** ({role})")
        extra = f"\n_+{len(members) - 12} more._" if len(members) > 12 else ""
        sections.append(f"**found family: {family['name']}**\n" + "\n".join(lines) + extra)

    bonds = db.get_bonds_for_wolf(user["id"])
    by_type: dict[str, list] = {t: [] for t in BOND_LABELS}
    for row in bonds:
        other_id = row["wolf_b_id"] if row["wolf_a_id"] == user["id"] else row["wolf_a_id"]
        other = db.get_user_by_id(other_id)
        if not other:
            continue
        by_type[row["bond_type"]].append((other["wolf_name"], row))

    COMPLICATED_THRESHOLD = 30
    friend_names = {name for name, _ in by_type["friendship"]}
    rival_names = {name for name, _ in by_type["rivalry"]}
    complicated_names = {
        name for name in friend_names & rival_names
        if any(int(r["strength"]) >= COMPLICATED_THRESHOLD for n, r in by_type["friendship"] if n == name)
        and any(int(r["strength"]) >= COMPLICATED_THRESHOLD for n, r in by_type["rivalry"] if n == name)
    }

    for bond_type, label in BOND_LABELS.items():
        rows = by_type[bond_type]
        if not rows:
            continue
        if bond_type == "kin":
            rows = [(n, r) for n, r in rows if not str(r["note"] or "").startswith("found family:")]
        if not rows:
            continue
        lines = []
        for name, row in sorted(rows, key=lambda x: -x[1]["strength"])[:8]:
            rival = bond_type == "rivalry"
            romantic = bond_type in ("romance", "fling")
            tier = strength_tier(row["strength"], rivalry=rival, romance=romantic)
            bar = strength_bar(row["strength"])
            note = f"; _{row['note']}_" if row["note"] else ""
            complicated = " ⁑" if name in complicated_names else ""
            lines.append(f"**{name}** {bar} ({tier}){note}{complicated}")
        if len(rows) > 8:
            lines.append(f"_+{len(rows) - 8} more._")
        sections.append(f"**{label}**\n" + "\n".join(lines))
    if complicated_names:
        sections.append("_⁑ complicated; friendship and rivalry both run high._")

    if not sections:
        return (
            "no bonds recorded yet.\n\n"
            "use **`/bonds action:set`** to mark friendships, rivalries, kin, romances, or flings. "
            "**`/playpen action:socialize`** and **`action:groom`** deepen friendships over time."
        )
    return "\n\n".join(sections)
