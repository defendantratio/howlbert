"""Wolf bonds; friendships, rivalries, kin, mentors, and found families."""

from __future__ import annotations

import database as db

BOND_TYPES = frozenset({"friendship", "rivalry", "kin", "mentor"})

BOND_LABELS = {
    "friendship": "Friendship",
    "rivalry": "Rivalry",
    "kin": "Kin",
    "mentor": "Mentor",
}

FAMILY_ROLES = frozenset({"founder", "parent", "sibling", "cub", "member"})

FAMILY_ROLE_LABELS = {
    "founder": "Founder",
    "parent": "Parent",
    "sibling": "Sibling",
    "cub": "Cub",
    "member": "Member",
}


def strength_tier(strength: int, *, rivalry: bool = False) -> str:
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


def apply_socialize_bonds(user, partner, outcome: str, *, day: int = 0) -> str | None:
    """Adjust bond strength from /socialize; returns optional note line."""
    notes: list[str] = []
    if outcome == "warm":
        row = db.adjust_bond_strength(user["id"], partner["id"], "friendship", 10, day=day)
        if row:
            notes.append(
                f"Bond; **{partner['wolf_name']}**: friendship **{strength_bar(row['strength'])}** "
                f"({strength_tier(row['strength'])})"
            )
    elif outcome == "good":
        row = db.adjust_bond_strength(user["id"], partner["id"], "friendship", 5, day=day)
        if row:
            if row["strength"] >= 40:
                notes.append(f"Bond with **{partner['wolf_name']}** grows warmer.")
            else:
                notes.append(
                    f"Bond; **{partner['wolf_name']}**: friendship **{strength_bar(row['strength'])}** "
                    f"({strength_tier(row['strength'])})"
                )
    elif outcome == "awkward":
        db.adjust_bond_strength(user["id"], partner["id"], "rivalry", 5, day=day)
        db.adjust_bond_strength(user["id"], partner["id"], "friendship", -3, day=day)
        notes.append(f"Tension with **{partner['wolf_name']}**; rivalry stirs.")
    elif outcome == "scrap":
        r = db.adjust_bond_strength(user["id"], partner["id"], "rivalry", 12, day=day)
        db.adjust_bond_strength(user["id"], partner["id"], "friendship", -8, day=day)
        if r and r["strength"] >= 40:
            notes.append(
                f"**{partner['wolf_name']}**; rivalry **{strength_bar(r['strength'])}** "
                f"({strength_tier(r['strength'], rivalry=True)})"
            )
    return "\n".join(notes) if notes else None


def apply_groom_bonds(user, partner, *, day: int = 0) -> str | None:
    row = db.adjust_bond_strength(user["id"], partner["id"], "friendship", 3, day=day)
    if not row:
        return None
    return (
        f"Bond; **{partner['wolf_name']}**: friendship **{strength_bar(row['strength'])}** "
        f"({strength_tier(row['strength'])})"
    )


def format_bonds_embed_body(user) -> str:
    sections: list[str] = []

    mate = db.get_bonded_mate(user)
    if mate:
        sections.append(f"**Bonded mate**; {mate['wolf_name']}")

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
        sections.append(f"**Found family: {family['name']}**\n" + "\n".join(lines) + extra)

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
            tier = strength_tier(row["strength"], rivalry=rival)
            bar = strength_bar(row["strength"])
            note = f"; _{row['note']}_" if row["note"] else ""
            lines.append(f"**{name}** {bar} ({tier}){note}")
        if len(rows) > 8:
            lines.append(f"_+{len(rows) - 8} more._")
        sections.append(f"**{label}**\n" + "\n".join(lines))

    if not sections:
        return (
            "No bonds recorded yet.\n\n"
            "Use **`/bonds action:Set`** to mark friendships, rivalries, or kin. "
            "**`/playpen action:socialize`** and **`action:groom`** deepen friendships over time."
        )
    return "\n\n".join(sections)
