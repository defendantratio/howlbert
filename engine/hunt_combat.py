"""Hunt encounters with cornered large prey (deer/elk)."""

from __future__ import annotations

import random

import discord

import database as db
from config import LARGE_PREY_BONES, LARGE_PREY_ENCOUNTER_CHANCE
from engine.bestiary import BESTIARY_NPCS, npc_hp
from engine.character import attr_modifier, get_attr
from utils.currency import format_bones
from utils.embeds import SUCCESS_COLOR, howlbert_embed
from utils.hunting import award_bones

LARGE_PREY_ENCOUNTER_TEXT = [
    "your quarry was no rabbit; a **deer** wheels on you, hooves ready.",
    "an **elk** bursts from the brush, antlers lowered. it will not flee.",
    "The herd broke wrong; one **stag** stands its ground instead of running.",
    "Heavy scent, heavy breath; **large prey** turns to fight for its life.",
]

LARGE_PREY_LABELS = (
    "cornered deer",
    "fighting elk",
    "desperate stag",
)


def roll_large_prey_encounter() -> bool:
    return random.randint(1, 100) <= LARGE_PREY_ENCOUNTER_CHANCE


PREY_NPC_NAMES = (
    "cornered deer",
    "fighting elk",
    "Desperate Stag",
)


def start_large_prey_fight(user, *, guild_id: int, channel_id: int) -> int:
    """Begin an active combat vs large prey. Returns encounter id."""
    template = BESTIARY_NPCS["large_prey"]
    prey_hp = npc_hp(template)
    prey_name = random.choice(PREY_NPC_NAMES)
    enc_id = db.setup_hunt_prey_encounter(
        guild_id,
        channel_id,
        user["discord_id"],
        user["id"],
        hunter_hp=user["hp"],
        hunter_max_hp=user["max_hp"],
        prey_hp=prey_hp,
        prey_name=prey_name,
    )
    enc = db.get_encounter(enc_id)
    if not enc or enc["status"] != "active":
        db.rebuild_encounter_initiative(enc_id)
    fighters = db.get_combat_fighters(enc_id)
    prey = next((f for f in fighters if f["npc_name"]), None)
    if prey:
        db.set_combat_target(user["discord_id"], enc_id, prey["id"])
    return enc_id


def enrich_large_prey_embed(
    embed: discord.Embed,
    enc_id: int,
    user,
    *,
    day: int,
) -> discord.Embed:
    """Add fight roster and turn hint so the hunt works even if the panel is slow to load."""
    from engine.combat_display import current_fighter_for_enc
    from engine.role_privileges import hunts_left_footer

    enc = db.get_encounter(enc_id)
    if not enc:
        embed.description = (
            (embed.description or "")
            + "\n\n_combat failed to open; try **`/bones action:hunt`** again or `/combat list`._"
        )
        return embed

    fighters = db.get_combat_fighters(enc_id)
    hunter_name = user["wolf_name"] if user and "wolf_name" in user.keys() else "Hunter"
    lines = [f"fight **#{enc_id}**"]
    for fighter in fighters:
        label = fighter["npc_name"] or hunter_name
        lines.append(f"· **{label}** {fighter['hp']}/{fighter['max_hp']} hp")

    if enc["status"] == "active":
        current = current_fighter_for_enc(enc_id)
        actor = (current["npc_name"] if current and current["npc_name"] else hunter_name) if current else hunter_name
        lines.append(
            f"\n**round {enc['round']}**; **{actor}** acts first. "
            "on your turn: **bite** or **claw** (auto-targets lone prey), or pick from the target menu."
        )
    else:
        lines.append(
            f"\n_combat status **{enc['status']}**; `/combat status encounter:{enc_id}` to recover the panel._"
        )

    embed.description = (embed.description or "") + "\n\n" + "\n".join(lines)
    footer = (
        f"~{LARGE_PREY_ENCOUNTER_CHANCE}% hunt chance · down the prey to open the fresh-kill cache"
        f" · {hunts_left_footer(user, day)}"
    )
    embed.set_footer(text=footer)
    return embed


def is_hunt_prey_encounter(enc) -> bool:
    if not enc:
        return False
    return bool(enc["is_hunt_prey"] if "is_hunt_prey" in enc.keys() else False)


