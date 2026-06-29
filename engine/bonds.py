"""Wolf bonds; friendships, rivalries, kin, mentors, and found families."""

from __future__ import annotations

import database as db
from config import (
    BOND_DECAY_IDLE_DAYS,
    JEALOUSY_MOOD_PENALTY,
    JEALOUSY_RIVALRY_GAIN,
    KIN_REUNION_BOND_GAIN,
    KIN_REUNION_MOOD_BONUS,
)

BOND_TYPES = frozenset({"friendship", "rivalry", "kin", "mentor", "romance"})

BOND_LABELS = {
    "friendship": "friendship",
    "rivalry": "rivalry",
    "kin": "kin",
    "mentor": "mentor",
    "romance": "romance",
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


def has_strong_positive_bond(wolf_a_id: int, wolf_b_id: int) -> bool:
    """
    True if these two wolves share a deep enough friendship/romance/kin/mentor
    bond that it should matter beyond the bond list — personal trust
    outweighing pack politics, not just a number on a sheet.
    """
    if not wolf_a_id or not wolf_b_id:
        return False
    for bond_type in POSITIVE_BOND_TYPES:
        bond = db.get_bond(wolf_a_id, wolf_b_id, bond_type)
        if bond and int(bond["strength"]) >= STRONG_BOND_THRESHOLD:
            return True
    return False


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
    filled = round(s / 20)
    return "●" * filled + "○" * (5 - filled)


def _format_bond_note(partner_name: str, bond_type: str, row, *, label: str | None = None) -> str:
    display = label or BOND_LABELS.get(bond_type, bond_type.title()).lower()
    rival = bond_type == "rivalry"
    romantic = bond_type == "romance"
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
    for bond_type in ("kin", "mentor", "romance", "friendship", "rivalry"):
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


def apply_groom_bonds(user, partner, *, day: int = 0) -> str | None:
    bond_type, label = _pair_bond_kind(user, partner)
    row = db.adjust_bond_strength(user["id"], partner["id"], bond_type, 3, day=day)
    if not row:
        return None
    return _format_bond_note(partner["wolf_name"], bond_type, row, label=label)


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

    for bond_type, label in BOND_LABELS.items():
        rows = by_type[bond_type]
        if not rows:
            continue
        lines = []
        for name, row in sorted(rows, key=lambda x: -x[1]["strength"])[:8]:
            rival = bond_type == "rivalry"
            romantic = bond_type == "romance"
            tier = strength_tier(row["strength"], rivalry=rival, romance=romantic)
            bar = strength_bar(row["strength"])
            note = f"; _{row['note']}_" if row["note"] else ""
            lines.append(f"**{name}** {bar} ({tier}){note}")
        if len(rows) > 8:
            lines.append(f"_+{len(rows) - 8} more._")
        sections.append(f"**{label}**\n" + "\n".join(lines))

    if not sections:
        return (
            "no bonds recorded yet.\n\n"
            "use **`/bonds action:set`** to mark friendships, rivalries, kin, or romances. "
            "**`/playpen action:socialize`** and **`action:groom`** deepen friendships over time."
        )
    return "\n\n".join(sections)
