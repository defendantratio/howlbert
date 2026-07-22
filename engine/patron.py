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
    REFERRAL_MILESTONE_BONES,
    REFERRAL_MILESTONES,
)


def _month_key() -> str:
    return datetime.date.today().strftime("%y-%m")


def _invite_payouts_this_month(discord_id: int, conn=None) -> int:
    def _run(c):
        return c.execute(
            "SELECT invite_reward_month, invite_reward_count FROM account_progress WHERE discord_id = ?",
            (discord_id,),
        ).fetchone()

    row = _run(conn) if conn is not None else None
    if row is None and conn is None:
        with db.get_db() as c:
            row = _run(c)
    if not row:
        return 0
    month = row["invite_reward_month"] or ""
    count = int(row["invite_reward_count"] or 0)
    if month != _month_key():
        return 0
    return count


def _increment_invite_payout(discord_id: int, conn=None) -> None:
    month = _month_key()

    def _run(c) -> None:
        row = c.execute(
            "SELECT invite_reward_month, invite_reward_count FROM account_progress WHERE discord_id = ?",
            (discord_id,),
        ).fetchone()
        if not row:
            c.execute(
                "INSERT INTO account_progress (discord_id, invite_reward_month, invite_reward_count) VALUES (?, ?, 1)",
                (discord_id, month),
            )
            return
        count = 1
        if row["invite_reward_month"] == month:
            count = int(row["invite_reward_count"]) + 1
        c.execute(
            """
            UPDATE account_progress
            SET invite_reward_month = ?, invite_reward_count = ?
            WHERE discord_id = ?
            """,
            (month, count, discord_id),
        )

    if conn is not None:
        _run(conn)
    else:
        with db.get_db() as c:
            _run(c)


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


def _check_referral_milestone(discord_id: int, conn=None) -> str | None:
    """Uncapped, cosmetic-only title track for lifetime successful referrals;
    separate from the monthly bones/standing cap above. Returns a note the
    first time a new threshold is crossed, else None."""
    count = db.count_successful_referrals(discord_id, conn=conn)
    current = db.get_referral_milestone(discord_id, conn=conn)
    newly_earned = [n for n in sorted(REFERRAL_MILESTONES) if current < n <= count]
    if not newly_earned:
        return None
    highest = newly_earned[-1]
    db.set_referral_milestone(discord_id, highest, conn=conn)
    title = REFERRAL_MILESTONES[highest]
    # one-time grant for every threshold crossed at once (a big jump can clear
    # more than one); paid on top of the monthly per-referral cap by design.
    bonus = sum(REFERRAL_MILESTONE_BONES.get(n, 0) for n in newly_earned)
    if bonus > 0:
        conn.execute(
            "UPDATE users SET bones = bones + ? WHERE discord_id = ?",
            (bonus, discord_id),
        )
        return (
            f"<@{discord_id}> reached **{count}** lifetime referrals; new title unlocked: "
            f"**{title}** (**+{bonus}** bones, one-time)."
        )
    return f"<@{discord_id}> reached **{count}** lifetime referrals; new title unlocked: **{title}**."


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
            inviter_wolf = conn.execute(
                "SELECT id FROM users WHERE discord_id = ? LIMIT 1", (inviter_id,)
            ).fetchone()
            if not inviter_wolf:
                continue

            # the referral itself always counts (leaderboard + milestone titles
            # track every successful referral, uncapped); only the bones/standing
            # payout is limited to INVITE_MAX_PAYOUTS_PER_MONTH per inviter.
            conn.execute(
                """
                UPDATE invite_referrals SET referrer_granted = 1
                WHERE guild_id = ? AND invitee_discord_id = ?
                """,
                (guild_id, row["invitee_discord_id"]),
            )

            payout_capped = _invite_payouts_this_month(inviter_id, conn=conn) >= INVITE_MAX_PAYOUTS_PER_MONTH
            if payout_capped:
                note = (
                    f"<@{inviter_id}> brought <@{row['invitee_discord_id']}> home "
                    f"(**{INVITE_REFERRAL_ROLLOVERS}** sunrises); monthly referrer payout "
                    f"already capped at **{INVITE_MAX_PAYOUTS_PER_MONTH}**, but the referral still counts."
                )
            else:
                conn.execute(
                    "UPDATE users SET bones = bones + ? WHERE discord_id = ?",
                    (INVITE_REFERRER_BONES, inviter_id),
                )
                conn.execute(
                    "UPDATE users SET standing = standing + ? WHERE discord_id = ?",
                    (INVITE_REFERRER_STANDING, inviter_id),
                )
                _increment_invite_payout(inviter_id, conn=conn)
                note = (
                    f"<@{inviter_id}> earned **{INVITE_REFERRER_BONES}** bones + "
                    f"**{INVITE_REFERRER_STANDING}** standing; "
                    f"<@{row['invitee_discord_id']}> stayed **{INVITE_REFERRAL_ROLLOVERS}** sunrises."
                )
            notes.append(note)

            milestone_note = _check_referral_milestone(inviter_id, conn=conn)
            if milestone_note:
                notes.append(milestone_note)

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




def referral_title(discord_id: int) -> str | None:
    """Current uncapped referral milestone title, if any has been earned."""
    milestone = db.get_referral_milestone(discord_id)
    return REFERRAL_MILESTONES.get(milestone)


def referral_badge_text(discord_id: int) -> str | None:
    """`/profile` footer badge for the current referral title, if any."""
    title = referral_title(discord_id)
    return f"🐾 {title}" if title else None


def referral_milestone_line(discord_id: int) -> str:
    """`/patron` line: current title (if any) plus how many more referrals to the next one."""
    count = db.count_successful_referrals(discord_id)
    current = db.get_referral_milestone(discord_id)
    title = REFERRAL_MILESTONES.get(current)
    next_threshold = next((n for n in sorted(REFERRAL_MILESTONES) if n > current), None)
    title_bit = f"**{title}**" if title else "none yet"
    line = f"referral title: {title_bit} · **{count}** lifetime referrals"
    if next_threshold:
        remaining = next_threshold - count
        line += f" · **{remaining}** more to **{REFERRAL_MILESTONES[next_threshold]}**"
        next_bonus = REFERRAL_MILESTONE_BONES.get(next_threshold, 0)
        if next_bonus > 0:
            line += f" (**+{next_bonus}** bones)"
    return line


def referral_leaderboard_lines(guild_id: int, *, limit: int = 10) -> list[str]:
    """`who brought the most wolves home` — the visible half of the referral
    loop; the reward itself already exists (record_invite_join/process_invite_rollovers
    above), this just surfaces it so it reads as a flex, not a quiet backend bonus."""
    rows = db.get_referral_leaderboard(guild_id, limit=limit)
    if not rows:
        return ["no referrals have paid out yet; invite a friend and stick around."]
    lines = []
    for i, row in enumerate(rows, start=1):
        count = int(row["referral_count"])
        wolves = "wolf" if count == 1 else "wolves"
        title = referral_title(int(row["inviter_discord_id"]))
        title_bit = f" · **{title}**" if title else ""
        lines.append(f"**{i}.** <@{row['inviter_discord_id']}> — **{count}** {wolves} brought home{title_bit}")
    return lines


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
    lines.append(referral_milestone_line(discord_id))
    from engine.kickstarter import kickstarter_status_lines

    ks_lines = kickstarter_status_lines(discord_id)
    if ks_lines:
        lines.extend(ks_lines)
    return lines
