"""Swap Finnpelt ↔ RiverShroud roles; transfer Finnpelt to admin account."""
import sys

sys.path.insert(0, ".")

import database as db
from engine.aging import proficiencies_for_role, sync_role_to_age

ADMIN_DISCORD_ID = 1056053114177855548
FINNPELT_ID = 94
RIVERSHROUD_ID = 96
THISTLEHIDE_KEY = "thistlehide"


def _set_role(wolf_id: int, role: str) -> str:
    user = db.get_user_by_id(wolf_id)
    if not user:
        raise RuntimeError(f"wolf_id={wolf_id} not found")
    age = int(user["age_months"])
    new_role = sync_role_to_age(age, role)
    db.update_user_by_id(
        wolf_id,
        wolf_role=new_role,
        skill_proficiencies=proficiencies_for_role(new_role),
    )
    return new_role


def main() -> None:
    db.init_db()
    finn = db.get_user_by_id(FINNPELT_ID)
    river = db.get_user_by_id(RIVERSHROUD_ID)
    if not finn or not river:
        raise SystemExit("Finnpelt or RiverShroud missing from database.")

    finn_role = _set_role(FINNPELT_ID, "hunter")
    river_role = _set_role(RIVERSHROUD_ID, "alpha")

    pack = db.get_pack_by_key(THISTLEHIDE_KEY)
    if not pack:
        raise SystemExit("Thistlehide pack not found.")
    with db.get_db() as conn:
        conn.execute(
            "UPDATE packs SET alpha_id = ? WHERE id = ?",
            (int(river["discord_id"]), int(pack["id"])),
        )

    transfer = "skipped"
    if int(finn["discord_id"]) != ADMIN_DISCORD_ID:
        transfer = db.reassign_wolf_owner(FINNPELT_ID, ADMIN_DISCORD_ID, set_active=False)
    else:
        transfer = "already_owner"

    finn = db.get_user_by_id(FINNPELT_ID)
    river = db.get_user_by_id(RIVERSHROUD_ID)
    pack = db.get_pack_by_key(THISTLEHIDE_KEY)
    print(
        f"Finnpelt role={finn['wolf_role']} owner={finn['discord_id']} | "
        f"RiverShroud role={river['wolf_role']} owner={river['discord_id']} | "
        f"Thistlehide alpha_id={pack['alpha_id']} | transfer={transfer}"
    )


if __name__ == "__main__":
    main()
