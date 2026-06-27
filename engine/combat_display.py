"""Shared combat display helpers (no cog imports)."""

from __future__ import annotations

import json

import database as db
from discord.ext import commands


def fighter_val(fighter, key: str, default=None):
    """Read a combat_fighters row column (sqlite3.Row has no .get())."""
    return db.row_val(fighter, key, default)


def is_npc_fighter(fighter) -> bool:
    return bool(fighter["npc_name"])


def fighter_name(fighter, bot: commands.Bot) -> str:
    if fighter["npc_name"]:
        return fighter["npc_name"]
    user = db.get_user(fighter["discord_id"])
    if user:
        return user["wolf_name"]
    member = bot.get_user(fighter["discord_id"])
    return member.display_name if member else "unknown"


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


def sole_living_opponent(enc_id: int, attacker_fighter_id: int) -> int | None:
    """When only one enemy remains, return their fighter id (hunt prey, 1v1)."""
    opponents = [
        f["id"]
        for f in db.get_combat_fighters(enc_id)
        if f["hp"] > 0 and f["id"] != attacker_fighter_id
    ]
    if len(opponents) == 1:
        return opponents[0]
    return None


def is_valid_attack_target(enc_id: int, attacker_fighter_id: int, target_id: int) -> bool:
    defender = db.get_combat_fighter(enc_id, target_id)
    if not defender or defender["hp"] <= 0:
        return False
    return defender["id"] != attacker_fighter_id


def pick_combat_target(discord_id: int, enc_id: int, attacker_fighter_id: int) -> int | None:
    """Locked target, or auto-lock the only living opponent."""
    tid = db.get_combat_target(discord_id, enc_id)
    if tid:
        if is_valid_attack_target(enc_id, attacker_fighter_id, tid):
            return tid
        db.clear_combat_target(discord_id, enc_id)
    sole = sole_living_opponent(enc_id, attacker_fighter_id)
    if sole:
        db.set_combat_target(discord_id, enc_id, sole)
        return sole
    return None
