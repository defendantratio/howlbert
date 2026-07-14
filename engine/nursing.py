"""Mothers nurse pups; caretakers can offer nursery mash when needed."""

from __future__ import annotations

import database as db
from config import (
    CARETAKER_MASH_HUNGER_GAIN,
    CARETAKER_MASH_THIRST_GAIN,
    HONEY_PUP_EXHAUSTION_RELIEF,
    HONEY_PUP_HUNGER_BONUS,
    HUNGER_CRITICAL_THRESHOLD,
    HUNGER_LOW_THRESHOLD,
    HUNGER_MAX,
    MILK_HUNGER_GAIN,
    MILK_THIRST_GAIN,
    MOTHER_NURSE_HUNGER_COST_PER_PUP,
    PUP_MAX_MOONS,
    THIRST_MAX,
)
from engine.aging import stage_for_age
from engine.role_features import has_any_role


def is_nursery_caretaker(user) -> bool:
    return has_any_role(user, "caretaker", "caretaker_apprentice")


def is_nursing_mother(user) -> bool:
    if not user:
        return False
    sex = user["birth_sex"] if "birth_sex" in user.keys() else None
    if sex != "female":
        return False
    return bool(db.get_nursing_pups_for_mother(user["id"]))


def is_weaning_pup(user) -> bool:
    if not user:
        return False
    if user["condition"] in ("dead", "dying"):
        return False
    age = int(user["age_months"] if "age_months" in user.keys() else 24)
    return stage_for_age(age) == "pup"


def pup_needs_milk_today(pup, day_number: int) -> bool:
    if not is_weaning_pup(pup):
        return False
    last = int(pup["last_milk_day"] if "last_milk_day" in pup.keys() else 0)
    return last < day_number


def pup_fed_today(pup, day_number: int) -> bool:
    if not is_weaning_pup(pup):
        return False
    last = int(pup["last_milk_day"] if "last_milk_day" in pup.keys() else 0)
    return last >= day_number


def lone_nursing_note(mother) -> str:
    if mother and mother["pack_id"]:
        return ""
    return (
        " **lone mothers** have no pack caretaker; nurse daily or use **honey** "
        "(`/medic action:treat` on the pup, or carry honey when nursing)."
    )


def _clamp_hunger(value: int) -> int:
    return max(0, min(HUNGER_MAX, value))


def _clamp_thirst(value: int) -> int:
    return max(0, min(THIRST_MAX, value))


def _filter_pups(pups: list, pup_name: str | None):
    if not pup_name:
        return pups
    key = pup_name.strip().lower()
    return [p for p in pups if p["wolf_name"].lower() == key]


def _try_consume_feeder_honey(feeder) -> bool:
    item = db.get_item_by_key("honey")
    if not item:
        return False
    if db.get_inventory_quantity_for_wolf(feeder["id"], item["id"]) < 1:
        return False
    return db.consume_item_for_wolf(feeder["id"], item["id"], 1)


def _pup_hunger_bonus_fields(pup, hunger_gain: int, *, day_number: int | None = None) -> dict:
    new_hunger = _clamp_hunger(int(pup["hunger"]) + hunger_gain)
    fields: dict = {"hunger": new_hunger}
    if int(pup["hunger"]) < HUNGER_LOW_THRESHOLD and int(
        pup["exhaustion"] if "exhaustion" in pup.keys() else 0
    ) > 0:
        old_ex = int(pup["exhaustion"])
        fields["exhaustion"] = max(0, old_ex - HONEY_PUP_EXHAUSTION_RELIEF)
        relieved = old_ex - fields["exhaustion"]
        if relieved > 0:
            from engine.energy import gain_energy_from_exhaustion_relief
            gain_energy_from_exhaustion_relief(pup, relieved)
    if day_number is not None:
        fields["last_milk_day"] = day_number
    return fields




