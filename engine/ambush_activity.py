"""Finalize hunt/explore ambushes; consume activity on win, refund on flee/loss."""

from __future__ import annotations

import random

import database as db
from engine.role_privileges import hunts_remaining_today, is_hunter, record_hunt_use
from utils.currency import format_bones
from utils.embeds import SUCCESS_COLOR, howlbert_embed
from utils.hunting import award_bones

AMBUSH_WIN_BONES = (6, 14)


def _enc_activity(enc) -> str:
    if not enc:
        return ""
    return str(enc["ambush_activity"] if "ambush_activity" in enc.keys() else "" or "").strip()


def _ambush_won(enc_id: int) -> bool:
    fighters = db.get_combat_fighters(enc_id)
    hunter_alive = False
    npc_alive = False
    for f in fighters:
        if f["npc_name"]:
            if f["hp"] > 0:
                npc_alive = True
        elif f["discord_id"] or f["wolf_id"]:
            if f["hp"] > 0:
                hunter_alive = True
    return hunter_alive and not npc_alive


def _hunter_user(enc):
    hunter_discord_id = enc["hunter_discord_id"] if "hunter_discord_id" in enc.keys() else None
    hunter_wolf_id = enc["hunter_wolf_id"] if "hunter_wolf_id" in enc.keys() else None
    user = db.get_user_by_id(hunter_wolf_id) if hunter_wolf_id else None
    if not user and hunter_discord_id:
        user = db.get_user(hunter_discord_id)
    return user


def _is_finalized(enc) -> bool:
    return bool(enc["ambush_finalized"] if "ambush_finalized" in enc.keys() else False)


def _is_hunt_prey_enc(enc) -> bool:
    return bool(enc and enc["is_hunt_prey"] if "is_hunt_prey" in enc.keys() else False)


def finalize_ambush_activity(encounter_id: int, *, won: bool | None = None) -> None:
    """Idempotent: on win consume hunt/explore; on loss/yield leave slots open."""
    enc = db.get_encounter(encounter_id)
    activity = _enc_activity(enc)
    collab_hunt_id = int(enc["collab_hunt_id"]) if enc and "collab_hunt_id" in enc.keys() and enc["collab_hunt_id"] else 0
    collab_patrol_id = int(enc["collab_patrol_id"]) if enc and "collab_patrol_id" in enc.keys() and enc["collab_patrol_id"] else 0
    if collab_hunt_id or collab_patrol_id:
        activity = activity or ("collab_hunt" if collab_hunt_id else "collab_patrol")
    if not enc or not activity:
        return
    if _is_finalized(enc):
        return

    if won is None:
        won = _ambush_won(encounter_id)

    with db.get_db() as conn:
        conn.execute(
            "UPDATE combat_encounters SET ambush_finalized = 1 WHERE id = ?",
            (encounter_id,),
        )

    if collab_hunt_id:
        if _is_hunt_prey_enc(enc):
            rewarded = bool(enc["hunt_prey_rewarded"] if "hunt_prey_rewarded" in enc.keys() else False)
            if not won and not rewarded:
                hunt = db.get_collab_hunt(collab_hunt_id)
                if hunt and hunt["status"] == "encounter":
                    db.set_collab_hunt_status(
                        collab_hunt_id,
                        "done",
                        result_text=(
                            "The pack hunt ended without a haul; large prey escaped or the caller fell. "
                            "Hunts were spent."
                        ),
                    )
            return
        if not won:
            hunt = db.get_collab_hunt(collab_hunt_id)
            if hunt and hunt["status"] == "encounter":
                db.set_collab_hunt_status(
                    collab_hunt_id,
                    "cancelled",
                    result_text="The pack hunt broke off; ambush unresolved. Hunt slots were not spent.",
                )
            return
        from engine.collab_hunt import complete_collab_hunt_ambush

        complete_collab_hunt_ambush(collab_hunt_id, encounter_id)
        return

    if collab_patrol_id:
        if not won:
            patrol = db.get_collab_patrol(collab_patrol_id)
            if patrol and patrol["status"] == "encounter":
                trail = (
                    "patrol_kind" in patrol.keys() and patrol["patrol_kind"] == "trail"
                )
                slot = "trail" if trail else "survey"
                label = "trail" if trail else "patrol"
                db.set_collab_patrol_status(
                    collab_patrol_id,
                    "cancelled",
                    result_text=(
                        f"The pack {label} broke off; ambush unresolved. "
                        f"{slot.capitalize()} slots were not spent."
                    ),
                )
            return
        from engine.collab_patrol import complete_collab_patrol_ambush

        complete_collab_patrol_ambush(collab_patrol_id, encounter_id)
        return

    user = _hunter_user(enc)
    if not user or not won:
        return

    world = db.get_world(enc["guild_id"])
    day = world["day_number"]

    if activity == "hunt":
        record_hunt_use(user["discord_id"], wolf_id=user["id"], day=day)
    elif activity == "explore":
        db.update_user(user["discord_id"], wolf_id=user["id"], last_explore_day=day)


