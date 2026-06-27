"""Ko-fi Shop Order processing; auto bones/codes + manual fulfillment queue."""

from __future__ import annotations

import datetime
import json
import sqlite3
from typing import Any

import database as db
from config import KOFI_SHOP_CATALOG
from engine.donor import (
    _discord_id_from_email,
    _link_kofi_email,
    _record_kofi_transaction,
    apply_donation_grant,
    create_donation_code,
    parse_discord_id_from_message,
)

ShopResult = tuple[bool, str, int | None, str | None]


def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds")


def match_shop_product(item: dict[str, Any], *, amount_cents: int) -> str | None:
    code = str(item.get("direct_link_code", "") or "")
    variant = str(
        item.get("variation_name") or item.get("variant_name") or item.get("name") or ""
    ).lower()

    best_key: str | None = None
    best_score = 0
    for key, prod in KOFI_SHOP_CATALOG.items():
        score = 0
        codes = prod.get("direct_link_codes") or ()
        if code and code in codes:
            score += 1000
        for pattern in prod.get("match_names") or ():
            if pattern.lower() in variant:
                score += len(pattern)
        if score > best_score:
            best_score = score
            best_key = key
    if best_score > 0:
        return best_key

    price_matches = [
        key
        for key, prod in KOFI_SHOP_CATALOG.items()
        if int(prod.get("price_cents", 0)) == amount_cents
    ]
    if len(price_matches) == 1:
        return price_matches[0]
    return None


