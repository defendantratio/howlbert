"""Pack howl, group checks, and assisted rolls."""

from __future__ import annotations

import random

from engine.dice import format_roll_result, resolve_check
from engine.character import is_skill_proficient


def pack_howl_range(charisma_roll: int, pack_size: int, *, natural_20: bool) -> int:
    """Highest Charisma roll sets range; +1 per 3 wolves; nat 20 doubles."""
    bonus = pack_size // 3
    base = charisma_roll + bonus
    return base * 2 if natural_20 else base


def run_group_check(
    wolves: list,
    *,
    dc: int,
    attr_keys: tuple[str, ...],
    skill_key: str,
    skill_label: str,
    day: int,
) -> tuple[bool, str]:
    if not wolves:
        return False, "no wolves in the group."
    results = []
    successes = 0
    for wolf in wolves:
        proficient = is_skill_proficient(wolf, skill_key)
        roll = resolve_check(
            wolf,
            attr_keys=attr_keys,
            skill=skill_label,
            dc=dc,
            proficient=proficient,
            skill_key=skill_key,
            game_day=day,
        )
        if roll["success"]:
            successes += 1
        results.append(f"**{wolf['wolf_name']}**: {roll['total']} vs dc {dc} ({'ok' if roll['success'] else 'fail'})")
    needed = (len(wolves) + 1) // 2
    ok = successes >= needed
    header = f"group check; **{successes}/{len(wolves)}** succeeded (need **{needed}**)."
    return ok, header + "\n" + "\n".join(results)


def run_assisted_check(
    primary,
    helper,
    *,
    dc: int,
    attr_keys: tuple[str, ...],
    skill_key: str,
    skill_label: str,
    day: int,
) -> tuple[bool, str]:
    help_roll = resolve_check(
        helper,
        attr_keys=attr_keys,
        skill=skill_label,
        dc=10,
        proficient=False,
        skill_key=skill_key,
        game_day=day,
    )
    advantage = help_roll["success"] and help_roll["die"] != 1
    if advantage:
        r1 = resolve_check(
            primary,
            attr_keys=attr_keys,
            skill=skill_label,
            dc=dc,
            proficient=False,
            skill_key=skill_key,
            game_day=day,
        )
        r2 = resolve_check(
            primary,
            attr_keys=attr_keys,
            skill=skill_label,
            dc=dc,
            proficient=False,
            skill_key=skill_key,
            game_day=day,
        )
        primary_roll = r1 if r1["total"] >= r2["total"] else r2
        assist_note = "_assisted; primary took the higher of two rolls._"
    else:
        primary_roll = resolve_check(
            primary,
            attr_keys=attr_keys,
            skill=skill_label,
            dc=dc,
            proficient=False,
            skill_key=skill_key,
            game_day=day,
        )
        assist_note = ""
    lines = [
        f"helper **{helper['wolf_name']}**: {format_roll_result(help_roll)}",
        f"primary **{primary['wolf_name']}**: {format_roll_result(primary_roll)}",
    ]
    if help_roll["die"] == 1:
        lines.append("_helper fumbled; no advantage._")
    elif assist_note:
        lines.append(assist_note)
    ok = primary_roll["success"]
    return ok, "\n".join(lines)
