"""Ko-fi donor / shop / membership tests; run: python -m tests.test_kofi"""

from __future__ import annotations

import sys
import traceback
import uuid

import database as db
from config import KOFI_SHOP_CATALOG
from engine.donor import (
    bones_from_donation_cents,
    donor_daily_bonus,
    effective_donor_tier,
    process_kofi_event,
    redeem_code,
    tier_key_from_kofi_name,
)
from engine.kofi_shop import fulfill_shop_order, list_pending_shop_orders, match_shop_product

TOKEN = "test-kofi-token"
TEST_GUILD = 1516980863911329802
USER_A = 999000001000000001
USER_B = 999000002000000002
USER_LEGEND = 999000003000000003
USER_NO_WOLF = 999000004000000004
USER_DONOR = 999000005000000005

_pass = 0
_fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  OK  {name}")
    else:
        _fail += 1
        print(f" FAIL {name}" + (f" - {detail.encode('ascii', 'replace').decode()}" if detail else ""))


def _ensure_world() -> None:
    if not db.get_world(TEST_GUILD):
        with db.get_db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO world_state (guild_id, day_number) VALUES (?, 1)",
                (TEST_GUILD,),
            )


def _ensure_user(discord_id: int, name: str) -> None:
    if db.get_user(discord_id):
        return
    _ensure_world()
    db.register_user(discord_id, name, "greyspire", "hunter")


