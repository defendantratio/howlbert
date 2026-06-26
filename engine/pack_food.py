"""Shared pack food reserve; deposit, withdraw, and feed-all."""

from __future__ import annotations

import random

import database as db
from engine.conditions import apply_meal_energy
from engine.hunger import meal_hunger_gain
from engine.thirst import meal_thirst_gain
from engine.injury_effects import meal_blocked_by_injury
from engine.prey_items import is_cannibal_prey, prey_meta


def pack_treasury_pinch_line(pack_id: int) -> str:
    """Nudge when communal bones may not cover sunrise stipends."""
    pack = db.get_pack(pack_id)
    if not pack:
        return ""
    treasury = int(pack["treasury"])
    from config import DAILY_REWARD
    from utils.currency import format_bones

    if treasury >= DAILY_REWARD:
        return ""
    return (
        f"\n\n_Treasury pinch: **{format_bones(treasury)}** in communal bones "
        f"(stipends draw ~**{format_bones(DAILY_REWARD)}**+). "
        "Hunt tax, `/pack deposit`, or `/preypile` → **Leave for the den**._"
    )


def format_pack_stash_line(stack, current_day: int) -> str:
    meta = prey_meta(stack["prey_key"])
    from engine.prey_items import freshness_label

    fresh = freshness_label(
        stack["acquired_day"],
        current_day,
        stack["prey_key"],
        rotting=bool(stack["is_rotting"]),
    )
    return (
        f"`#{stack['id']}` **{meta['name']}**; "
        f"{stack['uses_left']}/{meta['uses']} uses · {fresh} · **den reserve**"
    )


def deposit_to_pack_stash(user, stack_id: int, *, pack_id: int, guild_id: int, day: int) -> tuple[bool, str]:
    stack = db.get_prey_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "You don't carry that carcass."
    if stack["uses_left"] <= 0:
        return False, "That carcass is picked clean."
    if stack["is_rotting"]:
        return (
            False,
            "Only **fresh** carcasses go in the den reserve; eat or `/salvage` this one first.",
        )

    db.add_pack_prey_stack(
        pack_id,
        stack["prey_key"],
        uses_left=stack["uses_left"],
        bone_value=stack["bone_value"],
        acquired_day=stack["acquired_day"],
        guild_id=guild_id,
        deposited_by=user["id"],
        is_rotting=int(stack["is_rotting"]),
    )
    db.remove_prey_stack(stack_id)
    meta = prey_meta(stack["prey_key"])
    msg = f"**{meta['name']}** added to the den food reserve (`/pack stash`)."
    from config import HUNTER_HEALER_TRIBUTE_STANDING
    from engine.role_privileges import is_hunter

    last_tribute = int(user["last_healer_tribute_day"] if "last_healer_tribute_day" in user.keys() else 0)
    if is_hunter(user) and last_tribute < day:
        db.adjust_pack_unity(pack_id, 1)
        db.update_user_by_id(user["id"], last_healer_tribute_day=day)
        db.adjust_wolf_standing_by_id(user["id"], HUNTER_HEALER_TRIBUTE_STANDING)
        msg += (
            "\n\n_Hunters feed the healer den: **+1 pack unity**, "
            f"**+{HUNTER_HEALER_TRIBUTE_STANDING} standing** (once per sunrise)._"
        )
    from engine.pack_season_goals import record_stash_deposit

    goal_line = record_stash_deposit(pack_id, day)
    if goal_line:
        msg += f"\n\n{goal_line}"
    from engine.cannibalism import cannibalism_public_exposure

    msg += cannibalism_public_exposure(user, stack["prey_key"], action="stash")
    msg += pack_treasury_pinch_line(pack_id)
    return True, msg


def withdraw_from_pack_stash(user, stack_id: int, *, pack_id: int) -> tuple[bool, str]:
    stack = db.get_pack_prey_stack(stack_id)
    if not stack or stack["pack_id"] != pack_id:
        return False, "That carcass isn't in your den reserve."
    if stack["uses_left"] <= 0:
        return False, "That reserve stack is empty."

    db.add_prey_stack(
        user["id"],
        stack["prey_key"],
        uses_left=stack["uses_left"],
        bone_value=stack["bone_value"],
        acquired_day=stack["acquired_day"],
        guild_id=stack["guild_id"],
        is_rotting=int(stack["is_rotting"]),
    )
    db.remove_pack_prey_stack(stack_id)
    meta = prey_meta(stack["prey_key"])
    return True, f"You drag **{meta['name']}** from the reserve into your hoard (`/prey`)."


def _pick_feed_stack(pack_id: int):
    stacks = db.get_pack_prey_stacks(pack_id)
    if not stacks:
        return None
    fresh = [s for s in stacks if not s["is_rotting"]]
    return (fresh or stacks)[0]


def _is_sick(wolf) -> bool:
    """Carrying an illness or in any non-healthy condition counts as sick."""
    keys = wolf.keys()
    disease = wolf["disease"] if "disease" in keys else None
    if disease:
        return True
    condition = wolf["condition"] if "condition" in keys else "healthy"
    return bool(condition) and condition != "healthy"


