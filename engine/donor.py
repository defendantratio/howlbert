"""Ko-fi donations and one-time redeem codes; personal rewards only."""

from __future__ import annotations

import datetime
import re
import secrets
import sqlite3

import database as db
from config import (
    DONOR_BONES_PER_DOLLAR,
    DONOR_LEGEND_DAILY_BONUS,
    DONOR_LEGEND_SUPPORTER_DAYS,
    DONOR_MONTHLY_BONE_CAP,
    DONOR_TIERS,
    KOFI_MEMBERSHIP_PERIOD_DAYS,
    KOFI_MEMBERSHIP_PERKS,
    KOFI_TIER_NAME_MATCHES,
)

_DISCORD_ID_RE = re.compile(r"\b(\d{17,20})\b")


def _utcnow_str() -> str:
    """Timezone-aware UTC timestamp, truncated to seconds (datetime.utcnow() is deprecated)."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _today() -> datetime.date:
    return datetime.date.today()


def _month_key() -> str:
    return _today().strftime("%y-%m")


def _iso_date(day: datetime.date) -> str:
    return day.isoformat()


def _parse_date(raw: str) -> datetime.date | None:
    if not raw:
        return None
    try:
        return datetime.date.fromisoformat(raw)
    except ValueError:
        return None


def _acct_int(account: sqlite3.Row | None, key: str, default: int = 0) -> int:
    if not account or key not in account.keys():
        return default
    return int(account[key])


def _acct_str(account: sqlite3.Row | None, key: str, default: str = "") -> str:
    if not account or key not in account.keys():
        return default
    return str(account[key] or default)


def tier_label(tier_key: str) -> str:
    if not tier_key:
        return "-"
    info = DONOR_TIERS.get(tier_key, {})
    return str(info.get("label", tier_key))


def tier_for_total_cents(cents: int) -> str:
    tier = ""
    for key, info in sorted(DONOR_TIERS.items(), key=lambda x: x[1]["min_cents"]):
        if cents >= int(info["min_cents"]):
            tier = key
    return tier


def tier_key_from_kofi_name(tier_name: str | None) -> str:
    if not tier_name:
        return ""
    lower = tier_name.lower()
    for pattern, key in KOFI_TIER_NAME_MATCHES:
        if pattern in lower:
            return key
    return ""


def _tier_rank(key: str) -> int:
    order = {"": 0, "friend": 1, "benefactor": 2, "legend": 3}
    return order.get(key, 0)


def effective_donor_tier(account: sqlite3.Row | None) -> str:
    if not account:
        return ""
    membership = _acct_str(account, "kofi_membership_tier")
    until = _parse_date(_acct_str(account, "kofi_membership_until"))
    if membership and until and until >= _today():
        lifetime = _acct_str(account, "donor_tier")
        if _tier_rank(membership) >= _tier_rank(lifetime):
            return membership
        return lifetime
    return _acct_str(account, "donor_tier")


def _link_kofi_email(conn: sqlite3.Connection, email: str, discord_id: int) -> None:
    normalized = email.strip().lower()
    if not normalized or "@" not in normalized:
        return
    conn.execute(
        """
        INSERT INTO kofi_email_links (email, discord_id, linked_at)
        VALUES (?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            discord_id = excluded.discord_id,
            linked_at = excluded.linked_at
        """,
        (normalized, discord_id, _utcnow_str()),
    )


def _discord_id_from_email(conn: sqlite3.Connection, email: str) -> int | None:
    normalized = email.strip().lower()
    if not normalized:
        return None
    row = conn.execute(
        "SELECT discord_id FROM kofi_email_links WHERE email = ?", (normalized,)
    ).fetchone()
    return int(row["discord_id"]) if row else None


def _extend_membership_until(conn: sqlite3.Connection, discord_id: int, days: int) -> None:
    row = conn.execute(
        "SELECT kofi_membership_until FROM account_progress WHERE discord_id = ?",
        (discord_id,),
    ).fetchone()
    start = _today()
    if row and row["kofi_membership_until"]:
        existing = _parse_date(str(row["kofi_membership_until"]))
        if existing and existing >= start:
            start = existing
    until = start + datetime.timedelta(days=days)
    conn.execute(
        "UPDATE account_progress SET kofi_membership_until = ? WHERE discord_id = ?",
        (_iso_date(until), discord_id),
    )


def parse_discord_id_from_message(message: str) -> int | None:
    if not message:
        return None
    for match in _DISCORD_ID_RE.findall(message):
        try:
            return int(match)
        except ValueError:
            continue
    return None


def donor_daily_bonus(discord_id: int) -> int:
    account = db.get_account(discord_id)
    if not account:
        return 0
    until = _parse_date(_acct_str(account, "donor_supporter_until"))
    if until and until >= _today():
        return DONOR_LEGEND_DAILY_BONUS
    membership = _acct_str(account, "kofi_membership_tier")
    member_until = _parse_date(_acct_str(account, "kofi_membership_until"))
    if membership == "legend" and member_until and member_until >= _today():
        return DONOR_LEGEND_DAILY_BONUS
    return 0


def _bones_remaining_this_month(account: sqlite3.Row | None) -> int:
    month = _acct_str(account, "donor_bones_month")
    used = _acct_int(account, "donor_bones_month_amount")
    if month != _month_key():
        return DONOR_MONTHLY_BONE_CAP
    return max(0, DONOR_MONTHLY_BONE_CAP - used)


def _record_monthly_bones(conn: sqlite3.Connection, discord_id: int, bones: int) -> None:
    month = _month_key()
    row = conn.execute(
        "SELECT donor_bones_month, donor_bones_month_amount FROM account_progress WHERE discord_id = ?",
        (discord_id,),
    ).fetchone()
    if not row:
        conn.execute(
            """
            INSERT INTO account_progress
            (discord_id, donor_bones_month, donor_bones_month_amount)
            VALUES (?, ?, ?)
            """,
            (discord_id, month, bones),
        )
        return
    amount = bones
    if row["donor_bones_month"] == month:
        amount = int(row["donor_bones_month_amount"]) + bones
    conn.execute(
        """
        UPDATE account_progress
        SET donor_bones_month = ?, donor_bones_month_amount = ?
        WHERE discord_id = ?
        """,
        (month, amount, discord_id),
    )


def _extend_supporter_days(conn: sqlite3.Connection, discord_id: int, days: int) -> None:
    if days <= 0:
        return
    row = conn.execute(
        "SELECT donor_supporter_until FROM account_progress WHERE discord_id = ?",
        (discord_id,),
    ).fetchone()
    start = _today()
    if row and row["donor_supporter_until"]:
        existing = _parse_date(str(row["donor_supporter_until"]))
        if existing and existing >= start:
            start = existing
    until = start + datetime.timedelta(days=days)
    conn.execute(
        "UPDATE account_progress SET donor_supporter_until = ? WHERE discord_id = ?",
        (_iso_date(until), discord_id),
    )


def apply_donation_grant(
    discord_id: int,
    *,
    bones: int = 0,
    add_cents: int = 0,
    tier: str = "",
    mood: int = 0,
    standing: int = 0,
    supporter_days: int = 0,
    count_toward_monthly_cap: bool = False,
) -> tuple[bool, str]:
    """Grant donor rewards to a registered wolf owner. Returns (ok, message)."""
    user = db.get_user(discord_id)
    if not user:
        return False, "no registered wolf for that discord account."

    db.get_account(discord_id)
    account = db.get_account(discord_id)
    if count_toward_monthly_cap and bones > 0:
        remaining = _bones_remaining_this_month(account)
        if remaining <= 0:
            bones = 0
        else:
            bones = min(bones, remaining)

    with db.get_db() as conn:
        if add_cents > 0:
            total = _acct_int(account, "donor_total_cents") + add_cents
            new_tier = tier_for_total_cents(total)
            conn.execute(
                """
                UPDATE account_progress
                SET donor_total_cents = ?, donor_tier = ?
                WHERE discord_id = ?
                """,
                (total, new_tier, discord_id),
            )
            if new_tier == "legend" and supporter_days <= 0:
                supporter_days = DONOR_LEGEND_SUPPORTER_DAYS
        elif tier:
            conn.execute(
                "UPDATE account_progress SET donor_tier = ? WHERE discord_id = ?",
                (tier, discord_id),
            )

        if supporter_days > 0:
            _extend_supporter_days(conn, discord_id, supporter_days)

        if count_toward_monthly_cap and bones > 0:
            _record_monthly_bones(conn, discord_id, bones)

    if bones > 0:
        db.add_bones(discord_id, bones, wolf_id=user["id"])
    if mood > 0:
        db.adjust_mood(user["id"], mood)
    if standing > 0:
        db.adjust_wolf_standing(discord_id, standing)

    parts: list[str] = []
    if bones > 0:
        parts.append(f"**+{bones}** bones")
    if add_cents > 0:
        parts.append(f"**${add_cents / 100:.2f}** recorded")
    account = db.get_account(discord_id)
    tier_key = _acct_str(account, "donor_tier")
    if tier_key:
        parts.append(f"tier **{tier_label(tier_key)}**")
    if mood > 0:
        parts.append(f"**+{mood}** mood")
    if standing > 0:
        parts.append(f"**+{standing}** standing")
    if supporter_days > 0:
        until = _acct_str(db.get_account(discord_id), "donor_supporter_until")
        parts.append(
            f"**+{DONOR_LEGEND_DAILY_BONUS}** `/bones action:daily` until **{until}**"
            if until
            else f"**{supporter_days}** supporter days"
        )
    if not parts:
        return True, "donor record updated."
    return True, " · ".join(parts)


def bones_from_donation_cents(cents: int) -> int:
    dollars = cents / 100.0
    return max(0, int(round(dollars * DONOR_BONES_PER_DOLLAR)))


def _bool_field(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).lower() in ("true", "1", "yes")


def _record_kofi_transaction(
    conn: sqlite3.Connection,
    *,
    transaction_id: str,
    discord_id: int,
    amount_cents: int,
    bones: int,
    event_type: str,
    tier_name: str,
    is_subscription: bool,
) -> None:
    conn.execute(
        """
        INSERT INTO kofi_transactions
        (transaction_id, discord_id, amount_cents, bones_granted, processed_at,
         event_type, tier_name, is_subscription)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transaction_id,
            discord_id,
            amount_cents,
            bones,
            _utcnow_str(),
            event_type,
            tier_name,
            1 if is_subscription else 0,
        ),
    )


