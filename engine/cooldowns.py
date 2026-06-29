"""Per-sunrise activity status for /cooldowns."""

from __future__ import annotations

import sqlite3

import database as db
from config import BOOST_DAILY_BONUS, DAILY_REWARD
from engine.prestige import apply_bone_bonus, bone_bonus_pct
# can_hunt_again is unused here directly; re-exported for engine.wolf_checklist.
from engine.role_privileges import can_hunt_again
from utils.currency import format_bones

DROWN_SICK_ROLE = "drown_sick"


def _col(user: sqlite3.Row, name: str, default: int = 0) -> int:
    if name not in user.keys():
        return default
    return int(user[name])


def _used_today(user: sqlite3.Row, day: int, column: str) -> bool:
    return _col(user, column) >= day


def daily_stipend_amount(
    prestige_tier: int, *, is_booster: bool = False, donor_bonus: int = 0
) -> int:
    base = apply_bone_bonus(DAILY_REWARD, prestige_tier)
    if is_booster:
        base += BOOST_DAILY_BONUS
    if donor_bonus > 0:
        base += donor_bonus
    return base


def daily_ration_note(
    prestige_tier: int,
    *,
    pack_name: str | None = None,
    treasury: int | None = None,
    is_booster: bool = False,
    donor_bonus: int = 0,
) -> str:
    """Where `/bones action:daily` bones come from; shown on `/checklist`."""
    base = DAILY_REWARD
    payout = daily_stipend_amount(
        prestige_tier, is_booster=is_booster, donor_bonus=donor_bonus
    )
    bonus_pct = bone_bonus_pct(prestige_tier)
    lines = [
        "paid from **pack treasury** each sunrise (hunt tax, `/pack deposit`, prey-pile shares).",
        f"stipend: **{format_bones(payout)}**",
    ]
    if is_booster:
        lines.append(
            f"_includes **+{BOOST_DAILY_BONUS}** den patron boost (paid to you, not treasury)._"
        )
    if donor_bonus > 0:
        lines.append(
            f"_includes **+{donor_bonus}** supporter thank-you (paid to you, not treasury)._"
        )
    if bonus_pct > 0:
        lines.append(
            f"_(base {format_bones(base)} + {bonus_pct}% prestige; +1 xp; debits treasury)_"
        )
    else:
        lines.append(f"_(base {format_bones(base)}; +1 xp; debits treasury)_")
    if pack_name is not None and treasury is not None:
        lines.append(f"**{pack_name}** treasury: **{format_bones(treasury)}**")
    return "\n".join(lines)


def daily_stipend_status(
    user: sqlite3.Row,
    day: int,
    prestige_tier: int,
    *,
    is_booster: bool = False,
    donor_bonus: int = 0,
) -> tuple[str, str]:
    """Status line + full note for /cooldowns daily field."""
    base_payout = daily_stipend_amount(prestige_tier, is_booster=False)
    payout = daily_stipend_amount(
        prestige_tier, is_booster=is_booster, donor_bonus=donor_bonus
    )
    from engine.role_features import is_rogue_wolf

    if is_rogue_wolf(user):
        note = (
            "**rogues** cannot draw a den stipend; earn bones with `/bones action:hunt`, "
            "`/bones action:work`, or `/field action:scavenge`."
        )
        if _used_today(user, day, "last_daily_day"):
            return "n/a", note
        return "rogue", note

    pack_id = user["pack_id"] if "pack_id" in user.keys() else None
    if not pack_id:
        note = daily_ration_note(prestige_tier)
        note += "\n**loners** cannot draw a stipend; `/setfaction` to join a great pack."
        if _used_today(user, day, "last_daily_day"):
            return "used", note
        return "no pack", note

    pack = db.get_pack(pack_id)
    treasury = int(pack["treasury"]) if pack else 0
    pack_name = pack["name"] if pack else "pack"
    note = daily_ration_note(
        prestige_tier,
        pack_name=pack_name,
        treasury=treasury,
        is_booster=is_booster,
        donor_bonus=donor_bonus,
    )

    if _used_today(user, day, "last_daily_day"):
        return "used", note
    if treasury < base_payout:
        return f"treasury low ({format_bones(treasury)} need {format_bones(base_payout)})", note
    return "ready", note

