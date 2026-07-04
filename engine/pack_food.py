"""Shared pack food reserve; deposit, withdraw, and feed-all."""

from __future__ import annotations

import random

import database as db
from engine.conditions import apply_meal_energy
from engine.hunger import meal_hunger_gain
from engine.thirst import meal_thirst_gain
from engine.injury_effects import meal_blocked_by_injury, meal_jaw_pain_note
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
        f"\n\n_treasury pinch: **{format_bones(treasury)}** in communal bones "
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
        return False, "you don't have that in your hoard."
    if stack["uses_left"] <= 0:
        return False, "that's already picked clean."
    if stack["is_rotting"]:
        return (
            False,
            "only **fresh** food goes in the den reserve; eat or `/salvage` this one first.",
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

    season = db.get_world(guild_id)["season"]
    goal_line = record_stash_deposit(pack_id, season)
    if goal_line:
        msg += f"\n\n{goal_line}"
    from engine.cannibalism import cannibalism_public_exposure

    msg += cannibalism_public_exposure(user, stack["prey_key"], action="stash")
    msg += pack_treasury_pinch_line(pack_id)
    return True, msg


def deposit_all_to_pack_stash(user, *, pack_id: int, guild_id: int, day: int) -> tuple[int, str]:
    """Deposit all fresh personal prey stacks to the den reserve. Returns (count, message)."""
    stacks = db.get_prey_stacks(user["id"])
    fresh = [s for s in stacks if int(s["uses_left"] or 0) > 0 and not int(s["is_rotting"] or 0)]
    if not fresh:
        return 0, "nothing fresh in your hoard to deposit."

    names: list[str] = []
    for stack in fresh:
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
        db.remove_prey_stack(stack["id"])
        meta = prey_meta(stack["prey_key"])
        names.append(meta["name"])

    count = len(fresh)
    name_list = ", ".join(f"**{n}**" for n in names)
    msg = f"{count} item{'s' if count > 1 else ''} added to the den food reserve: {name_list}."

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

    season = db.get_world(guild_id)["season"]
    goal_line = None
    for _ in range(count):
        goal_line = record_stash_deposit(pack_id, season)
    if goal_line:
        msg += f"\n\n{goal_line}"

    msg += pack_treasury_pinch_line(pack_id)
    return count, msg


def withdraw_from_pack_stash(user, stack_id: int, *, pack_id: int) -> tuple[bool, str]:
    stack = db.get_pack_prey_stack(stack_id)
    if not stack or stack["pack_id"] != pack_id:
        return False, "that isn't in your den reserve."
    if stack["uses_left"] <= 0:
        return False, "that reserve stack is empty."

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
    return True, f"you drag **{meta['name']}** from the reserve into your hoard (`/food`)."


def _pick_feed_stack(pack_id: int):
    stacks = db.get_pack_prey_stacks(pack_id)
    if not stacks:
        return None
    fresh = [s for s in stacks if not s["is_rotting"]]
    return (fresh or stacks)[0]


def _is_sick(wolf) -> bool:
    """carrying an illness or in any non-healthy condition counts as sick."""
    keys = wolf.keys()
    disease = wolf["disease"] if "disease" in keys else None
    if disease:
        return True
    condition = wolf["condition"] if "condition" in keys else "healthy"
    return bool(condition) and condition != "healthy"


def _feed_priority(wolf) -> tuple[int, int]:
    """
    lore feeding order (fresh-kill custom): elders, pups, den-keepers, and sick
    wolves eat first, then hunters and yearlings. within a tier the hungriest
    eat first so a short reserve reaches those who need it most.

    returns a sort key; lower sorts (and eats) first.
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
    # Won rank disputes nudge a wolf earlier in line among similarly-hungry
    # packmates (real pecking order), without letting rank override genuine
    # survival need the way hunger itself does.
    pack_rank = int(wolf["pack_rank"]) if "pack_rank" in wolf.keys() and wolf["pack_rank"] is not None else 0
    adjusted_hunger = hunger + pack_rank * 3
    return (tier, adjusted_hunger)


def _feed_wolf_from_stack(wolf, stack, *, day: int = 0) -> tuple[bool, str]:
    jaw_note = meal_jaw_pain_note(wolf)
    from engine.prey_items import is_forage_food
    if day and not is_forage_food(stack["prey_key"]):
        db.update_user(wolf["discord_id"], wolf_id=wolf["id"], last_meat_day=day)
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
        from engine.disease_contract import try_rotting_meat_exposure
        from engine.prey_items import PREY_ROTTING_EAT_DISEASE_CHANCE

        if random.random() < PREY_ROTTING_EAT_DISEASE_CHANCE:
            note = try_rotting_meat_exposure(wolf)
            if note:
                disease_note = f" ({note})"

    uses_left = stack["uses_left"] - 1
    db.update_pack_prey_stack_uses(stack["id"], uses_left)

    old_exhaustion = int(wolf["exhaustion"]) if "exhaustion" in wolf.keys() else 0
    msg = f"**{wolf['wolf_name']}**; **{meta['label']}** +{hp_gain} hp, hunger **{new_hunger}**, thirst **{new_thirst}**"
    from engine.cannibalism import cannibalism_eat_consequences

    msg += cannibalism_eat_consequences(wolf, stack["prey_key"])
    if new_exhaustion < old_exhaustion:
        msg += f", exhaustion **{new_exhaustion}**"
    return True, msg + disease_note + jaw_note


def _passive_forage_chance(wolf, season: str | None) -> float:
    """
    odds a hungry wolf scrapes together enough food on its own at sunrise.
    wolves are facultative carnivores; berries, roots, fallen fruit, and
    scavenged scraps tide them over. foragers and scouts do best; pups, the
    injured, elders, and winter do worst, so starvation stays a real risk.
    """
    from config import ROLLOVER_SCAVENGE_BASE_CHANCE
    from engine.aging import stage_for_age
    from engine.role_restrictions import wolf_role

    chance = ROLLOVER_SCAVENGE_BASE_CHANCE

    role = wolf_role(wolf)
    role_mod = {
        "forager": 0.20,
        "forager_apprentice": 0.14,
        "scout": 0.12,
        "scout_apprentice": 0.08,
        "hunter": 0.08,
        "hunter_apprentice": 0.05,
        "bog_born": 0.10,
        "lowbelly": 0.06,
        "elder": -0.15,
        "juvenile": -0.10,
        "pup": -0.35,
        "drown_sick": -0.05,
    }.get(role, 0.0)
    chance += role_mod

    age_moons = int(wolf["age_months"]) if "age_months" in wolf.keys() else 24
    stage = stage_for_age(age_moons)
    if stage == "pup" and role != "pup":
        chance -= 0.30
    elif stage == "elder" and role != "elder":
        chance -= 0.10

    if _is_sick(wolf):
        chance -= 0.20

    season_mod = {
        "spring": 0.05,
        "summer": 0.10,
        "autumn": 0.15,
        "winter": -0.30,
    }.get((season or "").lower(), 0.0)
    chance += season_mod

    return max(0.05, min(0.95, chance))


def auto_feed_wolves_on_rollover(conn, day: int, season: str | None = None) -> list[dict]:
    """
    Sunrise feeding, two stages:

    1. Each pack feeds its living members from its food reserve in lore order
       (elders, pups, den-keepers, and sick wolves first), consuming stored prey.
    2. Any still-hungry wolf with nothing left in the reserve forages/scavenges
       for itself. The roll is modified by role, life stage, illness, and season;
       it usually succeeds but CAN fail, so neglect and bad seasons still starve
       the vulnerable. No magic floor; hunts and a stocked den still matter.

    Operates entirely on the given connection so it never opens a second
    connection (which would deadlock against the rollover transaction).
    """
    from config import (
        HUNGER_LOW_THRESHOLD,
        HUNGER_MAX,
        ROLLOVER_SCAVENGE_HUNGER,
        ROLLOVER_SCAVENGE_THIRST,
        THIRST_LOW_THRESHOLD,
        THIRST_MAX,
    )
    from engine.hunger import meal_hunger_gain
    from engine.thirst import meal_thirst_gain

    notes: list[dict] = []
    fed_from_reserve: set[int] = set()

    pack_ids = [r["id"] for r in conn.execute("SELECT id FROM packs").fetchall()]
    for pack_id in pack_ids:
        members = conn.execute(
            """
            SELECT * FROM users
            WHERE pack_id = ? AND condition NOT IN ('dead', 'dying')
            """,
            (pack_id,),
        ).fetchall()
        if not members:
            continue
        members = sorted(members, key=_feed_priority)

        stacks = conn.execute(
            """
            SELECT * FROM pack_prey_stacks
            WHERE pack_id = ? AND uses_left > 0
            ORDER BY is_rotting ASC, acquired_day DESC, id DESC
            """,
            (pack_id,),
        ).fetchall()
        reserve = [[s, int(s["uses_left"])] for s in stacks]
        ri = 0

        for wolf in members:
            hunger = int(wolf["hunger"]) if wolf["hunger"] is not None else 0
            thirst = int(wolf["thirst"]) if wolf["thirst"] is not None else 0
            if hunger >= HUNGER_MAX and thirst >= THIRST_MAX:
                continue
            while ri < len(reserve) and reserve[ri][1] <= 0:
                ri += 1
            if ri >= len(reserve):
                break
            stack = reserve[ri][0]
            reserve[ri][1] -= 1
            new_hunger = min(HUNGER_MAX, hunger + meal_hunger_gain(stack["prey_key"]))
            new_thirst = min(THIRST_MAX, thirst + meal_thirst_gain(stack["prey_key"]))
            from engine.prey_items import is_forage_food
            if is_forage_food(stack["prey_key"]):
                conn.execute(
                    "UPDATE users SET hunger = ?, thirst = ? WHERE id = ?",
                    (new_hunger, new_thirst, wolf["id"]),
                )
            else:
                conn.execute(
                    "UPDATE users SET hunger = ?, thirst = ?, last_meat_day = ? WHERE id = ?",
                    (new_hunger, new_thirst, day, wolf["id"]),
                )
            fed_from_reserve.add(int(wolf["id"]))

        for stack, left in reserve:
            if left == int(stack["uses_left"]):
                continue
            if left <= 0:
                conn.execute("DELETE FROM pack_prey_stacks WHERE id = ?", (stack["id"],))
            else:
                conn.execute(
                    "UPDATE pack_prey_stacks SET uses_left = ? WHERE id = ?",
                    (left, stack["id"]),
                )

    # Stage 2: wolves the reserve couldn't reach forage/scavenge for themselves.\n    hungry = conn.execute(\n        """\n        SELECT * FROM users\n        WHERE condition NOT IN ('dead', 'dying')\n          AND (hunger < ? OR thirst < ?)\n        """,\n        (HUNGER_LOW_THRESHOLD, THIRST_LOW_THRESHOLD),\n    ).fetchall()\n\n    for wolf in hungry:\n        if int(wolf["id"]) in fed_from_reserve:\n            continue\n        if random.random() > _passive_forage_chance(wolf, season):\n            continue  # foraging failed; the wolf goes hungry and stakes hold\n        hunger = int(wolf["hunger"]) if wolf["hunger"] is not None else 0\n        thirst = int(wolf["thirst"]) if wolf["thirst"] is not None else 0\n        # A successful forage gets the wolf by: at least a sustainable level (so\n        # it isn't slowly killed by exhaustion despite foraging), plus a little
        # more if it was already close. It does not let a wolf thrive; only real
        # meals (hunts, a stocked reserve) push vitals high.
        if hunger < HUNGER_LOW_THRESHOLD:
            new_hunger = min(HUNGER_MAX, max(HUNGER_LOW_THRESHOLD, hunger + ROLLOVER_SCAVENGE_HUNGER))
        else:
            new_hunger = hunger
        if thirst < THIRST_LOW_THRESHOLD:
            new_thirst = min(THIRST_MAX, max(THIRST_LOW_THRESHOLD, thirst + ROLLOVER_SCAVENGE_THIRST))
        else:
            new_thirst = thirst
        conn.execute(
            "UPDATE users SET hunger = ?, thirst = ? WHERE id = ?",
            (new_hunger, new_thirst, wolf["id"]),
        )
        notes.append({
            "wolf_name": wolf["wolf_name"],
            "discord_id": int(wolf["discord_id"]),
            "line": "foraged for themselves (reserve ran short).",
        })

    return notes


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
        return False, "pack not found.", 0
    from engine.pack_leadership import PACK_BULK_ALPHA_ONLY_MSG, can_run_pack_bulk_action

    if caller and not can_run_pack_bulk_action(caller, pack, discord_admin=discord_admin):
        return False, PACK_BULK_ALPHA_ONLY_MSG, 0
    if int(pack["last_feedall_day"]) >= day:
        return False, "the den already shared a communal meal this sunrise.", 0

    members = db.get_pack_den_wolves(pack_id)
    if not members:
        return False, "no wolves in the den.", 0

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
                    "the food reserve is empty; `/pack stash deposit` first." + pinch,
                    0,
                )
            break
        if is_cannibal_prey(stack["prey_key"]):
            served_wolf = True
        ok, line = _feed_wolf_from_stack(wolf, stack, day=day)
        if ok:
            fed += 1
            lines.append(line)
        else:
            lines.append(line)

    if fed == 0:
        return False, "no packmate could eat from the reserve.", 0

    db.set_pack_feedall_day(pack_id, day)
    db.adjust_pack_unity(pack_id, 1)
    summary = "\n".join(lines[:12])
    if len(lines) > 12:
        summary += f"\n_…and {len(lines) - 12} more._"
    msg = f"**communal feed**; **{fed}** wolf(s) ate from the reserve.\n{summary}"
    if served_wolf and caller:
        from engine.cannibalism import cannibalism_public_exposure

        msg += cannibalism_public_exposure(caller, "wolf_carcass", action="feedall")
    return True, msg, fed
