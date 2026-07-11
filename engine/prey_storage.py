"""Grant, eat, salvage, and rot prey carcasses in the hoard."""

from __future__ import annotations

import random

from engine.conditions import apply_meal_energy
from engine.injury_effects import meal_jaw_pain_note
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
    """Add a carcass to the wolf's hoard. returns stack id."""
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
            "fresh kills rot by type (3 to 8 sunrises); `/eat` before spoil · "
            "rotting → `/salvage` · `/checklist`"
        )
    return (
        "rot timers vary by carcass · `/eat` · `/drink` · `/bury` · `/preypile` · "
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
        "today's kill is **rotting**; the fresh-kill cache is for meat still good. "
        "`/eat` at gut-risk or `/salvage` for bones."
    )


def eat_prey_carcass(user, stack_id: int, *, day: int = 0) -> tuple[bool, str]:
    block = living_wolf_block(user)
    if block:
        return False, block

    jaw_note = meal_jaw_pain_note(user)
    stack = db.get_prey_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "you don't have that in your hoard."
    if stack["uses_left"] <= 0:
        return False, "that's already picked clean."

    meta = prey_meta(stack["prey_key"])
    old_hunger = int(user["hunger"]) if "hunger" in user.keys() else 0
    old_exhaustion_pre_meal = int(user["exhaustion"]) if "exhaustion" in user.keys() else 0
    new_hp, new_exhaustion, hp_gain = apply_meal_energy(user, stack["bone_value"])
    hunger_gain = meal_hunger_gain(stack["prey_key"])
    new_hunger = db.adjust_hunger(user["id"], hunger_gain)
    thirst_gain = meal_thirst_gain(stack["prey_key"])
    new_thirst = db.adjust_thirst(user["id"], thirst_gain)
    overfull_note = ""
    if old_hunger >= 100:
        from engine.exhaustion_effects import PAIN_EXHAUSTION_MAX as _PE_MAX
        old_pe = int(user["pain_exhaustion"]) if "pain_exhaustion" in user.keys() else 0
        new_pe = min(_PE_MAX, old_pe + 1)
        db.update_user(user["discord_id"], wolf_id=user["id"], pain_exhaustion=new_pe)
        overfull_note = "\n_gut already full; forcing it down adds **+1 pain exhaustion**._"
        from engine.disease_contract import try_contract_disease

        bloat_note = try_contract_disease(user, "bloat", "distension", chance=0.05)
        if bloat_note:
            overfull_note += f"\n{bloat_note}"
    db.set_user_conditions(
        user["discord_id"],
        wolf_id=user["id"],
        hp=new_hp,
        exhaustion=new_exhaustion,
    )
    if new_exhaustion < old_exhaustion_pre_meal:
        from engine.energy import gain_energy_from_exhaustion_relief
        gain_energy_from_exhaustion_relief(user, old_exhaustion_pre_meal - new_exhaustion)

    from engine.prey_items import is_forage_food

    forage = is_forage_food(stack["prey_key"])

    # meat resets the meatless-wasting clock; forage/liquids do not (carnivores
    # need real prey; see meatless wasting at rollover)
    if not forage and day:
        db.update_user(user["discord_id"], wolf_id=user["id"], last_meat_day=day)

    disease_note = ""
    if stack["is_rotting"]:
        if forage:
            disease_note = "\n_the fruit is **overripe**, fermented and sour; your gut churns._"
            from engine.disease_contract import try_contract_disease

            if random.random() < 0.15:
                note = try_contract_disease(user, "diarrhea", chance=1.0)
                if note:
                    disease_note += f"\n{note}"
        else:
            from engine.disease_contract import try_rotting_meat_exposure
            from engine.prey_items import PREY_ROTTING_EAT_DISEASE_CHANCE

            disease_note = "\n_you choke down **rotting** flesh; gut twists._"
            if random.random() < PREY_ROTTING_EAT_DISEASE_CHANCE:
                note = try_rotting_meat_exposure(user)
                if note:
                    disease_note += f"\n{note}"
    elif not forage:
        from engine.disease_contract import try_contract_disease

        if random.random() < 0.03:
            note = try_contract_disease(user, "worms", "mild_burden", chance=1.0)
            if note:
                disease_note += f"\n{note}"

    uses_left = stack["uses_left"] - 1
    if uses_left <= 0:
        db.remove_prey_stack(stack_id)
        uses_note = "it's all gone." if forage else "the carcass is finished."
    else:
        unit = "this forage" if forage else "this carcass"
        db.update_prey_stack_uses(stack_id, uses_left)
        uses_note = f"**{uses_left}** uses left on {unit}."

    old_exhaustion = int(user["exhaustion"]) if "exhaustion" in user.keys() else 0
    verb = "graze on" if forage else "tear into"
    msg = (
        f"you {verb} **{meta['label']}**; +{hp_gain} hp, "
        f"hunger **{new_hunger}** (+{hunger_gain}), hydration **{new_thirst}** (+{thirst_gain})"
    )
    from engine.cannibalism import cannibalism_eat_consequences

    msg += cannibalism_eat_consequences(user, stack["prey_key"])
    if new_exhaustion < old_exhaustion:
        msg += f", exhaustion **{new_exhaustion}** (−{old_exhaustion - new_exhaustion})"
    msg += f".\n{uses_note}{disease_note}{overfull_note}{jaw_note}"
    return True, msg


def salvage_prey_carcass(user, stack_id: int) -> tuple[bool, str, int]:
    stack = db.get_prey_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "you don't carry that carcass.", 0
    from engine.prey_items import is_forage_food

    if is_forage_food(stack["prey_key"]):
        return False, "spoiled forage rots to mush; there's nothing to salvage. `/bury` it instead.", 0
    if not stack["is_rotting"]:
        return False, "only **rotting** carcasses can be salvaged; eat them fresh or wait.", 0

    bones = salvage_bones(stack["prey_key"], stack["uses_left"], stack["bone_value"])
    db.remove_prey_stack(stack_id)
    db.add_bones(user["discord_id"], bones, wolf_id=user["id"])
    meta = prey_meta(stack["prey_key"])
    return True, f"salvaged **{meta['name']}** into **{bones}** bones.", bones