def _insert_shop_order(
    conn: sqlite3.Connection,
    *,
    transaction_id: str,
    discord_id: int | None,
    email: str,
    product_key: str,
    product_label: str,
    amount_cents: int,
    status: str,
    notes: str = "",
) -> int:
    cur = conn.execute(
        """
        INSERT INTO kofi_shop_orders
        (transaction_id, discord_id, email, product_key, product_label,
         amount_cents, status, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transaction_id,
            discord_id,
            email,
            product_key,
            product_label,
            amount_cents,
            status,
            notes,
            _now_iso(),
        ),
    )
    return int(cur.lastrowid)


def list_pending_shop_orders(limit: int = 20) -> list[sqlite3.Row]:
    with db.get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM kofi_shop_orders
            WHERE status = 'pending'
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def fulfill_shop_order(order_id: int, *, notes: str = "") -> tuple[bool, str]:
    with db.get_db() as conn:
        row = conn.execute(
            "SELECT * FROM kofi_shop_orders WHERE id = ?", (order_id,)
        ).fetchone()
        if not row:
            return False, "order not found."
        if row["status"] != "pending":
            return False, f"order #{order_id} is already **{row['status']}**."
        conn.execute(
            """
            UPDATE kofi_shop_orders
            SET status = 'fulfilled', fulfilled_at = ?, notes = ?
            WHERE id = ?
            """,
            (_now_iso(), notes or row["notes"], order_id),
        )
    label = row["product_label"]
    who = f"<@{row['discord_id']}>" if row["discord_id"] else row["email"]
    return True, f"marked **{label}** for {who} as fulfilled."


def process_kofi_shop_order(
    payload: dict,
    *,
    transaction_id: str,
    amount_cents: int,
) -> ShopResult:
    message = str(payload.get("message", "") or "")
    email = str(payload.get("email", "") or "")
    shop_items = payload.get("shop_items") or []
    if not isinstance(shop_items, list) or not shop_items:
        return False, "shop order has no items.", None, None

    discord_id = parse_discord_id_from_message(message)
    with db.get_db() as conn:
        if not discord_id and email:
            discord_id = _discord_id_from_email(conn, email)
        if discord_id and email:
            _link_kofi_email(conn, email, discord_id)

    lines: list[str] = []
    dm_parts: list[str] = []
    total_bones = 0
    unknown_items: list[str] = []

    processed_labels: list[str] = []

    with db.get_db() as conn:
        for raw_item in shop_items:
            if not isinstance(raw_item, dict):
                continue
            product_key = match_shop_product(raw_item, amount_cents=amount_cents)
            if not product_key:
                code = str(raw_item.get("direct_link_code", "?"))
                unknown_items.append(code)
                _insert_shop_order(
                    conn,
                    transaction_id=transaction_id,
                    discord_id=discord_id,
                    email=email,
                    product_key="unknown",
                    product_label=f"unknown ({code})",
                    amount_cents=amount_cents,
                    status="pending",
                    notes=json.dumps(raw_item),
                )
                continue

            prod = KOFI_SHOP_CATALOG[product_key]
            label = str(prod["label"])
            processed_labels.append(label)
            delivery = str(prod.get("delivery", "manual"))

            grant_item_key = str(prod.get("grant_item") or "")
            if grant_item_key:
                item_row = db.get_item_by_key(grant_item_key)
                if not item_row:
                    lines.append(f"**{label}**; missing item `{grant_item_key}` in bot catalog")
                    continue
                if discord_id and db.get_user(discord_id):
                    db.grant_item(discord_id, item_row["id"])
                    lines.append(f"**{label}** → **{item_row['name']}** in `/bones action:inventory`")
                    dm_parts.append(
                        f"**{item_row['name']}** is in `/bones action:inventory`.\n"
                        + (
                            "When your wolf dies, use `/bones action:use item:revive` to bring them back as-is."
                            if grant_item_key == "revive"
                            else "When your wolf dies, use `/bones action:use item:reincarnation new_name:<name>` "
                            "for a new identity with the same stats."
                        )
                    )
                    _insert_shop_order(
                        conn,
                        transaction_id=transaction_id,
                        discord_id=discord_id,
                        email=email,
                        product_key=product_key,
                        product_label=label,
                        amount_cents=int(prod.get("price_cents", amount_cents)),
                        status="fulfilled",
                    )
                    continue
                _insert_shop_order(
                    conn,
                    transaction_id=transaction_id,
                    discord_id=discord_id,
                    email=email,
                    product_key=product_key,
                    product_label=label,
                    amount_cents=int(prod.get("price_cents", amount_cents)),
                    status="pending",
                    notes=f"grant_item:{grant_item_key}",
                )
                lines.append(f"**{label}**; queued (need `/register` + discord id on order)")
                dm_parts.append(
                    f"**{label}**; we couldn't find a registered wolf for your discord id.\n"
                    "Use `/register`, then contact staff with your order receipt."
                )
                continue

            if delivery == "manual":
                _insert_shop_order(
                    conn,
                    transaction_id=transaction_id,
                    discord_id=discord_id,
                    email=email,
                    product_key=product_key,
                    product_label=label,
                    amount_cents=int(prod.get("price_cents", amount_cents)),
                    status="pending",
                )
                lines.append(f"**{label}**; queued for manual delivery")
                dm_parts.append(
                    f"**{label}**; we'll dm you within **{prod.get('sla_days', 7)} days** "
                    f"to deliver. make sure dms are open."
                )
                continue

            bones = int(prod.get("bones", 0))
            tier = str(prod.get("donor_tier", "") or "")
            supporter_days = int(prod.get("supporter_days", 0))
            mood = int(prod.get("mood", 0))
            standing = int(prod.get("standing", 0))

            if delivery == "code":
                code = create_donation_code(
                    bones=bones,
                    donor_tier=tier,
                    mood_bonus=mood,
                    standing_bonus=standing,
                    daily_bonus_days=supporter_days,
                    max_uses=1,
                    note=f"shop:{product_key}:{transaction_id}",
                )
                lines.append(f"**{label}** → code **`{code}`**")
                if product_key == "gift_bone_pouch":
                    dm_parts.append(
                        f"**gift code:** `{code}`\n"
                        f"share with any registered player; they use `/redeem {code}` "
                        f"(**{bones}** bones)."
                    )
                elif product_key == "legend_gift_card":
                    dm_parts.append(
                        f"**legend gift code:** `{code}`\n"
                        f"share or redeem with `/redeem {code}`; "
                        f"**{bones}** bones, legend perks, **+3 `/bones action:daily`** for "
                        f"**{supporter_days}** days."
                    )
                else:
                    dm_parts.append(f"**{label}** code: `{code}`; `/redeem {code}`")
                _insert_shop_order(
                    conn,
                    transaction_id=transaction_id,
                    discord_id=discord_id,
                    email=email,
                    product_key=product_key,
                    product_label=label,
                    amount_cents=int(prod.get("price_cents", amount_cents)),
                    status="fulfilled",
                    notes=f"code:{code}",
                )
                continue

            # instant delivery
            if discord_id and db.get_user(discord_id):
                ok, grant_note = apply_donation_grant(
                    discord_id,
                    bones=bones,
                    tier=tier,
                    mood=mood,
                    standing=standing,
                    supporter_days=supporter_days,
                    count_toward_monthly_cap=False,
                )
                if ok:
                    total_bones += bones
                    lines.append(f"**{label}** → {grant_note}")
                    dm_parts.append(f"**{label}**; {grant_note}")
                    _insert_shop_order(
                        conn,
                        transaction_id=transaction_id,
                        discord_id=discord_id,
                        email=email,
                        product_key=product_key,
                        product_label=label,
                        amount_cents=int(prod.get("price_cents", amount_cents)),
                        status="fulfilled",
                    )
                    continue

            code = create_donation_code(
                bones=bones,
                donor_tier=tier,
                mood_bonus=mood,
                standing_bonus=standing,
                daily_bonus_days=supporter_days,
                max_uses=1,
                note=f"shop:{product_key}:{transaction_id}",
            )
            lines.append(f"**{label}** → code **`{code}`** (could not auto-grant)")
            dm_parts.append(
                f"**{label}**; use `/register` then `/redeem {code}` "
                f"(include discord id on future orders for instant delivery)."
            )
            _insert_shop_order(
                conn,
                transaction_id=transaction_id,
                discord_id=discord_id,
                email=email,
                product_key=product_key,
                product_label=label,
                amount_cents=int(prod.get("price_cents", amount_cents)),
                status="fulfilled",
                notes=f"code:{code}",
            )

        _record_kofi_transaction(
            conn,
            transaction_id=transaction_id,
            discord_id=discord_id or 0,
            amount_cents=amount_cents,
            bones=total_bones,
            event_type="Shop Order",
            tier_name=", ".join(processed_labels),
            is_subscription=False,
        )

    if unknown_items:
        lines.append(
            f"unknown item code(s): {', '.join(unknown_items)}; add to `config.py` "
            f"`direct_link_codes` or fulfill manually."
        )

    if not lines:
        return False, "no shop items processed.", discord_id, None

    note = "shop order · " + " · ".join(lines)
    dm_message = None
    if dm_parts:
        dm_message = "**thank you for your shop order!** 🦴\n\n" + "\n\n".join(dm_parts)
        if any("queued for manual" in line for line in lines):
            dm_message += (
                "\n\n_Manual items: we'll contact you on Discord. "
                "Pending orders show in `/patronadmin orders`._"
            )
    return True, note, discord_id, dm_message
