"""Border skirmishes; clan cat patrols from /sniff (Warrior Cats-style)."""

from __future__ import annotations

import random

import discord

import database as db
from config import BORDER_CAT_BONES, BORDER_CAT_MOOD, BORDER_CAT_STANDING
from engine.bestiary import BESTIARY_NPCS, npc_hp
from utils.currency import format_bones
from utils.embeds import SUCCESS_COLOR, howlbert_embed
from utils.hunting import award_bones

BORDER_CAT_WEIGHTS: tuple[tuple[str, int], ...] = (
    ("clan_warrior", 40),
    ("loner_cat", 20),
    ("rogue_cat", 18),
    ("clan_deputy", 12),
    ("kittypet", 10),
)

BORDER_ENCOUNTER_TEXT = {
    "clan_warrior": (
        "a **clan warrior** drops from the branches; forest-cat scent, bristling tail, "
        "eyes on your throat.",
        "Moss and cat-musk on the wind. A **patrol cat** steps onto the trail, fur on end.",
    ),
    "clan_deputy": (
        "This isn't a lone hunter; a **clan deputy** leads the patrol, scars along one ear.",
        "A **deputy cat** blocks the border, gaze cold. The rest of the patrol hangs back in the trees.",
    ),
    "rogue_cat": (
        "A **rogue** slinks from the bracken; no clan scent, only hunger and spite.",
        "Torn ears and a ragged coat: a **rogue cat** means to steal your kill or your life.",
    ),
    "loner_cat": (
        "A **loner** freezes on the ridge; neither clan nor kittypet, just another predator.",
        "Solitary cat-scent. A **loner** watches your every step from the holly.",
    ),
    "kittypet": (
        "A plump **kittypet** wandered too far from the Twoleg nests; it yowls when it sees you.",
        "Collar-bells and milk-scent: a lost **kittypet** hisses from behind a stump.",
    ),
}

BORDER_VICTORY_TEXT = (
    "the cat breaks off, spitting, and melts back toward **cat territory**.",
    "you drive the patrol back across the scent-line; for now, the border holds.",
    "The forest-cat retreats, leaving claw-marks in the bark and fury in the air.",
)


def pick_border_cat_template() -> str:
    keys, weights = zip(*BORDER_CAT_WEIGHTS)
    return random.choices(keys, weights=weights, k=1)[0]


def border_encounter_flavor(template_key: str) -> str:
    lines = BORDER_ENCOUNTER_TEXT.get(template_key, BORDER_ENCOUNTER_TEXT["clan_warrior"])
    return random.choice(lines)


def start_border_cat_fight(
    user,
    *,
    guild_id: int,
    channel_id: int,
    pick: tuple[str, str, bool] | None = None,
) -> tuple[int, str, str]:
    """Begin active combat vs a border cat. Returns (encounter_id, template_key, flavor)."""
    from engine.cat_pacts import pick_border_cat_for_pack

    if pick is None:
        template_key, clan_name, violation = pick_border_cat_for_pack(guild_id, user["pack_id"])
    else:
        template_key, clan_name, violation = pick
    template = BESTIARY_NPCS[template_key]
    cat_hp = npc_hp(template)
    named = None
    if template_key in ("clan_warrior", "clan_deputy"):
        from engine.cat_clans import pick_border_cat_display_name

        named = pick_border_cat_display_name(clan_name, template_key)
    display_name = named or f"{clan_name} {template['name']}"
    enc_id = db.setup_border_cat_encounter(
        guild_id,
        channel_id,
        user["discord_id"],
        user["id"],
        hunter_hp=user["hp"],
        hunter_max_hp=user["max_hp"],
        cat_hp=cat_hp,
        cat_name=display_name,
        cat_template=template_key,
        border_cat_clan=clan_name,
        border_pact_violation=violation,
    )
    flavor = border_encounter_flavor(template_key)
    if named:
        flavor = f"**{named.split(' (', 1)[0]}** blocks the trail.\n\n{flavor}"
    elif clan_name:
        flavor = flavor.replace("clan warrior", f"**{clan_name}** warrior").replace(
            "clan deputy", f"**{clan_name}** deputy"
        )
        if clan_name not in flavor:
            flavor = f"**{clan_name}** scent on the wind.\n\n{flavor}"
    if violation:
        flavor += "\n\n_this patrol answers to a clan your den has sworn peace with; blood here has consequences._"
    return enc_id, template_key, flavor


def is_border_fight_encounter(enc) -> bool:
    if not enc:
        return False
    return bool(enc["is_border_fight"] if "is_border_fight" in enc.keys() else False)


def is_border_cat_fighter(fighter) -> bool:
    if not fighter or not fighter["npc_name"]:
        return False
    if "npc_template" in fighter.keys() and fighter["npc_template"]:
        key = fighter["npc_template"]
        return key in BESTIARY_NPCS and BESTIARY_NPCS[key]["category"] == "cats"
    return False


async def try_complete_border_victory(
    bot: discord.Client,
    channel: discord.abc.Messageable,
    enc_id: int,
) -> discord.Embed | None:
    """If the wolf drove off a border cat, award standing/mood/bones."""
    enc = db.get_encounter(enc_id)
    if not is_border_fight_encounter(enc):
        return None
    if enc["border_fight_rewarded"] if "border_fight_rewarded" in enc.keys() else False:
        return None

    fighters = db.get_combat_fighters(enc_id)
    cat = next((f for f in fighters if is_border_cat_fighter(f)), None)
    if not cat or cat["hp"] > 0:
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
        db.mark_border_fight_rewarded(enc_id)
        db.end_encounter(enc_id)
        return howlbert_embed(
            "cat escapes",
            "the patrol cat limps off; but you're too hurt to claim the border.",
            color=SUCCESS_COLOR,
        )

    user = db.get_user_by_id(hunter_wolf_id) if hunter_wolf_id else None
    if not user and hunter_discord_id:
        user = db.get_user(hunter_discord_id)
    if not user:
        return None

    guild_id = enc["guild_id"]
    world = db.get_world(guild_id)
    amount = random.randint(*BORDER_CAT_BONES)
    net_amount, tax, _, lucky_bonus, _, _, _, _, _ = award_bones(
        user, amount, world["weather"], "work"
    )

    db.adjust_mood(user["id"], BORDER_CAT_MOOD)
    db.adjust_wolf_standing(user["discord_id"], BORDER_CAT_STANDING)
    db.mark_border_fight_rewarded(enc_id)
    db.end_encounter(enc_id)

    violation_note = None
    if user["pack_id"]:
        from engine.cat_pacts import handle_border_pact_violation

        cat_template = None
        if cat and "npc_template" in cat.keys():
            cat_template = cat["npc_template"]
        violation_note = handle_border_pact_violation(
            user,
            guild_id=guild_id,
            enc=enc,
            cat_template=cat_template,
        )

    cat_name = cat["npc_name"] or "The patrol cat"
    embed = howlbert_embed("border held", color=SUCCESS_COLOR)
    embed.description = (
        f"{random.choice(BORDER_VICTORY_TEXT)}\n\n"
        f"**{cat_name}** driven back.\n"
        f"**+{BORDER_CAT_STANDING} standing** · **+{BORDER_CAT_MOOD} mood**"
    )
    if violation_note:
        embed.description += violation_note
    embed.add_field(name="spoils", value=format_bones(net_amount, signed=True), inline=True)
    if lucky_bonus > 0:
        embed.add_field(name="lucky tooth", value=format_bones(lucky_bonus, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="pack tax", value=format_bones(tax), inline=True)
    embed.set_footer(text="/field action:sniff · /pact action:view")
    return embed
