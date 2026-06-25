"""Backfill Soot on player account (idempotent). Run on the host that owns fable.db."""
import sys

sys.path.insert(0, ".")

import database as db
from engine.aging import proficiencies_for_role

DISCORD_ID = 1320489142525759632

SOOT_STATS = dict(
    attr_str=2,
    attr_dex=3,
    attr_con=4,
    attr_int=4,
    attr_cha=3,
    attr_wis=5,
)


def main() -> None:
    db.init_db()
    for w in db.list_user_wolves(DISCORD_ID):
        if w["wolf_name"].lower() == "soot":
            user = db.get_user_by_id(w["id"])
            changes = db.backfill_canonical_character_sheet(
                user, force_lore=True, force_traits=True, force_defaults=True
            )
            db.update_user(
                DISCORD_ID,
                wolf_id=w["id"],
                wolf_role="medic",
                skill_proficiencies=proficiencies_for_role("medic"),
                maw_belief="orthodox",
                great_pack="mistmoor",
                **SOOT_STATS,
            )
            user = db.get_user_by_id(w["id"])
            print(
                f"UPDATED wolf_id={w['id']} backfill={changes or 'ok'} "
                f"role={user['wolf_role']} pack={user['great_pack']} "
                f"belief={user['maw_belief']}"
            )
            return

    wolf_id = db.register_user(
        DISCORD_ID,
        "Soot",
        "mistmoor",
        wolf_role="medic",
        stats=SOOT_STATS,
        birth_sex="female",
        sexuality=None,
        age_months=12,
        maw_belief="orthodox",
    )
    user = db.get_user_by_id(wolf_id)
    db.backfill_canonical_character_sheet(user, force_lore=True, force_traits=True)
    db.update_user(
        DISCORD_ID,
        wolf_id=wolf_id,
        wolf_role="medic",
        skill_proficiencies=proficiencies_for_role("medic"),
    )
    user = db.get_user_by_id(wolf_id)
    print(
        f"REGISTERED wolf_id={wolf_id} role={user['wolf_role']} pack={user['great_pack']} "
        f"stats={user['attr_str']}/{user['attr_dex']}/{user['attr_con']}/"
        f"{user['attr_int']}/{user['attr_cha']}/{user['attr_wis']}"
    )


if __name__ == "__main__":
    main()
