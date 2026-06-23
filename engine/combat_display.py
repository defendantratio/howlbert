"""Shared combat display helpers (no cog imports)."""

from __future__ import annotations

import json

import database as db
from discord.ext import commands


def is_npc_fighter(fighter) -> bool:
    return bool(fighter["npc_name"])


def fighter_name(fighter, bot: commands.Bot) -> str:
    if fighter["npc_name"]:
        return fighter["npc_name"]
    user = db.get_user(fighter["discord_id"])
    if user:
        return user["wolf_name"]
    member = bot.get_user(fighter["discord_id"])
    return member.display_name if member else "Unknown"


def assign_npc_display_name(encounter_id: int, template_key: str, base_name: str) -> str:
    """Number duplicate NPCs in one fight (Kittypet 1, 2, 3, …)."""
    fighters = db.get_combat_fighters(encounter_id)
    same = sorted(
        (f for f in fighters if f["npc_template"] == template_key),
        key=lambda f: f["id"],
    )
    n = len(same) + 1
    if n == 1:
        return base_name

    for i, fighter in enumerate(same, 1):
        label = f"{base_name} {i}"
        if fighter["npc_name"] != label:
            db.update_fighter_npc_name(fighter["id"], label)
    return f"{base_name} {n}"


def current_fighter_for_enc(enc_id: int):
    enc = db.get_encounter(enc_id)
    if not enc or enc["status"] != "active":
        return None
    order = json.loads(enc["turn_order"])
    if not order:
        return None
    idx = enc["current_turn"]
    if idx < 0 or idx >= len(order):
        return None
    return db.get_combat_fighter(enc_id, order[idx])