def process_kofi_event(
    payload: dict, *, expected_token: str
) -> tuple[bool, str, int | None, str | None]:
    """Validate Ko-fi webhook payload. Returns (ok, note, discord_id, dm_message)."""
    verification_token = str(payload.get("verification_token", ""))
    if not expected_token:
        return False, "kofi_verification_token not configured.", None, None
    if verification_token != expected_token:
        return False, "invalid verification token.", None, None

    transaction_id = str(payload.get("kofi_transaction_id", ""))
    if not transaction_id:
        return False, "missing transaction id.", None, None

    with db.get_db() as conn:
        existing = conn.execute(
            "SELECT 1 FROM kofi_transactions WHERE transaction_id = ?",
            (transaction_id,),
        ).fetchone()
        if existing:
            return True, "already processed.", None, None

    event_type = str(payload.get("type", "donation") or "donation")

    try:
        amount_cents = int(round(float(str(payload.get("amount", "0"))) * 100))
    except (TypeError, ValueError):
        return False, "invalid donation amount.", None, None
    if amount_cents <= 0:
        return False, "zero donation amount.", None, None

    if event_type == "shop order":
        from engine.kofi_shop import process_kofi_shop_order

        return process_kofi_shop_order(
            payload, transaction_id=transaction_id, amount_cents=amount_cents
        )

    message = str(payload.get("message", "") or "")
    email = str(payload.get("email", "") or "")
    tier_name = str(payload.get("tier_name", "") or "")
    is_subscription = _bool_field(payload.get("is_subscription_payment")) or event_type == "Subscription"
    is_first_sub = _bool_field(payload.get("is_first_subscription_payment"))

    discord_id = parse_discord_id_from_message(message)
    if not discord_id and email:
        with db.get_db() as conn:
            discord_id = _discord_id_from_email(conn, email)

    if not discord_id:
        hint = "Put your Discord user id in the Ko-fi message on first subscribe."
        if is_subscription and not is_first_sub:
            hint = "Renewal could not be matched; use the same Ko-fi email as your first payment."
        return False, f"no discord account linked. {hint}", None, None

    if email:
        with db.get_db() as conn:
            _link_kofi_email(conn, email, discord_id)

    if is_subscription:
        ok, note, did = _process_kofi_membership(
            transaction_id=transaction_id,
            discord_id=discord_id,
            amount_cents=amount_cents,
            tier_name=tier_name,
            is_first_sub=is_first_sub,
            event_type=event_type,
        )
        return ok, note, did, None

    ok, note, did = _process_kofi_donation(
        transaction_id=transaction_id,
        discord_id=discord_id,
        amount_cents=amount_cents,
        event_type=event_type,
        tier_name=tier_name,
    )
    return ok, note, did, None


