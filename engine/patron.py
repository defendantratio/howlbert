"""Invite and server-boost rewards; booster perks are personal only."""

from __future__ import annotations

import datetime

import database as db
from config import (
    BOOST_DAILY_BONUS,
    BOOST_FIRST_BONES,
    BOOST_FIRST_MOOD,
    BOOST_FIRST_STANDING,
    BOOST_SECOND_BONES,
    INVITE_MAX_PAYOUTS_PER_MONTH,
    INVITE_REFERRAL_ROLLOVERS,
    INVITE_REFERRER_BONES,
    INVITE_REFERRER_STANDING,
    INVITE_REGISTER_WINDOW_DAYS,
    INVITE_WELCOME_BONES,
)


def _month_key() -> str:
    return datetime.date.today().strftime("%y-%m")


def _invite_payouts_this_month(discord_id: int) -> int:
    account = db.get_account(discord_id)
    if not account:
        return 0
    month = account["invite_reward_month"] if "invite_reward_month" in account.keys() else ""
    count = int(account["invite_reward_count"]) if "invite_reward_count" in account.keys() else 0
    if month != _month_key():
        return 0
    return count


def _increment_invite_payout(discord_id: int) -> None:
    month = _month_key()
    with db.get_db() as conn:
        row = conn.execute(
            "SELECT invite_reward_month, invite_reward_count FROM account_progress WHERE discord_id = ?",
            (discord_id,),
        ).fetchone()
        if not row:
            conn.execute(
                "INSERT INTO account_progress (discord_id, invite_reward_month, invite_reward_count) VALUES (?, ?, 1)",
                (discord_id, month),
            )
            return
        count = 1
        if row["invite_reward_month"] == month:
            count = int(row["invite_reward_count"]) + 1
        conn.execute(
            """
            UPDATE account_progress
            SET invite_reward_month = ?, invite_reward_count = ?
            WHERE discord_id = ?
            """,
            (month, count, discord_id),
        )


def record_invite_join(guild_id: int, invitee_id: int, inviter_id: int, day: int) -> None:
    if invitee_id == inviter_id:
        return
    with db.get_db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO invite_referrals
            (guild_id, invitee_discord_id, inviter_discord_id, join_day)
            VALUES (?, ?, ?, ?)
            """,
            (guild_id, invitee_id, inviter_id, day),
        )


def on_wolf_registered(
    discord_id: int,
    guild_id: int,
    *,
    first_wolf: bool,
) -> str | None:
    """Welcome bones for invited new players. Returns a note for the register embed."""
    if not first_wolf:
        return None

    with db.get_db() as conn:
        row = conn.execute(
            """
            SELECT * FROM invite_referrals
            WHERE guild_id = ? AND invitee_discord_id = ?
            """,
            (guild_id, discord_id),
        ).fetchone()
        if not row or row["welcome_granted"]:
            return None

        world = conn.execute(
            "SELECT day_number FROM world_state WHERE guild_id = ?", (guild_id,)
        ).fetchone()
        day = int(world["day_number"]) if world else row["join_day"]
        if day - int(row["join_day"]) > INVITE_REGISTER_WINDOW_DAYS:
            return None

        conn.execute(
            """
            UPDATE invite_referrals
            SET registered_day = ?, welcome_granted = 1
            WHERE guild_id = ? AND invitee_discord_id = ?
            """,
            (day, guild_id, discord_id),
        )

    db.add_bones(discord_id, INVITE_WELCOME_BONES)
    return (
        f"**invite welcome**; **+{INVITE_WELCOME_BONES}** bones for joining the den "
        f"(invited by <@{row['inviter_discord_id']}>)."
    )


def process_invite_rollovers(guild_id: int, day: int) -> list[str]:
    """After sunrise; count referral rollovers and pay inviters."""
    notes: list[str] = []
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM invite_referrals
            WHERE guild_id = ?
              AND registered_day IS NOT NULL
              AND referrer_granted = 0
            """,
            (guild_id,),
        ).fetchall()

        for row in rows:
            reg_day = int(row["registered_day"])
            if day <= reg_day:
                continue
            new_count = int(row["rollovers_after_register"]) + 1
            conn.execute(
                """
                UPDATE invite_referrals
                SET rollovers_after_register = ?
                WHERE guild_id = ? AND invitee_discord_id = ?
                """,
                (new_count, guild_id, row["invitee_discord_id"]),
            )
            if new_count < INVITE_REFERRAL_ROLLOVERS:
                continue

            inviter_id = int(row["inviter_discord_id"])
            if _invite_payouts_this_month(inviter_id) >= INVITE_MAX_PAYOUTS_PER_MONTH:
                continue
            inviter_wolf = conn.execute(
                "SELECT id FROM users WHERE discord_id = ? LIMIT 1", (inviter_id,)
            ).fetchone()
            if not inviter_wolf:
                continue

            conn.execute(
                """
                UPDATE invite_referrals SET referrer_granted = 1
                WHERE guild_id = ? AND invitee_discord_id = ?
                """,
                (guild_id, row["invitee_discord_id"]),
            )
            conn.execute(
                "UPDATE users SET bones = bones + ? WHERE discord_id = ?",
                (INVITE_REFERRER_BONES, inviter_id),
            )
            conn.execute(
                "UPDATE users SET standing = standing + ? WHERE discord_id = ?",
                (INVITE_REFERRER_STANDING, inviter_id),
            )

            _increment_invite_payout(inviter_id)
            notes.append(
                f"<@{inviter_id}> earned **{INVITE_REFERRER_BONES}** bones + "
                f"**{INVITE_REFERRER_STANDING}** standing; "
                f"<@{row['invitee_discord_id']}> stayed **{INVITE_REFERRAL_ROLLOVERS}** sunrises."
            )

    return notes