def _feed_pups_with_gains(
    pups: list,
    *,
    hunger_gain: int,
    thirst_gain: int,
    day_number: int,
    honey_used: bool,
    feeder_id: int | None = None,
) -> list[str]:
    from engine.long_term_injuries import parse_long_term_injuries

    fed: list[str] = []
    bonus = HONEY_PUP_HUNGER_BONUS if honey_used else 0
    for pup in pups:
        total_hunger = hunger_gain + bonus
        fields = _pup_hunger_bonus_fields(pup, total_hunger)
        fields["thirst"] = _clamp_thirst(int(pup["thirst"]) + thirst_gain)
        was_unfed = int(pup["last_milk_day"] if "last_milk_day" in pup.keys() else 0) == 0
        fields["last_milk_day"] = day_number
        db.update_user_by_id(pup["id"], **fields)
        fed.append(pup["wolf_name"])
        if (
            feeder_id
            and was_unfed
            and "runt" in parse_long_term_injuries(
                pup["long_term_injuries"] if "long_term_injuries" in pup.keys() else None
            )
        ):
            from engine.family import grant_runt_first_feed_bond

            grant_runt_first_feed_bond(feeder_id, pup["id"], day=day_number)
    return fed


def _honey_suffix(honey_used: bool) -> str:
    if not honey_used:
        return ""
    return (
        f" **honey** sweetens the meal (**+{HONEY_PUP_HUNGER_BONUS}** satiety per pup; "
        "starving pups shed **1** exhaustion)."
    )


def execute_mother_nursing(
    mother,
    *,
    day_number: int,
    pup_name: str | None = None,
) -> tuple[bool, str]:
    """Nurse biological pups under weaning age. Once per sunrise per mother."""
    if mother["birth_sex"] != "female":
        return False, "only **female** wolves can nurse with milk."

    # no mother-level once-per-sunrise block: each pup can only take milk once a
    # day (pup_needs_milk_today) and nursing costs the mother hunger per pup, so
    # those two are the real limiters; a repeat nurse just feeds any pup that
    # still needs it.
    pups = _filter_pups(db.get_nursing_pups_for_mother(mother["id"]), pup_name)
    pups = [p for p in pups if pup_needs_milk_today(p, day_number)]
    if not pups:
        if pup_name:
            return False, (
                f"**{pup_name}** is not your nursing pup, is weaned, or was already fed today."
            )
        return False, (
            f"**{mother['wolf_name']}** has no pups under **{PUP_MAX_MOONS} moons** "
            "who still need milk today."
            + lone_nursing_note(mother)
        )

    total_cost = MOTHER_NURSE_HUNGER_COST_PER_PUP * len(pups)
    mother_hunger = int(mother["hunger"] if "hunger" in mother.keys() else 80)
    if mother_hunger - total_cost < HUNGER_CRITICAL_THRESHOLD:
        return False, (
            f"**{mother['wolf_name']}** is too hungry to nurse "
            f"(needs **{total_cost}** satiety; eat from `/food` first)."
            + lone_nursing_note(mother)
        )

    honey_used = _try_consume_feeder_honey(mother)
    fed = _feed_pups_with_gains(
        pups,
        hunger_gain=MILK_HUNGER_GAIN,
        thirst_gain=MILK_THIRST_GAIN,
        day_number=day_number,
        honey_used=honey_used,
        feeder_id=mother["id"],
    )

    db.update_user_by_id(
        mother["id"],
        hunger=_clamp_hunger(mother_hunger - total_cost),
        last_nurse_day=day_number,
    )

    lines = ", ".join(f"**{n}**" for n in fed)
    return True, (
        f"**{mother['wolf_name']}** nurses {lines}. "
        f"milk restores **+{MILK_HUNGER_GAIN}** satiety and **+{MILK_THIRST_GAIN}** hydration per pup "
        f"(**−{total_cost}** satiety for the mother)."
        + _honey_suffix(honey_used)
        + (lone_nursing_note(mother) if not mother["pack_id"] else "")
    )