def _process_kofi_donation(
    *,
    transaction_id: str,
    discord_id: int,
    amount_cents: int,
    event_type: str,
    tier_name: str,
) -> tuple[bool, str, int | None]:
    account = db.get_account(discord_id)
    bones = bones_from_donation_cents(amount_cents)
    remaining = _bones_remaining_this_month(account)
    bones = min(bones, remaining)

    ok, note = apply_donation_grant(
        discord_id,
        bones=bones,
        add_cents=amount_cents,
        count_toward_monthly_cap=True,
    )
    if not ok:
        return False, note, discord_id

    with db.get_db() as conn:
        _record_kofi_transaction(
            conn,
            transaction_id=transaction_id,
            discord_id=discord_id,
            amount_cents=amount_cents,
            bones=bones,
            event_type=event_type,
            tier_name=tier_name,
            is_subscription=False,
        )

    cap_note = ""
    if bones < bones_from_donation_cents(amount_cents):
        cap_note = f" (monthly cap; **{remaining}** left this month)"
    return True, f"ko-fi tip **${amount_cents / 100:.2f}** → {note}{cap_note}", discord_id


def _process_kofi_membership(
    *,
    transaction_id: str,
    discord_id: int,
    amount_cents: int,
    tier_name: str,
    is_first_sub: bool,
    event_type: str,
) -> tuple[bool, str, int | None]:
    user = db.get_user(discord_id)
    if not user:
        return False, "no registered wolf for that discord account.", discord_id

    tier_key = tier_key_from_kofi_name(tier_name)
    if not tier_key:
        return (
            False,
            f"unknown membership tier **{tier_name or '?'}**; name it den friend, "
            "Pack Benefactor, or Legend in Ko-fi.",
            discord_id,
        )

    perks = KOFI_MEMBERSHIP_PERKS.get(tier_key, {})
    supporter_days = int(perks.get("supporter_days", 0))
    mood = int(perks.get("first_mood", 0)) if is_first_sub else 0
    standing = int(perks.get("first_standing", 0)) if is_first_sub else 0

    db.get_account(discord_id)
    account = db.get_account(discord_id)
    bones = bones_from_donation_cents(amount_cents)
    remaining = _bones_remaining_this_month(account)
    bones = min(bones, remaining)

    with db.get_db() as conn:
        total = _acct_int(account, "donor_total_cents") + amount_cents
        lifetime_tier = tier_for_total_cents(total)
        display_tier = tier_key if _tier_rank(tier_key) >= _tier_rank(lifetime_tier) else lifetime_tier
        conn.execute(
            """
            UPDATE account_progress
            SET donor_total_cents = ?,
                donor_tier = ?,
                kofi_membership_tier = ?
            WHERE discord_id = ?
            """,
            (total, display_tier, tier_key, discord_id),
        )
        _extend_membership_until(conn, discord_id, KOFI_MEMBERSHIP_PERIOD_DAYS)
        if supporter_days > 0:
            _extend_supporter_days(conn, discord_id, supporter_days)
        if bones > 0:
            _record_monthly_bones(conn, discord_id, bones)

        _record_kofi_transaction(
            conn,
            transaction_id=transaction_id,
            discord_id=discord_id,
            amount_cents=amount_cents,
            bones=bones,
            event_type=event_type,
            tier_name=tier_name,
            is_subscription=True,
        )

    if bones > 0:
        db.add_bones(discord_id, bones, wolf_id=user["id"])
    if mood > 0:
        db.adjust_mood(user["id"], mood)
    if standing > 0:
        db.adjust_wolf_standing(discord_id, standing)

    account = db.get_account(discord_id)
    member_until = _acct_str(account, "kofi_membership_until")
    sub_label = "first month" if is_first_sub else "renewal"
    parts = [
        f"**{tier_label(tier_key)}** membership ({sub_label})",
        f"active until **{member_until}**",
    ]
    if bones > 0:
        parts.append(f"**+{bones}** bones")
    if supporter_days > 0:
        until = _acct_str(account, "donor_supporter_until")
        parts.append(f"**+{DONOR_LEGEND_DAILY_BONUS}** `/bones action:daily` until **{until}**")
    if mood > 0:
        parts.append(f"**+{mood}** mood")
    if standing > 0:
        parts.append(f"**+{standing}** standing")

    cap_note = ""
    if bones < bones_from_donation_cents(amount_cents):
        cap_note = f" (monthly cap; **{remaining}** left)"
    return True, " · ".join(parts) + cap_note, discord_id


