"""Per-season pack food-reserve goals; deposit carcasses for unity."""

from __future__ import annotations

import database as db
from config import SEASONS

SEASON_STASH_TARGETS = {
    "spring": 4,
    "summer": 5,
    "autumn": 6,
    "winter": 5,
}
SEASON_STASH_UNITY_REWARD = 2


def stash_goal_target(season: str) -> int:
    return SEASON_STASH_TARGETS.get(season, 5)


def _sync_pack_epoch(pack, season: str) -> None:
    epoch = SEASONS.index(season) if season in SEASONS else 0
    stored = int(pack["season_goal_epoch"]) if "season_goal_epoch" in pack.keys() else -1
    if stored == epoch:
        return
    db.update_pack_season_goal(
        pack["id"],
        season_goal_epoch=epoch,
        season_stash_deposits=0,
        season_stash_goal_met=0,
    )


def record_stash_deposit(pack_id: int, season: str) -> str | None:
    """Increment seasonal stash counter; return celebration line if goal just met."""
    pack = db.get_pack(pack_id)
    if not pack:
        return None
    _sync_pack_epoch(pack, season)
    pack = db.get_pack(pack_id)
    if not pack:
        return None

    if int(pack["season_stash_goal_met"]):
        return None

    target = stash_goal_target(season)
    new_count = int(pack["season_stash_deposits"]) + 1
    db.update_pack_season_goal(pack_id, season_stash_deposits=new_count)

    if new_count < target:
        return None

    db.update_pack_season_goal(pack_id, season_stash_goal_met=1)
    outcome = db.adjust_pack_unity(pack_id, SEASON_STASH_UNITY_REWARD)
    line = (
        f"**season goal met!** the den filled the **{season}** reserve "
        f"({target} carcasses); pack unity **+{SEASON_STASH_UNITY_REWARD}**."
    )
    if outcome == "dissolved":
        line += " _(The pack fractured anyway; unity hit the dissolve threshold.)_"
    return line


def format_stash_goal_line(pack, season: str) -> str:
    _sync_pack_epoch(pack, season)
    pack = db.get_pack(pack["id"])
    if not pack:
        return ""
    target = stash_goal_target(season)
    count = int(pack["season_stash_deposits"])
    if int(pack["season_stash_goal_met"]):
        return f"**{season.title()} reserve goal**; complete ({target}/{target}). unity rewarded."
    return f"**{season.title()} reserve goal**; **{count}/{target}** carcasses deposited this season."
