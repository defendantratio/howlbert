"""Per-season pack food-reserve goals; deposit carcasses for unity."""

from __future__ import annotations

import database as db
from config import SEASON_LENGTH_DAYS, SEASONS

SEASON_STASH_TARGETS = {
    "spring": 4,
    "summer": 5,
    "autumn": 6,
    "winter": 5,
}
SEASON_STASH_UNITY_REWARD = 2


def season_for_day(day_number: int) -> str:
    index = ((day_number - 1) // SEASON_LENGTH_DAYS) % len(SEASONS)
    return SEASONS[index]


def season_epoch(day_number: int) -> int:
    return ((day_number - 1) // SEASON_LENGTH_DAYS) * SEASON_LENGTH_DAYS + 1


def stash_goal_target(day_number: int) -> int:
    return SEASON_STASH_TARGETS.get(season_for_day(day_number), 5)


def _sync_pack_epoch(pack, day_number: int) -> None:
    epoch = season_epoch(day_number)
    stored = int(pack["season_goal_epoch"]) if "season_goal_epoch" in pack.keys() else 0
    if stored == epoch:
        return
    db.update_pack_season_goal(
        pack["id"],
        season_goal_epoch=epoch,
        season_stash_deposits=0,
        season_stash_goal_met=0,
    )


def record_stash_deposit(pack_id: int, day_number: int) -> str | None:
    """Increment seasonal stash counter; return celebration line if goal just met."""
    pack = db.get_pack(pack_id)
    if not pack:
        return None
    _sync_pack_epoch(pack, day_number)
    pack = db.get_pack(pack_id)
    if not pack:
        return None

    if int(pack["season_stash_goal_met"]):
        return None

    target = stash_goal_target(day_number)
    new_count = int(pack["season_stash_deposits"]) + 1
    db.update_pack_season_goal(pack_id, season_stash_deposits=new_count)

    if new_count < target:
        return None

    db.update_pack_season_goal(pack_id, season_stash_goal_met=1)
    outcome = db.adjust_pack_unity(pack_id, SEASON_STASH_UNITY_REWARD)
    season = season_for_day(day_number)
    line = (
        f"**Season goal met!** The den filled the **{season}** reserve "
        f"({target} carcasses); pack unity **+{SEASON_STASH_UNITY_REWARD}**."
    )
    if outcome == "dissolved":
        line += " _(The pack fractured anyway; unity hit the dissolve threshold.)_"
    return line


def format_stash_goal_line(pack, day_number: int) -> str:
    _sync_pack_epoch(pack, day_number)
    pack = db.get_pack(pack["id"])
    if not pack:
        return ""
    target = stash_goal_target(day_number)
    count = int(pack["season_stash_deposits"])
    season = season_for_day(day_number)
    if int(pack["season_stash_goal_met"]):
        return f"**{season.title()} reserve goal**; complete ({target}/{target}). Unity rewarded."
    return f"**{season.title()} reserve goal**; **{count}/{target}** carcasses deposited this season."