def execute_caretaker_feed(
    caretaker,
    *,
    pack_id: int | None,
    day_number: int,
    pup_name: str | None = None,
) -> tuple[bool, str]:
    """Caretakers mash prey into nursery gruel for weaning pups."""
    if not is_nursery_caretaker(caretaker):
        return False, "only **caretakers** can feed pups without nursing."

    if not pack_id:
        return False, "join a pack to tend nursery pups."

    # no caretaker-level block: each pup takes nursery mash only once a day
    # (pup_needs_milk_today), so that per-pup gate is the real limiter.
    pups = _filter_pups(db.get_pack_pups_needing_feed(pack_id), pup_name)
    pups = [p for p in pups if pup_needs_milk_today(p, day_number)]
    if not pups:
        if pup_name:
            return False, f"no nursing pup named **{pup_name}** in your pack needs food today."
        return False, "no pups under weaning age need nursery mash in your pack today."

    honey_used = _try_consume_feeder_honey(caretaker)
    fed = _feed_pups_with_gains(
        pups,
        hunger_gain=CARETAKER_MASH_HUNGER_GAIN,
        thirst_gain=CARETAKER_MASH_THIRST_GAIN,
        day_number=day_number,
        honey_used=honey_used,
        feeder_id=caretaker["id"],
    )

    db.update_user_by_id(caretaker["id"], last_nurse_day=day_number)
    lines = ", ".join(f"**{n}**" for n in fed)
    return True, (
        f"**{caretaker['wolf_name']}** shares warm mash with {lines} "
        f"(**+{CARETAKER_MASH_HUNGER_GAIN}** satiety, **+{CARETAKER_MASH_THIRST_GAIN}** hydration each)."
        + _honey_suffix(honey_used)
    )


def execute_nursing(
    feeder,
    *,
    day_number: int,
    pack_id: int | None,
    pup_name: str | None = None,
) -> tuple[bool, str]:
    if is_nursing_mother(feeder):
        return execute_mother_nursing(feeder, day_number=day_number, pup_name=pup_name)
    if is_nursery_caretaker(feeder):
        return execute_caretaker_feed(
            feeder, pack_id=pack_id, day_number=day_number, pup_name=pup_name
        )
    if feeder["birth_sex"] == "female":
        return False, (
            "you have no nursing pups. **caretakers** can mash-feed pack pups, "
            "or wait until your litter is born."
            + lone_nursing_note(feeder)
        )
    return False, (
        "only **mothers** with nursing pups or **caretakers** can use **`/pupcare action:feed`**."
    )


def apply_unfed_pup_penalty_on_rollover(conn, day_ending: int) -> list[dict]:
    """Extra hunger slip for pups who missed milk the previous sunrise."""
    from config import PUP_UNFED_EXTRA_DECAY

    rows = conn.execute(
        """
        SELECT id, wolf_name, discord_id, hunger
        FROM users
        WHERE age_months < ?
          AND condition NOT IN ('dead', 'dying')
          AND COALESCE(last_milk_day, 0) < ?
        """,
        (PUP_MAX_MOONS, day_ending),
    ).fetchall()
    notes: list[dict] = []
    for row in rows:
        new_hunger = max(0, int(row["hunger"]) - PUP_UNFED_EXTRA_DECAY)
        conn.execute(
            "UPDATE users SET hunger = ? WHERE id = ?",
            (new_hunger, row["id"]),
        )
        if new_hunger <= HUNGER_CRITICAL_THRESHOLD:
            notes.append(
                {
                    "wolf_name": row["wolf_name"],
                    "discord_id": row["discord_id"],
                    "line": (
                        f"**{row['wolf_name']}** went hungry in the nursery "
                        f"(**−{PUP_UNFED_EXTRA_DECAY}** satiety; use **`/pupcare action:feed`** "
                        "or **`/medic action:treat`** with **honey**)."
                    ),
                }
            )
    return notes


