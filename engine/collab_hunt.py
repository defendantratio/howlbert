"""Pack collaborative hunt; call, join, set out together."""

from __future__ import annotations

import random

import discord

import database as db
from config import (
    COLLAB_HUNT_ALL_HUNTERS_BONUS,
    COLLAB_HUNT_BONUS_PCT_PER_WOLF,
    COLLAB_HUNT_MAX_WOLVES,
    COLLAB_HUNT_MIN_WOLVES,
    COLLAB_HUNT_MOOD_BONUS,
    HUNT_WILD_ENCOUNTER_CHANCE,
    LARGE_PREY_BONES,
    LARGE_PREY_ENCOUNTER_CHANCE,
)
from engine.character import attr_modifier, get_attr
from engine.hunt import roll_hunt_amount
from engine.hunt_combat import (
    LARGE_PREY_ENCOUNTER_TEXT,
    roll_large_prey_encounter,
    start_large_prey_fight,
)
from engine.hunt_payout import grant_prey_carcass_canonical, hunt_flavor_for_payout, prey_key_for_payout
from engine.injury_effects import hunt_blocked_by_injury
from engine.role_privileges import can_hunt_again, hunts_remaining_today, is_hunter, record_hunt_use
from engine.role_restrictions import young_wolf_block
from engine.sniff import apply_sniff_bone_bonus
from engine.vitals import full_activity_block
from engine.wild_encounters import ambush_embed, maybe_start_activity_ambush
from utils.currency import format_bones
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from utils.hunting import award_bones

COLLAB_FLAVOR = [
    "The pack fans out through birch and stone; scent thick, voices low.",
    "You move as one line through the timber, flankers holding the wind.",
    "A coordinated drive; no lone wolf's gamble, but the den's work.",
    "Calls and tail signals; the quarry has nowhere left to run.",
]

COLLAB_SUCCESS_FLAVOR = [
    "The kill is shared work; meat and marrow for every jaw that held the line.",
    "Flankers, chasers, and the leader's bite; the forest yields to the pack.",
    "A clean takedown. Even the elders would nod at this hunt.",
]


def _party_users(hunt_id: int) -> list:
    members = db.get_collab_hunt_members(hunt_id)
    users = [db.get_user_by_id(m["wolf_id"]) for m in members]
    return [u for u in users if u]


def _party_names(hunt_id: int) -> str:
    return ", ".join(m["wolf_name"] for m in db.get_collab_hunt_members(hunt_id))


def _hunt_block_reason(user, day: int) -> str | None:
    block = young_wolf_block(user, action="hunt")
    if block:
        return block
    inj = hunt_blocked_by_injury(user)
    if inj:
        return inj
    vitals = full_activity_block(user)
    if vitals:
        return vitals
    if not can_hunt_again(user, day):
        return "You've used your hunt(s) this sunrise."
    if db.wolf_in_open_collab_hunt(user["id"]):
        return "This wolf is already in an open pack hunt."
    return None


def validate_start_collab_hunt(user, *, guild_id: int, day: int) -> str | None:
    if not user.get("pack_id"):
        return "Join a Great Pack first; pack hunts are den business."
    reason = _hunt_block_reason(user, day)
    if reason:
        return reason
    if db.get_open_collab_hunt_by_leader(user["id"]):
        return "You already called a pack hunt. Set out or cancel it first."
    return None


def validate_join_collab_hunt(user, hunt, day: int) -> str | None:
    if hunt["status"] != "open":
        return "This pack hunt is no longer open."
    if user["pack_id"] != hunt["pack_id"]:
        return "Only wolves in the same Great Pack can join."
    members = db.get_collab_hunt_members(hunt["id"])
    if any(m["wolf_id"] == user["id"] for m in members):
        return "This wolf is already on the hunt."
    if len(members) >= COLLAB_HUNT_MAX_WOLVES:
        return f"The hunting party is full ({COLLAB_HUNT_MAX_WOLVES} wolves max)."
    return _hunt_block_reason(user, day)


def wolves_eligible_to_join(discord_id: int, hunt_id: int, day: int) -> list:
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt:
        return []
    member_ids = {m["wolf_id"] for m in db.get_collab_hunt_members(hunt_id)}
    eligible = []
    for wolf in db.list_user_wolves(discord_id):
        if wolf["pack_id"] != hunt["pack_id"]:
            continue
        if wolf["id"] in member_ids:
            continue
        if validate_join_collab_hunt(wolf, hunt, day):
            continue
        eligible.append(wolf)
    return eligible


