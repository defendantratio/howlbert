"""Cat pact tests; run: python -m tests.test_cat_pacts"""

from __future__ import annotations

import database as db
from engine.cat_clans import validate_clan_name
from engine.cat_pacts import PACT_SPECS, pact_border_chance_multiplier

_pass = 0
_fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  OK  {name}")
    else:
        _fail += 1
        print(f" FAIL {name}" + (f" - {detail}" if detail else ""))


def main() -> None:
    db.init_db()

    name, err = validate_clan_name("MossClan")
    check("clan name valid", name == "MossClan" and not err)
    bad, berr = validate_clan_name("X")
    check("clan name too short", bad is None and berr is not None)

    guild_id = 88001
    pack = db.get_pack_by_name("Greyspire")
    check("greyspire pack", pack is not None)
    if not pack:
        raise SystemExit(1)

    db.register_user(88010, "PactAlpha", affiliation="greyspire", wolf_role="alpha")
    user = db.get_user(88010)
    check("user in pack", user and user["pack_id"] == pack["id"])

    db.add_pack_treasury(pack["id"], 200)
    day = 5000

    db.upsert_cat_pact(
        guild_id,
        pack["id"],
        "MossClan",
        pact_type="truce",
        trust=55,
        tribute_paid=30,
        terms_note="No hunting past the oak grove.",
        forged_day=day,
        expires_day=day + PACT_SPECS["truce"]["days"],
        forged_by_discord_id=88010,
    )
    active = db.list_active_cat_pacts(guild_id, pack["id"])
    check("active pact listed", len(active) == 1 and active[0]["clan_name"] == "MossClan")

    mult = pact_border_chance_multiplier(guild_id, pack["id"])
    check("pact lowers border odds", mult < 0.5, str(mult))

    db.adjust_cat_pact_trust(pack["id"], "MossClan", -30)
    pact = db.get_cat_pact(pack["id"], "MossClan")
    check("trust adjusted", pact and int(pact["trust"]) == 25)

    db.break_cat_pact(pack["id"], "MossClan", day=day + 1, reason="Test break.")
    broken = db.get_cat_pact(pack["id"], "MossClan")
    check("pact broken", broken and broken["status"] == "broken")

    expired = db.expire_cat_pacts_for_day(guild_id, day + 99)
    check("expire empty", expired == [])

    db.upsert_cat_pact(
        guild_id,
        pack["id"],
        "PineClan",
        pact_type="alliance",
        trust=70,
        tribute_paid=80,
        terms_note="",
        forged_day=day,
        expires_day=day + 2,
        forged_by_discord_id=88010,
    )
    expired2 = db.expire_cat_pacts_for_day(guild_id, day + 5)
    check("expire pine", "PineClan" in expired2)

    check("deduct treasury", db.deduct_pack_treasury(pack["id"], 10))
    check("deduct fails over balance", not db.deduct_pack_treasury(pack["id"], 999999))

    print(f"\n{_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
