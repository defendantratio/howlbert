"""Bond life-event text for sunrise den news."""

from __future__ import annotations


def bond_tier(strength: int, bond_type: str) -> str:
    if bond_type == "romance":
        if strength >= 80:
            return "devoted"
        if strength >= 60:
            return "smitten"
        if strength >= 40:
            return "courting"
        return "drawn together"
    if strength >= 80:
        return "unshakable"
    if strength >= 60:
        return "close"
    if strength >= 40:
        return "steady"
    return "growing"


def bond_cooling_line(name_a: str, name_b: str, bond_type: str, threshold: int) -> str:
    old_label = bond_tier(threshold, bond_type)
    new_label = bond_tier(threshold - 1, bond_type)
    if bond_type == "romance":
        return (
            f"_something has cooled between **{name_a}** and **{name_b}**; "
            f"what was **{old_label}** feels **{new_label}** now._"
        )
    return (
        f"_**{name_a}** and **{name_b}**; a bond that once ran **{old_label}** "
        f"has drifted to **{new_label}**. distance does that._"
    )


def bond_graduation_line(name_a: str, name_b: str) -> str:
    return (
        f"**{name_a}** and **{name_b}**; their mentorship has run its course; "
        f"something quieter and steadier has taken root."
    )