def build_collab_hunt_embed(hunt_id: int) -> discord.Embed:
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt:
        return howlbert_embed("Pack Hunt", "Hunt not found.", color=ERROR_COLOR)
    members = db.get_collab_hunt_members(hunt_id)
    leader = db.get_user_by_id(hunt["leader_wolf_id"])
    leader_name = leader["wolf_name"] if leader else "Unknown"
    pack = db.get_pack(hunt["pack_id"])
    pack_name = pack["name"] if pack else "the den"

    if hunt["status"] == "open":
        title = "Pack Hunt Called"
        desc = (
            f"**{leader_name}** calls the pack to hunt for **{pack_name}**.\n"
            f"{random.choice(COLLAB_FLAVOR)}\n\n"
            f"**Party** ({len(members)}/{COLLAB_HUNT_MAX_WOLVES}); need at least "
            f"**{COLLAB_HUNT_MIN_WOLVES}** to set out.\n"
            f"Each wolf spends one hunt this sunrise. "
            f"+**{COLLAB_HUNT_BONUS_PCT_PER_WOLF}%** bones per extra hunter.\n"
            f"Large prey and ambushes can still strike; the party fights together (+1 attack per ally, max +3)."
        )
        color = SUCCESS_COLOR
    elif hunt["status"] == "encounter":
        title = "Pack Hunt; Fight!"
        desc = (
            f"The party (**{_party_names(hunt_id)}**) ran into trouble.\n"
            "Combat is live below; bring it down to finish the hunt."
        )
        color = SUCCESS_COLOR
    elif hunt["status"] == "done":
        title = "Pack Hunt Complete"
        desc = hunt["result_text"] or "The party returned to the den."
        color = SUCCESS_COLOR
    else:
        title = "Pack Hunt Closed"
        desc = "This hunt was cancelled or the den rolled over."
        color = ERROR_COLOR

    embed = howlbert_embed(title, desc, color=color)
    if members:
        lines = []
        for m in members:
            tag = " (caller)" if m["wolf_id"] == hunt["leader_wolf_id"] else ""
            hunter = ""
            w = db.get_user_by_id(m["wolf_id"])
            if w and is_hunter(w):
                hunter = " · Hunter"
            lines.append(f"• **{m['wolf_name']}**{tag}{hunter}")
        embed.add_field(name="Wolves", value="\n".join(lines), inline=False)
    if hunt["status"] == "open":
        embed.set_footer(
            text=f"Join with the button · Caller sets out when ready · max {COLLAB_HUNT_MAX_WOLVES} wolves"
        )
    return embed


def _compute_collab_base(users: list, *, fixed_base: int | None = None) -> tuple[int, int]:
    if fixed_base is not None:
        base = fixed_base
    else:
        base = roll_hunt_amount()
        if base > 0 and users:
            dex_avg = sum(max(0, attr_modifier(get_attr(u, "dex"))) for u in users) // len(users)
            base += dex_avg
    bonus_pct = (len(users) - 1) * COLLAB_HUNT_BONUS_PCT_PER_WOLF if users else 0
    if users and all(is_hunter(u) for u in users):
        bonus_pct += COLLAB_HUNT_ALL_HUNTERS_BONUS
    if base > 0 and bonus_pct:
        base = max(0, int(base * (100 + bonus_pct) / 100))
    return base, bonus_pct


def _record_all_hunt_uses(users: list, day: int) -> None:
    for user in users:
        record_hunt_use(user["discord_id"], wolf_id=user["id"], day=day)


