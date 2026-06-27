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
from engine.role_privileges import can_hunt_again, hunts_left_footer, is_hunter, record_hunt_use
from engine.role_restrictions import young_wolf_block
from engine.sniff import apply_sniff_bone_bonus
from engine.vitals import full_activity_block
from engine.wild_encounters import ambush_embed, maybe_start_activity_ambush
from utils.currency import format_bones
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from utils.hunting import award_bones

COLLAB_FLAVOR = [
    "the pack fans out through birch and stone; scent thick, voices low.",
    "you move as one line through the timber, flankers holding the wind.",
    "A coordinated drive; no lone wolf's gamble, but the den's work.",
    "Calls and tail signals; the quarry has nowhere left to run.",
]

COLLAB_SUCCESS_FLAVOR = [
    "the kill is shared work; meat and marrow for every jaw that held the line.",
    "flankers, chasers, and the leader's bite; the forest yields to the pack.",
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
    vitals = full_activity_block(user, day, action="hunt")
    if vitals:
        return vitals
    if not can_hunt_again(user, day):
        return "you've used your hunt(s) this sunrise."
    if db.wolf_in_open_collab_hunt(user["id"]):
        return "this wolf is already in an open pack hunt."
    return None


def validate_start_collab_hunt(user, *, guild_id: int, day: int) -> str | None:
    if not db.row_val(user, "pack_id"):
        return "join a great pack first; pack hunts are den business."
    reason = _hunt_block_reason(user, day)
    if reason:
        return reason
    if db.get_open_collab_hunt_by_leader(user["id"]):
        return "you already called a pack hunt. set out or cancel it first."
    return None


def validate_join_collab_hunt(user, hunt, day: int) -> str | None:
    if hunt["status"] != "open":
        return "this pack hunt is no longer open."
    if user["pack_id"] != hunt["pack_id"]:
        from engine.pack_relations import can_join_friendly_pack_hunt

        ok, _note = can_join_friendly_pack_hunt(user, hunt, guild_id=int(hunt["guild_id"]))
        if not ok:
            return "only wolves in the same great pack can join (or **≥8** standing for allied hunts)."
    members = db.get_collab_hunt_members(hunt["id"])
    if any(m["wolf_id"] == user["id"] for m in members):
        return "this wolf is already on the hunt."
    if len(members) >= COLLAB_HUNT_MAX_WOLVES:
        return f"the hunting party is full ({COLLAB_HUNT_MAX_WOLVES} wolves max)."
    return _hunt_block_reason(user, day)


def wolves_eligible_to_join(discord_id: int, hunt_id: int, day: int) -> list:
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt:
        return []
    member_ids = {m["wolf_id"] for m in db.get_collab_hunt_members(hunt_id)}
    eligible = []
    for wolf in db.list_user_wolves(discord_id):
        if wolf["id"] in member_ids:
            continue
        if validate_join_collab_hunt(wolf, hunt, day):
            continue
        eligible.append(wolf)
    return eligible


def build_collab_hunt_embed(hunt_id: int) -> discord.Embed:
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt:
        return howlbert_embed("pack hunt", "hunt not found.", color=ERROR_COLOR)
    members = db.get_collab_hunt_members(hunt_id)
    leader = db.get_user_by_id(hunt["leader_wolf_id"])
    leader_name = leader["wolf_name"] if leader else "Unknown"
    pack = db.get_pack(hunt["pack_id"])
    pack_name = pack["name"] if pack else "the den"

    if hunt["status"] == "open":
        title = "pack hunt called"
        desc = (
            f"**{leader_name}** calls the pack to hunt for **{pack_name}**.\n"
            f"{random.choice(COLLAB_FLAVOR)}\n\n"
            f"**party** ({len(members)}/{COLLAB_HUNT_MAX_WOLVES}); need at least "
            f"**{COLLAB_HUNT_MIN_WOLVES}** to set out.\n"
            f"each wolf spends one hunt this sunrise. "
            f"+**{COLLAB_HUNT_BONUS_PCT_PER_WOLF}%** bones per extra hunter; "
            "assign **leader / chaser / flank / scout / blocker** roles for chemistry.\n"
            f"allied dens at **≥8** standing may join. "
            f"large prey and ambushes can still strike; the party fights together (+1 attack per ally, max +3)."
        )
        color = SUCCESS_COLOR
    elif hunt["status"] == "encounter":
        title = "pack hunt; fight!"
        desc = (
            f"the party (**{_party_names(hunt_id)}**) ran into trouble.\n"
            "Combat is live below; bring it down to finish the hunt."
        )
        color = SUCCESS_COLOR
    elif hunt["status"] == "done":
        title = "pack hunt complete"
        desc = hunt["result_text"] or "the party returned to the den."
        color = SUCCESS_COLOR
    else:
        title = "pack hunt closed"
        desc = "this hunt was cancelled or the den rolled over."
        color = ERROR_COLOR

    embed = howlbert_embed(title, desc, color=color)
    if members:
        lines = []
        for m in members:
            role = m["hunt_role"] if "hunt_role" in m.keys() and m["hunt_role"] else "flank"
            tag = " (caller)" if m["wolf_id"] == hunt["leader_wolf_id"] else ""
            hunter = ""
            w = db.get_user_by_id(m["wolf_id"])
            if w and is_hunter(w):
                hunter = " · Hunter"
            pack_tag = ""
            if w and db.row_val(w, "pack_id") and int(w["pack_id"]) != int(hunt["pack_id"]):
                ally = db.get_pack(int(w["pack_id"]))
                if ally:
                    pack_tag = f" · **{ally['name']}** ally"
            lines.append(f"• **{m['wolf_name']}** · _{role}_{tag}{hunter}{pack_tag}")
        embed.add_field(name="wolves", value="\n".join(lines), inline=False)
    if hunt["status"] == "open":
        chemistry = ""
        if len(members) >= 2:
            from engine.hunt_party import collab_hunt_bond_modifiers

            users = _party_users(hunt_id)
            world = db.get_world(hunt["guild_id"])
            season = world["season"] if world else None
            bond_bonus, bond_note = collab_hunt_bond_modifiers(users, members, season=season)
            if bond_note:
                chemistry = f" · {bond_note.strip('_')}"
            elif bond_bonus:
                chemistry = f" · chemistry **+{bond_bonus}%**"
        embed.set_footer(
            text=(
                f"join with the button · caller sets out when ready · max {COLLAB_HUNT_MAX_WOLVES} wolves"
                f"{chemistry}"
            )
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
        return howlbert_embed("pack hunt", "hunt not found.", color=ERROR_COLOR)
    if hunt["status"] == "done":
        return build_collab_hunt_embed(hunt_id)

    guild_id = hunt["guild_id"]
    world = db.get_world(guild_id)
    day = world["day_number"]
    weather = world["weather"]
    season = world["season"]
    users = _party_users(hunt_id)
    members = db.get_collab_hunt_members(hunt_id)
    leader = db.get_user_by_id(hunt["leader_wolf_id"])

    base, bonus_pct = _compute_collab_base(users, fixed_base=fixed_base)
    from engine.hunt_party import collab_hunt_bond_modifiers

    bond_bonus, bond_note = collab_hunt_bond_modifiers(users, members, season=season)
    if bond_bonus == -100:
        base = 0
        bonus_pct = 0
    elif bond_bonus > 0:
        bonus_pct += bond_bonus
    elif bond_bonus < 0:
        base = max(0, int(base * (100 + bond_bonus) / 100))
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
        from config import COLLAB_RP_MOOD_BONUS

        if db.collab_hunt_member_rp_said(hunt_id, user["id"]):
            db.adjust_mood(user["id"], COLLAB_RP_MOOD_BONUS)
        total_payout += payout

        parts = [f"**{user['wolf_name']}** {format_bones(net, signed=True)}"]
        if tax:
            parts.append(f"tax {format_bones(tax)}")
        if sniff_bonus:
            parts.append(f"sniff +{sniff_bonus}")
        if lucky_bonus:
            parts.append(f"lucky +{lucky_bonus}")
        fresh = db.get_user(user["discord_id"])
        from engine.activity_exhaustion import apply_activity_fatigue
        from engine.role_privileges import hunts_used_today

        fatigue = apply_activity_fatigue(
            fresh, "hunt", "hunting", day, activity_count=hunts_used_today(fresh, day)
        )
        if fatigue:
            parts.append(fatigue.replace("**", ""))
        lines.append(" · ".join(parts))
        if payout > 0:
            award_blooding_on_hunt(user)

    db.adjust_pack_unity(hunt["pack_id"], 1)

    prey_key = prey_key_for_payout(total_payout, user=leader, season=season) if total_payout > 0 else None
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
    if bond_note:
        flavor = bond_note + "\n\n" + flavor

    bonus_note = f"+{bonus_pct}% pack bonus"
    if users and all(is_hunter(u) for u in users):
        bonus_note += " (all hunters)"

    result_text = (
        f"{flavor}\n\n"
        + "\n".join(lines)
        + f"\n\n**{bonus_note}** · pack unity **+1**"
    )
    if prey_name and leader:
        result_text += (
            f"\n**{prey_name}** in the caller's hoard (`/food`) — "
            f"use `/preypile` to lay fresh-kill out for the den."
        )

    db.set_collab_hunt_status(hunt_id, "done", result_text=result_text)
    embed = build_collab_hunt_embed(hunt_id)
    if leader:
        leader = db.get_user_by_id(hunt["leader_wolf_id"])
        footer = f"{hunts_left_footer(leader, day)} for the caller"
        from engine.nursing import is_nursing_mother

        if is_nursing_mother(leader):
            footer += " · Nursing dam: eat extra from `/food`; lactation drains hunger each sunrise"
        embed.set_footer(text=footer)
    return embed


def resolve_collab_hunt(hunt_id: int) -> tuple[discord.Embed | None, str | None]:
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt or hunt["status"] != "open":
        return None, "this pack hunt is not open."
    members = db.get_collab_hunt_members(hunt_id)
    if len(members) < COLLAB_HUNT_MIN_WOLVES:
        return None, f"need at least **{COLLAB_HUNT_MIN_WOLVES}** wolves to set out."
    users = _party_users(hunt_id)
    if len(users) < COLLAB_HUNT_MIN_WOLVES:
        return None, "not enough valid wolves on the hunt."

    world = db.get_world(hunt["guild_id"])
    _record_all_hunt_uses(users, world["day_number"])
    embed = payout_collab_hunt(hunt_id)
    return embed, None


def try_set_out_collab_hunt(hunt_id: int) -> tuple[discord.Embed | None, str | None, int | None]:
    """Set out; may start combat (returns enc_id) or resolve immediately."""
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt or hunt["status"] != "open":
        return None, "this pack hunt is not open.", None
    members = db.get_collab_hunt_members(hunt_id)
    if len(members) < COLLAB_HUNT_MIN_WOLVES:
        return None, f"need at least **{COLLAB_HUNT_MIN_WOLVES}** wolves to set out.", None

    users = _party_users(hunt_id)
    leader = db.get_user_by_id(hunt["leader_wolf_id"])
    if not leader or len(users) < COLLAB_HUNT_MIN_WOLVES:
        return None, "not enough valid wolves on the hunt.", None

    guild_id = hunt["guild_id"]
    channel_id = hunt["channel_id"]
    world = db.get_world(guild_id)
    day = world["day_number"]
    party_note = f"pack hunt: {_party_names(hunt_id)}"

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
        embed = howlbert_embed("large prey!", flavor, color=SUCCESS_COLOR)
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
        embed = ambush_embed(template_key, flavor, leader, activity="hunt")
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
        encounter_note="the pack brought down **large prey** together.",
    )
    db.mark_hunt_prey_rewarded(enc_id)
    db.end_encounter(enc_id)

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
        encounter_note="the pack drove off the ambush and claimed what was left behind.",
    )
    db.end_encounter(enc_id)
    return embed
