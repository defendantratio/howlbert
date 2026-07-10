"""Treasury raid fallout: rival memory, audit, accusation, and pack-specific odds."""

from __future__ import annotations

import random

import discord

import database as db
from config import (
    CROSS_PACK_STEAL_CATCH_CHANCE,
    GREAT_PACKS,
    RAID_ACCUSE_RECOVER_PCT,
    RAID_ALERT_SUNRISES,
    RAID_AUDIT_RECOVER_PCT,
    RAID_PACK_MODIFIERS,
    RAID_SNIFF_ENCOUNTER_BONUS,
    RAID_SURVEY_DC_RAIDER,
    RAID_SURVEY_DC_VICTIM,
    RAID_SURVEY_VICTIM_BONE_BONUS,
)
from engine.dice import format_roll_result, resolve_check
from engine.role_privileges import is_guard
from utils.currency import format_bones
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed


def steal_catch_chance(target_pack_key: str) -> float:
    mod = RAID_PACK_MODIFIERS.get(target_pack_key, {})
    bonus = float(mod.get("catch_bonus", 0))
    return min(0.95, max(0.05, CROSS_PACK_STEAL_CATCH_CHANCE + bonus))


def roll_steal_caught(target_pack_key: str) -> bool:
    return random.random() < steal_catch_chance(target_pack_key)


def scaled_steal_attempt(target_pack_key: str, base_amount: int) -> int:
    mod = RAID_PACK_MODIFIERS.get(target_pack_key, {})
    mult = float(mod.get("steal_mult", 1.0))
    return max(1, int(base_amount * mult))


def record_treasury_raid(
    guild_id: int,
    *,
    victim_pack_id: int,
    raider_pack_id: int,
    stolen_amount: int,
    day: int,
    caught: bool,
) -> int:
    return db.record_pack_raid_alert(
        guild_id,
        victim_pack_id=victim_pack_id,
        suspect_pack_id=raider_pack_id,
        stolen_amount=stolen_amount,
        raid_day=day,
        expires_day=day + RAID_ALERT_SUNRISES,
        caught=caught,
    )


def sniff_encounter_chance_bonus(
    guild_id: int, user_pack_id: int | None, other_pack_id: int | None, day: int
) -> float:
    if not guild_id or not user_pack_id or not other_pack_id:
        return 0.0
    if db.raid_watch_active(guild_id, user_pack_id, other_pack_id, day):
        return RAID_SNIFF_ENCOUNTER_BONUS
    return 0.0


def survey_dc_modifiers(user, guild_id: int, day: int) -> tuple[int, str]:
    """extra dc and footnote for scout survey when raid alerts are active."""
    pack_id = user["pack_id"] if "pack_id" in user.keys() else None
    if not pack_id or not guild_id:
        return 0, ""
    alert = db.get_active_raid_alert_for_victim(guild_id, pack_id, day)
    if not alert:
        return 0, ""
    suspect = int(alert["suspect_pack_id"])
    if pack_id == int(alert["victim_pack_id"]):
        return RAID_SURVEY_DC_VICTIM, "treasury alert; borders easier to read."
    if pack_id == suspect:
        return RAID_SURVEY_DC_RAIDER, "rival den is watchful; harder to ghost the ridge."
    return 0, ""


def survey_victim_bone_bonus(user, guild_id: int, day: int) -> int:
    pack_id = user["pack_id"] if "pack_id" in user.keys() else None
    if not pack_id or not guild_id:
        return 0
    alert = db.get_active_raid_alert_for_victim(guild_id, pack_id, day)
    if alert and int(alert["victim_pack_id"]) == pack_id:
        return RAID_SURVEY_VICTIM_BONE_BONUS
    return 0