def grant_first_boost(discord_id: int) -> str | None:
    account = db.get_account(discord_id)
    if not account or int(account["boost_first_claimed"]):
        return None
    if not db.get_user(discord_id):
        return None

    user = db.get_user(discord_id)
    with db.get_db() as conn:
        conn.execute(
            "UPDATE account_progress SET boost_first_claimed = 1 WHERE discord_id = ?",
            (discord_id,),
        )
    db.add_bones(discord_id, BOOST_FIRST_BONES, wolf_id=user["id"])
    db.adjust_wolf_standing(discord_id, BOOST_FIRST_STANDING)
    db.adjust_mood(user["id"], BOOST_FIRST_MOOD)
    return (
        f"**den patron**; first boost: **+{BOOST_FIRST_BONES}** bones, "
        f"**+{BOOST_FIRST_STANDING}** standing, **+{BOOST_FIRST_MOOD}** mood. "
        f"while you boost: **+{BOOST_DAILY_BONUS}** bones on `/bones action:daily`."
    )


def grant_second_boost(discord_id: int) -> str | None:
    account = db.get_account(discord_id)
    if not account or int(account["boost_second_claimed"]):
        return None
    if not db.get_user(discord_id):
        return None

    user = db.get_user(discord_id)
    with db.get_db() as conn:
        conn.execute(
            "UPDATE account_progress SET boost_second_claimed = 1 WHERE discord_id = ?",
            (discord_id,),
        )
    db.add_bones(discord_id, BOOST_SECOND_BONES, wolf_id=user["id"])
    return f"**den patron**; second boost slot: **+{BOOST_SECOND_BONES}** bones."


def booster_daily_bonus() -> int:
    return BOOST_DAILY_BONUS


def patron_status_lines(discord_id: int, *, is_boosting: bool) -> list[str]:
    account = db.get_account(discord_id)
    lines: list[str] = []
    if account:
        first = bool(int(account["boost_first_claimed"]))
        second = bool(int(account["boost_second_claimed"]))
        lines.append("**server boost (you only)**")
        lines.append(f"• first boost claimed: **{'yes' if first else 'no'}**")
        lines.append(f"• second slot claimed: **{'yes' if second else 'no'}**")
        if is_boosting:
            lines.append(f"• active booster: **+{BOOST_DAILY_BONUS}** bones on `/bones action:daily`")
        else:
            lines.append("• not currently boosting; daily bonus inactive")
    payouts = _invite_payouts_this_month(discord_id)
    lines.append(
        f"**invites**; **{payouts}/{INVITE_MAX_PAYOUTS_PER_MONTH}** referrer payouts this month"
    )
    lines.append(
        f"invitee welcome: **{INVITE_WELCOME_BONES}** bones · "
        f"referrer (after {INVITE_REFERRAL_ROLLOVERS} sunrises): "
        f"**{INVITE_REFERRER_BONES}** bones + **{INVITE_REFERRER_STANDING}** standing"
    )
    from engine.kickstarter import kickstarter_status_lines

    ks_lines = kickstarter_status_lines(discord_id)
    if ks_lines:
        lines.extend(ks_lines)
    return lines
