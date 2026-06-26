"""Kickstarter backer badge and Tier 2 fulfillment helpers."""

from __future__ import annotations

import database as db
from config import (
    KICKSTARTER_BACKER_LABEL,
    KICKSTARTER_TIER2_BONES,
    KICKSTARTER_TIER2_BONUS_ITEMS,
)


def kickstarter_badge_text() -> str:
    return f"🌲 {KICKSTARTER_BACKER_LABEL}"


def kickstarter_status_lines(discord_id: int) -> list[str]:
    if not db.is_kickstarter_backer(discord_id):
        return []
    return [
        f"**{KICKSTARTER_BACKER_LABEL}**",
        f"• {kickstarter_badge_text()}; shown on `/profile` for your wolves.",
    ]


def profile_footer_suffix(discord_id: int) -> str | None:
    if not db.is_kickstarter_backer(discord_id):
        return None
    return kickstarter_badge_text()


def grant_tier2_rewards(
    discord_id: int,
    *,
    bonus_item: str,
    grant_badge: bool = True,
    grant_bones: bool = True,
) -> tuple[bool, str]:
    """Fulfill Kickstarter Tier 2: badge, 75 bones, one inventory item."""
    if bonus_item not in KICKSTARTER_TIER2_BONUS_ITEMS:
        allowed = ", ".join(KICKSTARTER_TIER2_BONUS_ITEMS)
        return False, f"Invalid bonus item. Pick one of: {allowed}."

    user = db.get_user(discord_id)
    if not user:
        return False, "Player must `/register` a wolf before Tier 2 rewards."

    item = db.get_item_by_key(bonus_item)
    if not item:
        allowed = ", ".join(KICKSTARTER_TIER2_BONUS_ITEMS)
        return False, f"Shop item `{bonus_item}` not found in database. Pick one of: {allowed}."

    notes: list[str] = []
    if grant_badge:
        if db.grant_kickstarter_backer(discord_id):
            notes.append(kickstarter_badge_text())
        else:
            notes.append(f"{KICKSTARTER_BACKER_LABEL} badge (already granted)")

    if grant_bones:
        db.add_bones(discord_id, KICKSTARTER_TIER2_BONES, wolf_id=user["id"])
        notes.append(f"**+{KICKSTARTER_TIER2_BONES}** bones")

    db.grant_item(discord_id, item["id"])
    notes.append(f"**{item['name']}** in `/bones action:inventory`")

    return True, " · ".join(notes)