def payout_collab_hunt(
    hunt_id: int,
    *,
    fixed_base: int | None = None,
    encounter_note: str = "",
) -> discord.Embed:
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt:
        return howlbert_embed("Pack Hunt", "Hunt not found.", color=ERROR_COLOR)
    if hunt["status"] == "done":
        return build_collab_hunt_embed(hunt_id)

    guild_id = hunt["guild_id"]
    world = db.get_world(guild_id)
    day = world["day_number"]
    weather = world["weather"]
    season = world["season"]
    users = _party_users(hunt_id)
    leader = db.get_user_by_id(hunt["leader_wolf_id"])

    base, bonus_pct = _compute_collab_base(users, fixed_base=fixed_base)
    share = base // len(users) if users else 0
    remainder = base - share * len(users)

    lines: list[str] = []
    total_payout = 0
    from engine.blooding import award_blooding_on_hunt

    for user in users:
        gross = share + (remainder if user["id"] == hunt["leader_wolf_id"] else 0)
        gross, sniff_bonus, _sniff_note = apply_sniff_bone_bonus(user, gross, day)
        net, tax, payout, lucky_bonus, *_rest = award_bones(
            user, gross, weather, "hunt", season=season
        )
        db.adjust_mood(user["id"], COLLAB_HUNT_MOOD_BONUS)
        total_payout += payout

        parts = [f"**{user['wolf_name']}** {format_bones(net, signed=True)}"]
        if tax:
            parts.append(f"tax {format_bones(tax)}")
        if sniff_bonus:
            parts.append(f"sniff +{sniff_bonus}")
        if lucky_bonus:
            parts.append(f"lucky +{lucky_bonus}")
        lines.append(" · ".join(parts))
        if payout > 0:
            award_blooding_on_hunt(user)

    db.adjust_pack_unity(hunt["pack_id"], 1)

    prey_key = prey_key_for_payout(total_payout) if total_payout > 0 else None
    prey_name = None
    if prey_key and leader:
        prey_name = grant_prey_carcass_canonical(
            leader["id"],
            guild_id=guild_id,
            day=day,
            prey_key=prey_key,
        )
        db.update_user(
            leader["discord_id"],
            wolf_id=leader["id"],
            last_hunt_yield=total_payout,
            last_prey_label=None,
        )
        # Carcass goes to fresh-kill cache for the pack, not private hoard only.

    flavor = random.choice(COLLAB_SUCCESS_FLAVOR)
    if total_payout > 0 and prey_key:
        flavor = hunt_flavor_for_payout(total_payout, prey_key) + "\n\n" + flavor
    if encounter_note:
        flavor = encounter_note + "\n\n" + flavor

    bonus_note = f"+{bonus_pct}% pack bonus"
    if users and all(is_hunter(u) for u in users):
        bonus_note += " (all Hunters)"

    result_text = (
        f"{flavor}\n\n"
        + "\n".join(lines)
        + f"\n\n**{bonus_note}** · pack unity **+1**"
    )
    if prey_name and leader:
        result_text += (
            f"\n**{prey_name}** laid at the den; **fresh-kill cache** opens for the pack (`/preypile` style)."
        )

    db.set_collab_hunt_status(hunt_id, "done", result_text=result_text)
    embed = build_collab_hunt_embed(hunt_id)
    if leader and is_hunter(leader):
        left = hunts_remaining_today(leader, day)
        if left > 0:
            embed.set_footer(text=f"Hunter: {left} hunt(s) left this sunrise for the caller")
    return embed


def resolve_collab_hunt(hunt_id: int) -> tuple[discord.Embed | None, str | None]:
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt or hunt["status"] != "open":
        return None, "This pack hunt is not open."
    members = db.get_collab_hunt_members(hunt_id)
    if len(members) < COLLAB_HUNT_MIN_WOLVES:
        return None, f"Need at least **{COLLAB_HUNT_MIN_WOLVES}** wolves to set out."
    users = _party_users(hunt_id)
    if len(users) < COLLAB_HUNT_MIN_WOLVES:
        return None, "Not enough valid wolves on the hunt."

    world = db.get_world(hunt["guild_id"])
    _record_all_hunt_uses(users, world["day_number"])
    embed = payout_collab_hunt(hunt_id)
    return embed, None


def try_set_out_collab_hunt(hunt_id: int) -> tuple[discord.Embed | None, str | None, int | None]:
    """Set out; may start combat (returns enc_id) or resolve immediately."""
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt or hunt["status"] != "open":
        return None, "This pack hunt is not open.", None
    members = db.get_collab_hunt_members(hunt_id)
    if len(members) < COLLAB_HUNT_MIN_WOLVES:
        return None, f"Need at least **{COLLAB_HUNT_MIN_WOLVES}** wolves to set out.", None

    users = _party_users(hunt_id)
    leader = db.get_user_by_id(hunt["leader_wolf_id"])
    if not leader or len(users) < COLLAB_HUNT_MIN_WOLVES:
        return None, "Not enough valid wolves on the hunt.", None

    guild_id = hunt["guild_id"]
    channel_id = hunt["channel_id"]
    world = db.get_world(guild_id)
    day = world["day_number"]
    party_note = f"Pack hunt: {_party_names(hunt_id)}"

    if roll_large_prey_encounter():
        _record_all_hunt_uses(users, day)
        enc_id = start_large_prey_fight(
            leader,
            guild_id=guild_id,
            channel_id=channel_id,
        )
        db.set_encounter_collab_hunt(enc_id, hunt_id)
        db.set_collab_hunt_status(hunt_id, "encounter")
        flavor = random.choice(LARGE_PREY_ENCOUNTER_TEXT)
        embed = howlbert_embed("Large Prey!", flavor, color=SUCCESS_COLOR)
        embed.set_footer(
            text=f"{party_note} · ~{LARGE_PREY_ENCOUNTER_CHANCE}% chance · caller leads the fight"
        )
        from engine.collab_combat import enroll_collab_party_in_encounter

        enroll_collab_party_in_encounter(enc_id, users, leader_wolf_id=hunt["leader_wolf_id"])
        return embed, None, enc_id

    ambush = maybe_start_activity_ambush(
        leader,
        guild_id=guild_id,
        channel_id=channel_id,
        activity="hunt",
    )
    if ambush:
        enc_id, template_key, flavor = ambush
        db.set_encounter_collab_hunt(enc_id, hunt_id)
        db.set_collab_hunt_status(hunt_id, "encounter")
        embed = ambush_embed(template_key, flavor)
        embed.set_footer(
            text=f"{party_note} · ~{HUNT_WILD_ENCOUNTER_CHANCE}% ambush · win to finish · flee keeps hunts"
        )
        from engine.collab_combat import enroll_collab_party_in_encounter

        enroll_collab_party_in_encounter(enc_id, users, leader_wolf_id=hunt["leader_wolf_id"])
        return embed, None, enc_id

    embed, err = resolve_collab_hunt(hunt_id)
    return embed, err, None