def _tx(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _payload(**kwargs) -> dict:
    base = {
        "verification_token": TOKEN,
        "amount": "5.00",
        "message": "",
        "email": "",
        "currency": "USD",
        "is_subscription_payment": False,
        "is_first_subscription_payment": False,
    }
    base.update(kwargs)
    return base


def test_tier_matching() -> None:
    print("\n=== tier / product matching ===")
    check("legend tier name", tier_key_from_kofi_name("Legend of the Den") == "legend")
    check("friend tier name", tier_key_from_kofi_name("Den Friend") == "friend")
    check("unknown tier", tier_key_from_kofi_name("Supporter") == "")
    check("bones rate $5", bones_from_donation_cents(500) == 75)

    check(
        "bone pouch by link",
        match_shop_product({"direct_link_code": "f5d07feec4"}, amount_cents=500) == "bone_pouch",
    )
    check(
        "bone cache by link",
        match_shop_product({"direct_link_code": "86a62f713a"}, amount_cents=1000) == "bone_cache",
    )
    check(
        "gift pouch by link",
        match_shop_product({"direct_link_code": "79c40a6fa6"}, amount_cents=500) == "gift_bone_pouch",
    )
    check(
        "gift vs pouch title",
        match_shop_product({"variation_name": "Gift a Bone Pouch"}, amount_cents=500)
        == "gift_bone_pouch",
    )
    check(
        "plain pouch title",
        match_shop_product({"variation_name": "Bone Pouch"}, amount_cents=500) == "bone_pouch",
    )
    check(
        "all catalog codes non-empty",
        all(
            prod.get("direct_link_codes") or prod.get("grant_item")
            for prod in KOFI_SHOP_CATALOG.values()
        ),
    )


def test_auth_and_idempotency() -> None:
    print("\n=== auth & idempotency ===")
    ok, note, *_ = process_kofi_event(
        _payload(kofi_transaction_id="auth-bad", verification_token="wrong"),
        expected_token=TOKEN,
    )
    check("bad token rejected", not ok)

    tx = _tx("idem")
    ok, note, *_ = process_kofi_event(
        _payload(
            kofi_transaction_id=tx,
            type="Donation",
            message=str(USER_NO_WOLF),
            amount="5.00",
        ),
        expected_token=TOKEN,
    )
    check("donation without wolf fails", not ok and "No registered wolf" in note, note)

    _ensure_user(USER_A, "TestAlpha")
    ok, note, *_ = process_kofi_event(
        _payload(
            kofi_transaction_id=tx,
            type="Donation",
            message=str(USER_A),
            amount="5.00",
        ),
        expected_token=TOKEN,
    )
    check("donation succeeds after register", ok, note)

    ok2, note2, *_ = process_kofi_event(
        _payload(kofi_transaction_id=tx, type="Donation", message=str(USER_A)),
        expected_token=TOKEN,
    )
    check("duplicate txn skipped", ok2 and "Already processed" in note2)


def test_donation_and_cap() -> None:
    print("\n=== donations ===")
    _ensure_user(USER_DONOR, "TestDonor")
    uid = USER_DONOR
    before = db.get_user(uid)["bones"]

    ok, note, did, dm = process_kofi_event(
        _payload(
            kofi_transaction_id=_tx("don"),
            type="Donation",
            message=str(uid),
            email="donor@test.com",
            amount="10.00",
        ),
        expected_token=TOKEN,
    )
    after = db.get_user(uid)["bones"]
    check("donation grants bones", ok and after - before == 150, f"{before}->{after} {note}")
    check("email linked", did == uid)


def test_membership() -> None:
    print("\n=== membership ===")
    _ensure_user(USER_B, "TestBeta")
    uid = USER_B

    ok, note, did, dm = process_kofi_event(
        _payload(
            kofi_transaction_id=_tx("sub-first"),
            type="Subscription",
            is_subscription_payment=True,
            is_first_subscription_payment=True,
            tier_name="Den Friend",
            message=str(uid),
            email="beta@test.com",
            amount="5.00",
        ),
        expected_token=TOKEN,
    )
    acct = db.get_account(uid)
    check("first membership ok", ok, note)
    check("membership tier set", acct["kofi_membership_tier"] == "friend")
    check("membership until set", bool(acct["kofi_membership_until"]))

    ok2, note2, did2, _ = process_kofi_event(
        _payload(
            kofi_transaction_id=_tx("sub-renew"),
            type="Subscription",
            is_subscription_payment=True,
            is_first_subscription_payment=False,
            tier_name="Den Friend",
            message="",
            email="beta@test.com",
            amount="5.00",
        ),
        expected_token=TOKEN,
    )
    check("renewal via email", ok2 and did2 == uid, note2)


def test_shop() -> None:
    print("\n=== shop orders ===")
    _ensure_user(USER_A, "TestAlpha")

    ok, note, did, dm = process_kofi_event(
        _payload(
            kofi_transaction_id=_tx("shop-pouch"),
            type="Shop Order",
            message=str(USER_A),
            email="alpha@test.com",
            amount="5.00",
            shop_items=[{"direct_link_code": "f5d07feec4", "variation_name": "Bone Pouch"}],
        ),
        expected_token=TOKEN,
    )
    check("bone pouch instant", ok and "Bone Pouch" in note, note)

    ok, note, did, dm = process_kofi_event(
        _payload(
            kofi_transaction_id=_tx("shop-gift"),
            type="Shop Order",
            message=str(USER_A),
            amount="5.00",
            shop_items=[{"direct_link_code": "79c40a6fa6"}],
        ),
        expected_token=TOKEN,
    )
    check("gift generates code", ok and "code" in note.lower(), note)
    check("gift dm present", dm is not None and "Gift code" in dm)

    manual_tx = _tx("shop-manual")
    ok, note, _, dm = process_kofi_event(
        _payload(
            kofi_transaction_id=manual_tx,
            type="Shop Order",
            message=str(USER_A),
            amount="10.00",
            shop_items=[{"direct_link_code": "bba5807b42"}],
        ),
        expected_token=TOKEN,
    )
    check("manual item queued", ok and "queued" in note, note)
    pending = list_pending_shop_orders()
    match = [r for r in pending if r["transaction_id"] == manual_tx]
    check("pending orders list", bool(match))
    if match:
        oid = match[0]["id"]
        fok, fnote = fulfill_shop_order(oid, notes="delivered")
        check("fulfill order", fok, fnote)
        fok2, _ = fulfill_shop_order(oid)
        check("double fulfill blocked", not fok2)
    else:
        check("fulfill order", False, "manual order not found")
        check("double fulfill blocked", True)


def test_redeem() -> None:
    print("\n=== redeem codes ===")
    from engine.donor import create_donation_code

    _ensure_user(USER_B, "TestBeta")
    code = create_donation_code(bones=50, note="test")
    ok, note = redeem_code(USER_B, code)
    check("redeem works", ok, note)
    ok2, note2 = redeem_code(USER_B, code)
    check("double redeem blocked", not ok2, note2)


def test_legend_membership_daily() -> None:
    print("\n=== legend daily bonus ===")
    uid = USER_LEGEND
    _ensure_user(uid, "TestLegend")
    ok, _, _, _ = process_kofi_event(
        _payload(
            kofi_transaction_id=_tx("sub-legend"),
            type="Subscription",
            is_subscription_payment=True,
            is_first_subscription_payment=True,
            tier_name="Legend of the Den",
            message=str(uid),
            amount="25.00",
        ),
        expected_token=TOKEN,
    )
    check("legend membership", ok)
    check("legend daily bonus active", donor_daily_bonus(uid) == 3)
    acct = db.get_account(uid)
    check("effective tier", effective_donor_tier(acct) == "legend")


def test_wrapper_return_shape() -> None:
    print("\n=== API shape ===")
    from engine.donor import process_kofi_donation

    result = process_kofi_donation(
        transaction_id=_tx("shape"),
        amount_str="5.00",
        message=str(USER_A),
        verification_token=TOKEN,
        expected_token=TOKEN,
    )
    check("wrapper returns 4-tuple", len(result) == 4)


def main() -> int:
    print("Initializing test DB...")
    db.init_db()
    tests = [
        test_tier_matching,
        test_auth_and_idempotency,
        test_donation_and_cap,
        test_membership,
        test_shop,
        test_redeem,
        test_legend_membership_daily,
        test_wrapper_return_shape,
    ]
    for fn in tests:
        try:
            fn()
        except Exception as exc:
            global _fail
            _fail += 1
            print(f" FAIL {fn.__name__} EXCEPTION: {exc}")
            traceback.print_exc()

    print(f"\n{'=' * 40}\nResults: {_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    return 1 if _fail else 0


if __name__ == "__main__":
    sys.exit(main())