def is_large_prey_fighter(fighter) -> bool:
    if not fighter or not fighter["npc_name"]:
        return False
    if "npc_template" in fighter.keys() and fighter["npc_template"]:
        return fighter["npc_template"] == "large_prey"
    return (
        "large prey" in fighter["npc_name"]
        or "deer" in fighter["npc_name"].lower()
        or "elk" in fighter["npc_name"].lower()
        or "stag" in fighter["npc_name"].lower()
    )


async def try_complete_hunt_prey_victory(
    bot: discord.Client,
    channel: discord.abc.Messageable,
    enc_id: int,
) -> discord.Embed | None:
    """
    If the hunter downed large prey, award hunt bones and post the prey pile.
    Returns a victory embed, or None if not applicable.
    """
    enc = db.get_encounter(enc_id)
    if not is_hunt_prey_encounter(enc):
        return None
    if enc["hunt_prey_rewarded"] if "hunt_prey_rewarded" in enc.keys() else False:
        return None

    collab_hunt_id = int(enc["collab_hunt_id"]) if "collab_hunt_id" in enc.keys() and enc["collab_hunt_id"] else 0
    if collab_hunt_id:
        from engine.collab_hunt import complete_collab_hunt_large_prey

        return await complete_collab_hunt_large_prey(bot, channel, enc_id, collab_hunt_id)

    fighters = db.get_combat_fighters(enc_id)
    prey = next((f for f in fighters if is_large_prey_fighter(f)), None)
    if not prey or prey["hp"] > 0:
        return None

    hunter_wolf_id = enc["hunter_wolf_id"] if "hunter_wolf_id" in enc.keys() else None
    hunter_discord_id = enc["hunter_discord_id"] if "hunter_discord_id" in enc.keys() else None
    hunter_f = next(
        (
            f
            for f in fighters
            if (hunter_wolf_id and f["wolf_id"] == hunter_wolf_id)
            or (hunter_discord_id and f["discord_id"] == hunter_discord_id)
        ),
        None,
    )
    if not hunter_f or hunter_f["hp"] <= 0:
        db.mark_hunt_prey_rewarded(enc_id)
        db.end_encounter(enc_id)
        return howlbert_embed(
            "prey escapes",
            "the kill is yours, but you're too wounded to drag it to the cache.",
            color=SUCCESS_COLOR,
        )

    user = db.get_user_by_id(hunter_wolf_id) if hunter_wolf_id else None
    if not user and hunter_discord_id:
        user = db.get_user(hunter_discord_id)
    if not user:
        return None

    guild_id = enc["guild_id"]
    world = db.get_world(guild_id)
    dex_bonus = max(0, attr_modifier(get_attr(user, "dex")))
    amount = random.randint(*LARGE_PREY_BONES) + dex_bonus
    net_amount, tax, payout, lucky_bonus, _, _, _, _, _ = award_bones(
        user, amount, world["weather"], "hunt", season=world["season"]
    )

    prey_label = random.choice(LARGE_PREY_LABELS)
    prey_key = "elk" if "elk" in prey_label.lower() else "deer"
    from engine.hunt_payout import grant_prey_carcass_canonical

    grant_prey_carcass_canonical(
        user["id"],
        guild_id=guild_id,
        day=world["day_number"],
        prey_key=prey_key,
    )
    db.update_user(
        user["discord_id"],
        wolf_id=user["id"],
        last_hunt_yield=payout,
        last_prey_label=prey_label,
    )
    db.mark_hunt_prey_rewarded(enc_id)
    db.end_encounter(enc_id)

    # solo kill: the carcass goes straight into the hunter's inventory (granted
    # above). we do NOT auto-open a fresh-kill pile; the hunter chooses when to
    # share it with the den via `/preypile`, after which leftovers roll into the
    # pack stash.
    embed = howlbert_embed("fresh-kill secured", color=SUCCESS_COLOR)
    embed.description = (
        f"you bring down the **{prey_label}** and drag it home.\n"
        "the carcass is in your **inventory** (`/inventory`); share it with the den "
        "any time via **`/preypile`**, or **`/eat`** it yourself."
    )
    embed.add_field(name="haul", value=format_bones(net_amount, signed=True), inline=True)
    if lucky_bonus > 0:
        embed.add_field(name="lucky tooth", value=format_bones(lucky_bonus, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="pack tax", value=format_bones(tax), inline=True)
    from engine.blooding import award_blooding_on_hunt

    blooding_note = award_blooding_on_hunt(user)
    if blooding_note:
        embed.set_footer(text=blooding_note)
    return embed