def process_kofi_donation(
    *,
    transaction_id: str,
    amount_str: str,
    message: str,
    verification_token: str,
    expected_token: str,
) -> tuple[bool, str, int | None, str | None]:
    """Backward-compatible wrapper for simple donation fields."""
    return process_kofi_event(
        {
            "kofi_transaction_id": transaction_id,
            "amount": amount_str,
            "message": message,
            "verification_token": verification_token,
            "type": "Donation",
            "is_subscription_payment": False,
        },
        expected_token=expected_token,
    )


def create_donation_code(
    *,
    bones: int,
    donor_tier: str = "",
    mood_bonus: int = 0,
    standing_bonus: int = 0,
    daily_bonus_days: int = 0,
    max_uses: int = 1,
    expires_at: str | None = None,
    note: str = "",
) -> str:
    code = secrets.token_urlsafe(6).upper().replace("-", "")[:10]
    now = _utcnow_str()
    with db.get_db() as conn:
        conn.execute(
            """
            INSERT INTO donation_codes
            (code, bones, donor_tier, mood_bonus, standing_bonus, daily_bonus_days,
             max_uses, uses_count, created_at, expires_at, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (
                code,
                bones,
                donor_tier,
                mood_bonus,
                standing_bonus,
                daily_bonus_days,
                max(1, max_uses),
                now,
                expires_at,
                note,
            ),
        )
    return code


def redeem_code(discord_id: int, raw_code: str) -> tuple[bool, str]:
    code = raw_code.strip().upper()
    if not code:
        return False, "enter a code."

    user = db.get_user(discord_id)
    if not user:
        return False, "use `/register` first."

    with db.get_db() as conn:
        row = conn.execute(
            "SELECT * FROM donation_codes WHERE code = ?", (code,)
        ).fetchone()
        if not row:
            return False, "unknown code."

        if row["expires_at"]:
            expires = _parse_date(str(row["expires_at"]))
            if expires and expires < _today():
                return False, "that code has expired."

        if int(row["uses_count"]) >= int(row["max_uses"]):
            return False, "that code has no uses left."

        already = conn.execute(
            "SELECT 1 FROM donation_redemptions WHERE code = ? AND discord_id = ?",
            (code, discord_id),
        ).fetchone()
        if already:
            return False, "you already redeemed this code."

        conn.execute(
            """
            INSERT INTO donation_redemptions (code, discord_id, redeemed_at)
            VALUES (?, ?, ?)
            """,
            (code, discord_id, _utcnow_str()),
        )
        conn.execute(
            "UPDATE donation_codes SET uses_count = uses_count + 1 WHERE code = ?",
            (code,),
        )

    ok, note = apply_donation_grant(
        discord_id,
        bones=int(row["bones"]),
        tier=str(row["donor_tier"] or ""),
        mood=int(row["mood_bonus"]),
        standing=int(row["standing_bonus"]),
        supporter_days=int(row["daily_bonus_days"]),
        count_toward_monthly_cap=False,
    )
    if not ok:
        return False, note
    return True, f"redeemed **{code}**; {note}"


def donor_status_lines(discord_id: int) -> list[str]:
    account = db.get_account(discord_id)
    lines = ["**Donations (you only)**"]
    if not account:
        lines.append("• no donor record yet.")
        lines.append(
            f"ko-fi: put your discord user id in the message on **first subscribe** "
            f"(**{discord_id}**); **{DONOR_BONES_PER_DOLLAR}** bones per $1, "
            f"**{DONOR_MONTHLY_BONE_CAP}**/month cap. "
            f"membership tiers: den friend / pack benefactor / legend."
        )
        return lines

    tier_key = effective_donor_tier(account)
    total_cents = _acct_int(account, "donor_total_cents")
    membership_tier = _acct_str(account, "kofi_membership_tier")
    member_until = _parse_date(_acct_str(account, "kofi_membership_until"))
    active_member = bool(membership_tier and member_until and member_until >= _today())

    if tier_key or total_cents > 0 or active_member:
        lines.append(f"• tier: **{tier_label(tier_key)}**")
        if active_member:
            lines.append(
                f"• ko-fi membership: **{tier_label(membership_tier)}** until **{_acct_str(account, 'kofi_membership_until')}**"
            )
        if total_cents > 0:
            lines.append(f"• lifetime ko-fi: **${total_cents / 100:.2f}**")
    else:
        lines.append("• no ko-fi donations recorded yet.")

    lines.append(
        f"• membership tiers on ko-fi (**$5** minimum): **den friend** ($5), "
        f"**pack benefactor** ($10), **legend** ($25)"
    )

    bonus = donor_daily_bonus(discord_id)
    until = _acct_str(account, "donor_supporter_until")
    if bonus > 0 and until:
        lines.append(f"• supporter `/bones action:daily`: **+{bonus}** until **{until}**")
    elif until:
        lines.append(f"• supporter perk expired **{until}**")

    remaining = _bones_remaining_this_month(account)
    lines.append(
        f"• ko-fi bones left this month: **{remaining}/{DONOR_MONTHLY_BONE_CAP}**"
    )
    lines.append(
        f"redeem a gift code with `/redeem` · ko-fi message: your discord id **{discord_id}**"
    )
    return lines