def collect_raid_den_news(guild_id: int, day: int) -> list[str]:
    lines: list[str] = []
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT a.*, vp.name AS victim_name, sp.name AS suspect_name
            FROM pack_raid_alerts a
            JOIN packs vp ON vp.id = a.victim_pack_id
            JOIN packs sp ON sp.id = a.suspect_pack_id
            WHERE a.guild_id = ? AND a.raid_day = ?
            """,
            (guild_id, day),
        ).fetchall()
    for row in rows:
        stolen = int(row["stolen_amount"])
        if stolen <= 0 and not int(row["caught"]):
            continue
        victim = row["victim_name"]
        if int(row["caught"]):
            lines.append(
                f"**{victim}** treasury hit; **{row['suspect_name']}** caught at the border. "
                f"**`/pack audit`** or **`/pack accuse`** can claw back bones."
            )
        else:
            lines.append(
                f"**{victim}** den reserves down (worth **{format_bones(stolen)}**); sentries doubled. "
                f"scouts: **`/scout survey`** (easier dc) · alpha: **`/pack audit`**."
            )
    return lines


def try_treasury_audit(interaction: discord.Interaction, user, pack, day: int) -> discord.Embed:
    from engine.pack_leadership import is_pack_alpha, is_pack_beta

    if not (is_guard(user) or is_pack_alpha(user, pack) or is_pack_beta(user, pack)):
        return howlbert_embed(
            "not authorized",
            "only **guards**, **alpha**, or **beta (advisor)** can audit the treasury pit.",
            color=ERROR_COLOR,
        )
    guild_id = interaction.guild.id
    alert = db.get_active_raid_alert_for_victim(guild_id, pack["id"], day)
    if not alert:
        return howlbert_embed(
            "no alert",
            "no active treasury theft on file. audits only run while a raid alert is open.",
            color=ERROR_COLOR,
        )
    if int(alert["last_audit_day"]) >= day:
        return howlbert_embed(
            "already audited",
            "this sunrise's audit is done. try again after the next sunrise.",
            color=ERROR_COLOR,
        )

    from engine.character import parse_proficiencies

    profs = parse_proficiencies(user["skill_proficiencies"])
    dc = 11 + RAID_SURVEY_DC_VICTIM
    result = resolve_check(
        user,
        attr_keys=("attr_wis", "attr_dex"),
        skill="Stealth",
        dc=dc,
        proficient="stealth" in profs or "tracking" in profs,
        skill_key="stealth",
        game_day=day,
    )
    db.set_raid_alert_audit_day(int(alert["id"]), day)
    if not result["success"]:
        return howlbert_embed(
            "audit failed",
            format_roll_result(result)
            + "\n\ntracks are too churned; the thief's scent fades.",
            color=ERROR_COLOR,
        )

    remaining = int(alert["stolen_amount"]) - int(alert["recovered_amount"])
    recover = max(1, int(remaining * RAID_AUDIT_RECOVER_PCT))
    got = db.recover_raid_alert_bones(int(alert["id"]), recover, pack["id"])
    embed = howlbert_embed(
        "treasury audit",
        format_roll_result(result)
        + f"\n\nrecovered **{format_bones(got)}** into **{pack['name']}** treasury.",
        color=SUCCESS_COLOR,
    )
    embed.add_field(name="treasury", value=format_bones(db.get_pack(pack["id"])["treasury"]), inline=True)
    return embed


def try_raid_accuse(
    interaction: discord.Interaction,
    user,
    pack,
    target_pack_key: str,
    day: int,
) -> discord.Embed:
    from engine.pack_leadership import is_pack_alpha, is_pack_beta

    if not (is_pack_alpha(user, pack) or is_pack_beta(user, pack)):
        return howlbert_embed(
            "not authorized",
            "only **alpha** or **beta (advisor)** can accuse a rival den.",
            color=ERROR_COLOR,
        )
    if target_pack_key not in GREAT_PACKS:
        return howlbert_embed("unknown pack", "pick a great pack key.", color=ERROR_COLOR)

    guild_id = interaction.guild.id
    alert = db.get_active_raid_alert_for_victim(guild_id, pack["id"], day)
    if not alert:
        return howlbert_embed(
            "no alert",
            "no treasury theft to investigate.",
            color=ERROR_COLOR,
        )
    accused = db.get_pack_by_key(target_pack_key)
    if not accused:
        return howlbert_embed("pack not found", "that den isn't registered here.", color=ERROR_COLOR)

    from engine.energy import spend_energy

    _new_energy, _had_energy, accuse_penalty = spend_energy(user, "accuse")

    db.set_raid_alert_accused(int(alert["id"]), accused["id"], day)

    suspect_id = int(alert["suspect_pack_id"])
    victim_name = pack["name"]
    accused_name = GREAT_PACKS[target_pack_key]["name"]
    lines: list[str] = [f"**{victim_name}** names **{accused_name}** for the treasury raid."]

    if int(accused["id"]) == suspect_id:
        remaining = max(0, int(alert["stolen_amount"]) - int(alert["recovered_amount"]))
        claw = int(remaining * RAID_ACCUSE_RECOVER_PCT) if remaining > 0 else 0
        got = db.clawback_raid_from_pack_treasury(suspect_id, claw, pack["id"], int(alert["id"])) if claw > 0 else 0
        new_rel = db.adjust_pack_relation(guild_id, pack["id"], suspect_id, -2)
        claw_note = f"clawed back **{format_bones(got)}**" if got > 0 else "nothing left to claw back"
        lines.append(
            f"**correct.** {claw_note} from **{accused_name}** treasury."
        )
        lines.append(f"pack standing with **{accused_name}** **−2** (now **{new_rel}/10**).")
        color = SUCCESS_COLOR
    else:
        wrong_rel = db.adjust_pack_relation(guild_id, pack["id"], accused["id"], -1)
        db.adjust_wolf_standing(interaction.user.id, -1)
        lines.append(
            f"**wrong den.** **{accused_name}** pushes back; your standing **−1**."
        )
        lines.append(f"pack standing with **{accused_name}** **−1** (now **{wrong_rel}/10**).")
        color = ERROR_COLOR

    if accuse_penalty:
        lines.append(f"_{accuse_penalty}_")
    return howlbert_embed("raid accusation", "\n".join(lines), color=color)