def _feed_priority(wolf) -> tuple[int, int]:
    """
    Lore feeding order (Fresh-kill custom): elders, pups, den-keepers, and sick
    wolves eat first, then hunters and yearlings. Within a tier the hungriest
    eat first so a short reserve reaches those who need it most.

    Returns a sort key; lower sorts (and eats) first.
    """
    from engine.aging import stage_for_age
    from engine.role_restrictions import wolf_role

    role = wolf_role(wolf)
    age_moons = int(wolf["age_months"]) if "age_months" in wolf.keys() else 24
    stage = stage_for_age(age_moons)

    eats_first = (
        role == "elder"
        or stage == "elder"
        or role == "pup"
        or stage == "pup"
        or role in ("caretaker", "caretaker_apprentice")
        or _is_sick(wolf)
    )
    tier = 0 if eats_first else 1
    hunger = int(wolf["hunger"]) if "hunger" in wolf.keys() and wolf["hunger"] is not None else 50
    return (tier, hunger)


def _feed_wolf_from_stack(wolf, stack) -> tuple[bool, str]:
    block = meal_blocked_by_injury(wolf)
    if block:
        return False, f"**{wolf['wolf_name']}**; {block}"

    meta = prey_meta(stack["prey_key"])
    new_hp, new_exhaustion, hp_gain = apply_meal_energy(wolf, stack["bone_value"])
    hunger_gain = meal_hunger_gain(stack["prey_key"])
    new_hunger = db.adjust_hunger(wolf["id"], hunger_gain)
    thirst_gain = meal_thirst_gain(stack["prey_key"])
    new_thirst = db.adjust_thirst(wolf["id"], thirst_gain)
    db.set_user_conditions(
        wolf["discord_id"],
        wolf_id=wolf["id"],
        hp=new_hp,
        exhaustion=new_exhaustion,
    )

    disease_note = ""
    if stack["is_rotting"]:
        import random
        from engine.disease_contract import try_rotting_meat_exposure
        from engine.prey_items import PREY_ROTTING_EAT_DISEASE_CHANCE

        if random.random() < PREY_ROTTING_EAT_DISEASE_CHANCE:
            note = try_rotting_meat_exposure(wolf)
            if note:
                disease_note = f" ({note})"

    uses_left = stack["uses_left"] - 1
    db.update_pack_prey_stack_uses(stack["id"], uses_left)

    old_exhaustion = int(wolf["exhaustion"]) if "exhaustion" in wolf.keys() else 0
    msg = f"**{wolf['wolf_name']}**; **{meta['label']}** +{hp_gain} HP, hunger **{new_hunger}**, thirst **{new_thirst}**"
    from engine.cannibalism import cannibalism_eat_consequences

    msg += cannibalism_eat_consequences(wolf, stack["prey_key"])
    if new_exhaustion < old_exhaustion:
        msg += f", exhaustion **{new_exhaustion}**"
    return True, msg + disease_note


def run_feedall(
    pack_id: int,
    day: int,
    *,
    caller=None,
    discord_admin: bool = False,
) -> tuple[bool, str, int]:
    """Feed every living packmate one use from the den reserve. Once per pack per sunrise."""
    pack = db.get_pack(pack_id)
    if not pack:
        return False, "Pack not found.", 0
    from engine.pack_leadership import PACK_BULK_ALPHA_ONLY_MSG, can_run_pack_bulk_action

    if caller and not can_run_pack_bulk_action(caller, pack, discord_admin=discord_admin):
        return False, PACK_BULK_ALPHA_ONLY_MSG, 0
    if int(pack["last_feedall_day"]) >= day:
        return False, "The den already shared a communal meal this sunrise.", 0

    members = db.get_pack_den_wolves(pack_id)
    if not members:
        return False, "No wolves in the den.", 0

    members = sorted(members, key=_feed_priority)

    fed = 0
    lines: list[str] = []
    served_wolf = False
    for wolf in members:
        stack = _pick_feed_stack(pack_id)
        if not stack:
            if fed == 0:
                pinch = pack_treasury_pinch_line(pack_id)
                return (
                    False,
                    "The food reserve is empty; `/pack stash deposit` first." + pinch,
                    0,
                )
            break
        if is_cannibal_prey(stack["prey_key"]):
            served_wolf = True
        ok, line = _feed_wolf_from_stack(wolf, stack)
        if ok:
            fed += 1
            lines.append(line)
        else:
            lines.append(line)

    if fed == 0:
        return False, "No packmate could eat from the reserve.", 0

    db.set_pack_feedall_day(pack_id, day)
    db.adjust_pack_unity(pack_id, 1)
    summary = "\n".join(lines[:12])
    if len(lines) > 12:
        summary += f"\n_…and {len(lines) - 12} more._"
    msg = f"**Communal feed**; **{fed}** wolf(s) ate from the reserve.\n{summary}"
    if served_wolf and caller:
        from engine.cannibalism import cannibalism_public_exposure

        msg += cannibalism_public_exposure(caller, "wolf_carcass", action="feedall")
    return True, msg, fed