def apply_reproduction_vitals_drain_on_rollover(conn) -> list[dict]:
    """nursing mothers and pregnant females burn extra calories each sunrise."""
    from config import MOTHER_NURSE_HUNGER_COST_PER_PUP, PUP_MAX_MOONS

    PREGNANCY_HUNGER = 5
    PREGNANCY_THIRST = 4
    NURSING_THIRST_PER_PUP = 2

    notes: list[dict] = []
    rows = conn.execute(
        """
        SELECT id, wolf_name, discord_id, hunger, thirst, exhaustion, is_pregnant
        FROM users
        WHERE condition NOT IN ('dead', 'dying')
          AND birth_sex = 'female'
        """
    ).fetchall()
    for row in rows:
        hunger_loss = 0
        thirst_loss = 0
        exhaustion_gain = 0
        parts: list[str] = []
        if int(row["is_pregnant"]):
            hunger_loss += PREGNANCY_HUNGER
            thirst_loss += PREGNANCY_THIRST
            parts.append("gestation")
        pup_row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM users
            WHERE bio_parent_1_id = ?
              AND age_months < ?
              AND condition NOT IN ('dead', 'dying')
            """,
            (row["id"], PUP_MAX_MOONS),
        ).fetchone()
        pup_count = int(pup_row["c"]) if pup_row else 0
        if pup_count:
            hunger_loss += pup_count * MOTHER_NURSE_HUNGER_COST_PER_PUP
            thirst_loss += pup_count * NURSING_THIRST_PER_PUP
            exhaustion_gain += 1
            parts.append(f"nursing {pup_count} pup(s)")
        if not hunger_loss and not thirst_loss and not exhaustion_gain:
            continue
        new_hunger = max(0, int(row["hunger"]) - hunger_loss)
        new_thirst = max(0, int(row["thirst"]) - thirst_loss)
        new_exhaustion = min(5, int(row["exhaustion"]) + exhaustion_gain)
        conn.execute(
            "UPDATE users SET hunger = ?, thirst = ?, exhaustion = ? WHERE id = ?",
            (new_hunger, new_thirst, new_exhaustion, row["id"]),
        )
        drain_parts = []
        if hunger_loss:
            drain_parts.append(f"satiety **−{hunger_loss}**")
        if thirst_loss:
            drain_parts.append(f"hydration **−{thirst_loss}**")
        if exhaustion_gain:
            drain_parts.append(f"exhaustion **+{exhaustion_gain}** (now {new_exhaustion})")
        notes.append(
            {
                "wolf_name": row["wolf_name"],
                "discord_id": row["discord_id"],
                "line": (
                    f"extra drain from {' and '.join(parts)} "
                    f"({', '.join(drain_parts)})."
                ),
            }
        )
    return notes


FOSTER_HEALER_STANDING_BONUS = 1


def apply_foster_pup_rollover(conn) -> list[dict]:
    """
    Each sunrise: pack healers earn standing for hosting a foster pup in good health.
    """
    notes: list[dict] = []
    foster_pups = conn.execute(
        "SELECT * FROM users WHERE foster_pack_id IS NOT NULL AND condition NOT IN ('dead', 'dying')"
    ).fetchall()
    for pup in foster_pups:
        host_pack_id = int(pup["pack_id"]) if pup["pack_id"] else None
        origin_pack_id = int(pup["foster_pack_id"])
        if not host_pack_id or host_pack_id == origin_pack_id:
            continue
        medics = conn.execute(
            "SELECT * FROM users WHERE pack_id = ? AND wolf_role IN ('healer', 'healer_apprentice') AND condition NOT IN ('dead', 'dying')",
            (host_pack_id,),
        ).fetchall()
        for medic in medics:
            conn.execute(
                "UPDATE users SET standing = MIN(10, standing + ?) WHERE id = ?",
                (FOSTER_HEALER_STANDING_BONUS, medic["id"]),
            )
        if medics:
            notes.append({
                "wolf_name": pup["wolf_name"],
                "discord_id": None,
                "line": (
                    f"**{pup['wolf_name']}** (foster pup) cared for; "
                    f"{len(medics)} healer(s) earn standing **+{FOSTER_HEALER_STANDING_BONUS}** for the work."
                ),
            })
    return notes


def apply_winter_pup_cold_on_rollover(conn, season: str) -> list[dict]:
    """Pups in winter gain exhaustion from cold exposure each sunrise even when
    fed. Real pup mortality peaks in winter; here it shows as compounding
    exhaustion rather than instant death so players still have a chance to act."""
    import random
    if season != "winter":
        return []
    from config import PUP_MAX_MOONS, PUP_WINTER_COLD_EXHAUSTION_CHANCE

    rows = conn.execute(
        """
        SELECT id, wolf_name, discord_id, exhaustion, age_months
        FROM users
        WHERE age_months < ? AND condition NOT IN ('dead', 'dying')
        """,
        (PUP_MAX_MOONS,),
    ).fetchall()
    notes: list[dict] = []
    for pup in rows:
        if random.random() > PUP_WINTER_COLD_EXHAUSTION_CHANCE:
            continue
        old_ex = int(pup["exhaustion"]) if pup["exhaustion"] is not None else 0
        new_ex = old_ex + 1
        conn.execute("UPDATE users SET exhaustion = ? WHERE id = ?", (new_ex, pup["id"]))
        notes.append({
            "wolf_name": pup["wolf_name"],
            "discord_id": int(pup["discord_id"]) if pup["discord_id"] else None,
            "line": f"cold night; exhaustion **{old_ex}** → **{new_ex}** (`/pupcare action:feed` with honey eases the chill).",
        })
    return notes
