"""Wolves fear open flame; campfires, torches, wildfire."""

from __future__ import annotations

import database as db
from engine.dice import format_roll_result, resolve_check
from engine.role_features import has_any_role


FIRE_WISDOM_DC = 12
FIRE_ENCOURAGE_DC = 14
FIRE_INTIMIDATE_DC = 15
WILDFIRE_SURVIVAL_DC = 15
FIRE_NEAR_FEET = 10
WILDFIRE_NEAR_FEET = 20


def is_frightened_of_fire(user) -> bool:
    return bool(int(user["frightened_fire"] if "frightened_fire" in user.keys() else 0))


def set_fire_frightened(user, frightened: bool) -> None:
    db.update_user_by_id(user["id"], frightened_fire=1 if frightened else 0)


def fire_fear_save(user, *, wildfire: bool = False, day: int) -> tuple[bool, str]:
    """Wisdom save vs open flame. Returns (passed, message)."""
    result = resolve_check(
        user,
        attr_keys=("attr_wis",),
        skill="Wisdom",
        dc=FIRE_WISDOM_DC,
        proficient=False,
        skill_key=None,
        game_day=day,
    )
    lines = [format_roll_result(result)]
    range_ft = WILDFIRE_NEAR_FEET if wildfire else FIRE_NEAR_FEET
    if result["success"]:
        set_fire_frightened(user, False)
        lines.append(
            f"No panic; you can act within **{range_ft} ft** of the flame, still wary."
        )
        return True, "\n".join(lines)

    if has_any_role(user, "guard"):
        last = int(user["last_fire_reroll_day"] if "last_fire_reroll_day" in user.keys() else 0)
        if last < day:
            db.update_user_by_id(user["id"], last_fire_reroll_day=day)
            reroll = resolve_check(
                user,
                attr_keys=("attr_wis",),
                skill="Wisdom",
                dc=FIRE_WISDOM_DC,
                proficient=False,
                skill_key=None,
                game_day=day,
            )
            lines.append("_Guard steadiness; one reroll:_")
            lines.append(format_roll_result(reroll))
            if reroll["success"]:
                set_fire_frightened(user, False)
                lines.append(f"You master the flame within **{range_ft} ft**.")
                return True, "\n".join(lines)

    set_fire_frightened(user, True)
    lines.append(
        "**Frightened**; cannot move closer to the fire; disadvantage on attacks and checks "
        "while flame is in sight. Flee beyond **30 ft** or wait until it is out."
    )
    if wildfire:
        lines.append(
            "_Wildfire doubles fear range and each round near it needs Survival/Constitution "
            f"DC **{WILDFIRE_SURVIVAL_DC}** or **1d4** heat damage (smoke)._"
        )
    return False, "\n".join(lines)


def encourage_through_fire(ally, target, *, day: int) -> tuple[bool, str]:
    result = resolve_check(
        ally,
        attr_keys=("attr_cha",),
        skill="Persuasion",
        dc=FIRE_ENCOURAGE_DC,
        proficient=False,
        skill_key="persuasion",
        game_day=day,
    )
    lines = [format_roll_result(result)]
    if not result["success"]:
        lines.append(f"**{target['wolf_name']}** still shakes at the flame.")
        return False, "\n".join(lines)
    set_fire_frightened(target, False)
    lines.append(
        f"**{ally['wolf_name']}**'s howl steadies **{target['wolf_name']}**; fear lifts for now."
    )
    return True, "\n".join(lines)


def stand_against_fire(user, *, day: int) -> tuple[bool, str]:
    result = resolve_check(
        user,
        attr_keys=("attr_cha",),
        skill="Intimidation",
        dc=FIRE_INTIMIDATE_DC,
        proficient=False,
        skill_key="intimidation",
        game_day=day,
    )
    lines = [format_roll_result(result)]
    if result["success"]:
        set_fire_frightened(user, False)
        lines.append("You ignore the flame for **1 round**; teeth bared at the light.")
        return True, "\n".join(lines)
    lines.append("The fire still owns your nerves.")
    return False, "\n".join(lines)


def wildfire_heat_save(user, *, day: int) -> tuple[bool, str, int]:
    import random

    result = resolve_check(
        user,
        attr_keys=("attr_con",),
        skill="Survival",
        dc=WILDFIRE_SURVIVAL_DC,
        proficient=False,
        skill_key="survival",
        game_day=day,
    )
    if result["success"]:
        return True, format_roll_result(result) + "\nSmoke stings but you keep breathing.", 0
    dmg = random.randint(1, 4)
    new_hp = max(0, int(user["hp"]) - dmg)
    db.set_user_conditions(user["discord_id"], hp=new_hp)
    return (
        False,
        format_roll_result(result) + f"\nSmoke sears the lungs; **−{dmg} HP**.",
        dmg,
    )