async def complete_collab_hunt_large_prey(
    bot: discord.Client,
    channel: discord.abc.Messageable,
    enc_id: int,
    hunt_id: int,
) -> discord.Embed | None:
    enc = db.get_encounter(enc_id)
    if not enc or int(enc["collab_hunt_id"] or 0) != hunt_id:
        return None
    if enc["hunt_prey_rewarded"] if "hunt_prey_rewarded" in enc.keys() else False:
        return None

    users = _party_users(hunt_id)
    if not users:
        return None

    fighters = db.get_combat_fighters(enc_id)
    from engine.hunt_combat import is_large_prey_fighter

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
        db.set_collab_hunt_status(
            hunt_id,
            "done",
            result_text=(
                "The pack brought down large prey, but the caller was too hurt to drag it home. "
                "Hunts were spent."
            ),
        )
        db.end_encounter(enc_id)
        embed = build_collab_hunt_embed(hunt_id)
        return embed

    world = db.get_world(enc["guild_id"])
    dex_avg = sum(max(0, attr_modifier(get_attr(u, "dex"))) for u in users) // len(users)
    fixed_base = random.randint(*LARGE_PREY_BONES) + dex_avg

    leader = db.get_user_by_id(enc["hunter_wolf_id"] if "hunter_wolf_id" in enc.keys() else 0)
    if not leader:
        leader = db.get_user_by_id(db.get_collab_hunt(hunt_id)["leader_wolf_id"])

    embed = payout_collab_hunt(
        hunt_id,
        fixed_base=fixed_base,
        encounter_note="The pack brought down **large prey** together.",
    )
    db.mark_hunt_prey_rewarded(enc_id)
    db.end_encounter(enc_id)

    if leader:
        from cogs.prey_pile import post_prey_pile_to_channel
        from engine.prey_items import prey_meta

        stack = db.pick_prey_stack_for_pile(leader["id"], world["day_number"])
        pile_bones = stack["bone_value"] if stack else fixed_base
        pile_label = prey_meta(stack["prey_key"])["label"] if stack else "large prey"
        if stack:
            db.remove_prey_stack(stack["id"])
        await post_prey_pile_to_channel(
            bot,
            channel,
            leader,
            prey_bones=pile_bones,
            prey_label=pile_label,
            day_number=world["day_number"],
        )

    hunt = db.get_collab_hunt(hunt_id)
    if hunt and hunt["message_id"]:
        try:
            msg = await channel.fetch_message(hunt["message_id"])
            await msg.edit(embed=build_collab_hunt_embed(hunt_id))
        except (discord.HTTPException, AttributeError):
            pass

    from engine.collab_ui import post_collab_hunt_prey_pile, refresh_collab_hunt_post

    await post_collab_hunt_prey_pile(bot, channel, hunt_id)
    await refresh_collab_hunt_post(bot, hunt_id)
    return embed


def complete_collab_hunt_ambush(hunt_id: int, enc_id: int) -> discord.Embed | None:
    enc = db.get_encounter(enc_id)
    if not enc or int(enc["collab_hunt_id"] or 0) != hunt_id:
        return None
    if enc["ambush_finalized"] if "ambush_finalized" in enc.keys() else False:
        return None
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt or hunt["status"] != "encounter":
        return None

    users = _party_users(hunt_id)
    if not users:
        return None

    from engine.ambush_activity import AMBUSH_WIN_BONES, _ambush_won

    if not _ambush_won(enc_id):
        return None

    world = db.get_world(enc["guild_id"])
    _record_all_hunt_uses(users, world["day_number"])

    gross = random.randint(*AMBUSH_WIN_BONES)
    gross += (len(users) - 1) * 3

    with db.get_db() as conn:
        conn.execute(
            "UPDATE combat_encounters SET ambush_finalized = 1 WHERE id = ?",
            (enc_id,),
        )

    embed = payout_collab_hunt(
        hunt_id,
        fixed_base=gross,
        encounter_note="The pack drove off the ambush and claimed what was left behind.",
    )
    db.end_encounter(enc_id)
    return embed