def ambush_victory_embed(encounter_id: int):
    """Embed when the hunter downs an ambush NPC."""
    enc = db.get_encounter(encounter_id)
    activity = _enc_activity(enc)
    collab_hunt_id = int(enc["collab_hunt_id"]) if enc and "collab_hunt_id" in enc.keys() and enc["collab_hunt_id"] else 0
    collab_patrol_id = int(enc["collab_patrol_id"]) if enc and "collab_patrol_id" in enc.keys() and enc["collab_patrol_id"] else 0
    if not enc or not _ambush_won(encounter_id) or _is_finalized(enc):
        if collab_hunt_id or collab_patrol_id:
            pass
        else:
            return None
    elif not activity:
        if not collab_hunt_id and not collab_patrol_id:
            return None

    if collab_hunt_id and _ambush_won(encounter_id) and not _is_finalized(enc):
        from engine.collab_hunt import complete_collab_hunt_ambush

        embed = complete_collab_hunt_ambush(collab_hunt_id, encounter_id)
        if embed:
            embed.set_footer(text="Pack hunt complete; each wolf spent one hunt this sunrise.")
        return embed

    if collab_patrol_id and _ambush_won(encounter_id) and not _is_finalized(enc):
        from engine.collab_patrol import complete_collab_patrol_ambush

        patrol = db.get_collab_patrol(collab_patrol_id)
        trail = (
            patrol
            and "patrol_kind" in patrol.keys()
            and patrol["patrol_kind"] == "trail"
        )
        embed = complete_collab_patrol_ambush(collab_patrol_id, encounter_id)
        if embed:
            slot = "trail" if trail else "survey"
            embed.set_footer(
                text=f"Pack {'trail' if trail else 'patrol'} complete; each scout spent their {slot} this sunrise."
            )
        return embed

    if not activity or not _ambush_won(encounter_id) or _is_finalized(enc):
        return None

    user = _hunter_user(enc)
    if not user:
        return None

    world = db.get_world(enc["guild_id"])
    gross = random.randint(*AMBUSH_WIN_BONES)
    net, tax, _, _, *_ = award_bones(
        user, gross, world["weather"], "hunt", season=world["season"]
    )
    finalize_ambush_activity(encounter_id, won=True)
    db.end_encounter(encounter_id)

    if activity == "hunt":
        title = "Threat Driven Off"
        body = (
            "You survive the ambush and claim a small trove from what the attacker left behind.\n"
            f"**{format_bones(net, signed=True)}**"
        )
        if tax > 0:
            body += f" · pack tax **{format_bones(tax)}**"
        body += " · your hunt for this sunrise is spent."
        if is_hunter(user):
            left = hunts_remaining_today(user, world["day_number"])
            footer = (
                f"Hunter; **{left}** hunt(s) left this sunrise."
                if left > 0
                else "Hunter; no hunts left this sunrise."
            )
        else:
            footer = "You can hunt again tomorrow."
    else:
        title = "Ambush Survived"
        body = (
            "You drive off the attacker and catch your breath.\n"
            f"**{format_bones(net, signed=True)}** · your explore for this sunrise is done."
        )
        if tax > 0:
            body += f" Pack tax: **{format_bones(tax)}**."
        footer = "Scouts may still range out again today."

    embed = howlbert_embed(title, body, color=SUCCESS_COLOR)
    embed.set_footer(text=footer)
    return embed
