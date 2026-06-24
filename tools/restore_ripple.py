"""Restore Ripple on the owner account (idempotent). Run on the host that owns fable.db."""
import sys

sys.path.insert(0, ".")

import database as db

DISCORD_ID = 1056053114177855548

RIPPLE_STATS = dict(
    attr_str=2,
    attr_dex=3,
    attr_con=4,
    attr_int=5,
    attr_cha=4,
    attr_wis=4,
)


def main() -> None:
    db.init_db()
    for w in db.list_user_wolves(DISCORD_ID):
        if w["wolf_name"].lower() == "ripple":
            user = db.get_user_by_id(w["id"])
            changes = db.backfill_canonical_character_sheet(
                user, force_lore=True, force_traits=True, force_defaults=True
            )
            print(f"ALREADY_REGISTERED wolf_id={w['id']} backfill={changes or 'ok'}")
            return

    wolf_id = db.register_user(
        DISCORD_ID,
        "Ripple",
        "silverrush",
        wolf_role="medic",
        stats=RIPPLE_STATS,
        birth_sex="female",
        sexuality="asexual",
        age_months=48,
        maw_belief="zealot",
        set_active=False,
    )
    user = db.get_user_by_id(wolf_id)
    db.backfill_canonical_character_sheet(user, force_lore=True, force_traits=True)
    print(
        f"REGISTERED wolf_id={wolf_id} role={user['wolf_role']} pack={user['great_pack']} "
        f"stats={user['attr_str']}/{user['attr_dex']}/{user['attr_con']}/"
        f"{user['attr_int']}/{user['attr_cha']}/{user['attr_wis']}"
    )


if __name__ == "__main__":
    main()
