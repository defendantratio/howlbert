"""Grant prey carcasses when a wolf downs a foe in combat."""

from __future__ import annotations

import database as db
from engine.hunt_combat import is_hunt_prey_encounter
from engine.hunt_payout import grant_prey_carcass_canonical
from engine.prey_items import prey_meta

# Bestiary template key -> prey hoard key (large_prey handled by hunt_combat).
NPC_TEMPLATE_PREY: dict[str, str] = {
    "coyote": "coyote",
    "fox": "fox",
    "badger": "badger",
    "wolverine": "wolverine",
    "cougar": "cougar",
    "black_bear": "black_bear",
    "grizzly_bear": "grizzly_bear",
    "dog_feral": "feral_dog",
    "dog_guard": "guard_dog",
    "dog_hunting": "hunting_dog",
    "dog_fighting": "fighting_dog",
    "clan_warrior": "cat_carcass",
    "clan_deputy": "cat_carcass",
    "rogue_cat": "cat_carcass",
    "loner_cat": "cat_carcass",
    "kittypet": "kittypet_carcass",
    "water_snake": "snake",
    "garter_snake": "snake",
    "skink": "lizard",
}


def prey_key_for_npc_template(template_key: str | None) -> str | None:
    if not template_key:
        return None
    return NPC_TEMPLATE_PREY.get(template_key)


def try_grant_combat_kill_carcass(
    enc_id: int,
    killer_discord_id: int,
    defender_f,
) -> str | None:
    """
    Add a carcass to the killer's hoard when they drop a foe to 0 HP.
    Returns a short note for the combat embed, or None.
    """
    enc = db.get_encounter(enc_id)
    if not enc:
        return None

    killer = db.get_user(killer_discord_id)
    if not killer:
        return None

    world = db.get_world(enc["guild_id"])
    day = world["day_number"]

    is_npc = bool(defender_f["npc_name"] if "npc_name" in defender_f.keys() else None)
    if is_npc:
        if is_hunt_prey_encounter(enc):
            return None
        template = (
            defender_f["npc_template"]
            if "npc_template" in defender_f.keys()
            else None
        )
        prey_key = prey_key_for_npc_template(template)
        if not prey_key:
            return None
    else:
        defender_wolf_id = defender_f["wolf_id"] if "wolf_id" in defender_f.keys() else None
        defender_discord = defender_f["discord_id"] if "discord_id" in defender_f.keys() else None
        if defender_discord == killer_discord_id:
            return None
        if defender_wolf_id and defender_wolf_id == killer["id"]:
            return None
        prey_key = "wolf_carcass"

    name = grant_prey_carcass_canonical(
        killer["id"],
        guild_id=enc["guild_id"],
        day=day,
        prey_key=prey_key,
    )
    meta = prey_meta(prey_key)
    note = f"**{name}** dragged to your hoard (`/prey`)."
    if prey_key == "wolf_carcass":
        note += (
            " _Wolf meat is edible; private `/eat` costs mood and might slip by; "
            "`/preypile`, `/pack stash deposit`, or `/packlife feedall` with wolf flesh always gets you caught._"
        )
    return note
