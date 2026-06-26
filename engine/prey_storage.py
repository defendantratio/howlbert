"""Grant, eat, salvage, and rot prey carcasses in the hoard."""

from __future__ import annotations

import random

from engine.conditions import apply_meal_energy
from engine.injury_effects import meal_blocked_by_injury
from engine.vitals import living_wolf_block
from engine.hunger import meal_hunger_gain
from engine.thirst import meal_thirst_gain
from engine.prey_items import (
    prey_key_from_hunt_amount,
    prey_meta,
    freshness_label,
    salvage_bones,
)
import database as db


def grant_prey_carcass(
    wolf_id: int,
    prey_key: str,
    *,
    guild_id: int,
    acquired_day: int,
    bone_value: int | None = None,
) -> int:
    """Add a carcass to the wolf's hoard. Returns stack id."""
    meta = prey_meta(prey_key)
    bones = bone_value if bone_value is not None else meta["bones"]
    return db.add_prey_stack(
        wolf_id,
        prey_key,
        uses_left=meta["uses"],
        bone_value=bones,
        acquired_day=acquired_day,
        guild_id=guild_id,
    )


def grant_prey_from_hunt(
    wolf_id: int,
    *,
    guild_id: int,
    day: int,
    bone_value: int,
    prey_key: str | None = None,
) -> tuple[int, str]:
    key = prey_key or prey_key_from_hunt_amount(bone_value)
    stack_id = grant_prey_carcass(
        wolf_id,
        key,
        guild_id=guild_id,
        acquired_day=day,
        bone_value=bone_value,
    )
    return stack_id, prey_meta(key)["name"]


def format_prey_hoard_line(stack, current_day: int) -> str:
    meta = prey_meta(stack["prey_key"])
    fresh = freshness_label(
        stack["acquired_day"],
        current_day,
        stack["prey_key"],
        rotting=bool(stack["is_rotting"]),
    )
    return (
        f"`#{stack['id']}` **{meta['name']}**; "
        f"{stack['uses_left']}/{meta['uses']} uses · {fresh}"
    )


def format_prey_hoard_footer(*, empty: bool = False) -> str:
    if empty:
        return (
            "Fresh kills rot by type (3–8 sunrises); `/eat` before spoil · "
            "rotting → `/salvage` · `/world action:cooldowns`"
        )
    return (
        "Rot timers vary by carcass · `/eat` · `/drink` · `/bury` · `/preypile` · "
        "rotting → `/salvage` · `/pack stash deposit`"
    )


def fresh_kill_pile_block_message(wolf_id: int, day: int) -> str | None:
    """Return a player-facing error when fresh-kill cache cannot be opened."""
    stacks = db.get_todays_prey_stacks(wolf_id, day)
    if not stacks:
        return None
    if any(not s["is_rotting"] for s in stacks):
        return None
    return (
        "Today's kill is **rotting**; the fresh-kill cache is for meat still good. "
        "`/eat` at gut-risk or `/salvage` for bones."
    )


def eat_prey_carcass(user, stack_id: int) -> tuple[bool, str]:
    block = living_wolf_block(user)
    if block:
        return False, block
    block = meal_blocked_by_injury(user)
    if block:
        return False, block

    stack = db.get_prey_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "You don't carry that carcass."
    if stack["uses_left"] <= 0:
        return False, "That carcass is picked clean."

    meta = prey_meta(stack["prey_key"])
    new_hp, new_exhaustion, hp_gain = apply_meal_energy(user, stack["bone_value"])
    hunger_gain = meal_hunger_gain(stack["prey_key"])
    new_hunger = db.adjust_hunger(user["id"], hunger_gain)
    thirst_gain = meal_thirst_gain(stack["prey_key"])
    new_thirst = db.adjust_thirst(user["id"], thirst_gain)
    db.set_user_conditions(
        user["discord_id"],
        wolf_id=user["id"],
        hp=new_hp,
        exhaustion=new_exhaustion,
    )

    from engine.prey_items import is_forage_food

    forage = is_forage_food(stack["prey_key"])

    disease_note = ""
    if stack["is_rotting"]:
        if forage:
            disease_note = "\n_The fruit is **overripe**, fermented and sour; your gut churns._"
            from engine.disease_contract import try_contract_disease

            if random.random() < 0.15:
                note = try_contract_disease(user, "diarrhea", chance=1.0)
                if note:
                    disease_note += f"\n{note}"
        else:
            from engine.disease_contract import try_rotting_meat_exposure
            from engine.prey_items import PREY_ROTTING_EAT_DISEASE_CHANCE

            disease_note = "\n_You choke down **rotting** flesh; gut twists._"
            if random.random() < PREY_ROTTING_EAT_DISEASE_CHANCE:
                note = try_rotting_meat_exposure(user)
                if note:
                    disease_note += f"\n{note}"

    uses_left = stack["uses_left"] - 1
    if uses_left <= 0:
        db.remove_prey_stack(stack_id)
        uses_note = "It's all gone." if forage else "The carcass is finished."
    else:
        unit = "this forage" if forage else "this carcass"
        db.update_prey_stack_uses(stack_id, uses_left)
        uses_note = f"**{uses_left}** uses left on {unit}."

    old_exhaustion = int(user["exhaustion"]) if "exhaustion" in user.keys() else 0
    verb = "graze on" if forage else "tear into"
    msg = (
        f"You {verb} **{meta['label']}**; +{hp_gain} HP, "
        f"hunger **{new_hunger}** (+{hunger_gain}), thirst **{new_thirst}** (+{thirst_gain})"
    )
    from engine.cannibalism import cannibalism_eat_consequences

    msg += cannibalism_eat_consequences(user, stack["prey_key"])
    if new_exhaustion < old_exhaustion:
        msg += f", exhaustion **{new_exhaustion}** (−{old_exhaustion - new_exhaustion})"
    msg += f".\n{uses_note}{disease_note}"
    return True, msg


def salvage_prey_carcass(user, stack_id: int) -> tuple[bool, str, int]:
    stack = db.get_prey_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "You don't carry that carcass.", 0
    from engine.prey_items import is_forage_food

    if is_forage_food(stack["prey_key"]):
        return False, "Spoiled forage rots to mush; there's nothing to salvage. `/bury` it instead.", 0
    if not stack["is_rotting"]:
        return False, "Only **rotting** carcasses can be salvaged; eat them fresh or wait.", 0

    bones = salvage_bones(stack["prey_key"], stack["uses_left"], stack["bone_value"])
    db.remove_prey_stack(stack_id)
    db.add_bones(user["discord_id"], bones, wolf_id=user["id"])
    meta = prey_meta(stack["prey_key"])
    return True, f"Salvaged **{meta['name']}** into **{bones}** bones.", bones
