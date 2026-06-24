"""Run catalogued skill scenarios with mechanical outcomes."""

from __future__ import annotations

import random

import database as db
from engine.dice import format_contest_roll, format_roll_result, resolve_check, roll_contest
from engine.exhaustion_effects import effective_max_hp
from engine.herb_storage import consume_yarrow_from_bag, has_yarrow
from engine.skill_checks import OPPOSED_SPECS, SKILL_SCENARIOS, opponent_required


def _proficient(user, skill_key: str) -> bool:
    from engine.character import is_skill_proficient

    return is_skill_proficient(user, skill_key)


def _append_setback_on_failure(
    user,
    lines: list[str],
    *,
    skill_key: str,
    outcome: str,
    day: int,
    total: int | None = None,
    dc: int | None = None,
    margin: int | None = None,
) -> None:
    from engine.character_traits import maybe_apply_failure_setback

    note = maybe_apply_failure_setback(
        user,
        skill_key=skill_key,
        outcome=outcome,
        game_day=day,
        total=total,
        dc=dc,
        margin=margin,
    )
    if note:
        lines.append(note)


def _append_success_recovery(
    user,
    lines: list[str],
    *,
    skill_key: str,
    day: int,
    dc: int | None = None,
) -> None:
    from engine.character_traits import maybe_apply_success_recovery

    note = maybe_apply_success_recovery(
        user, skill_key=skill_key, game_day=day, dc=dc
    )
    if note:
        lines.append(note)


def _weather_scent_dc_mod(weather: str, *, rained: bool = False) -> tuple[int, str]:
    notes = []
    mod = 0
    if weather in ("rain", "sleet", "storm", "thunderstorm"):
        mod += 3
        notes.append("rain washes scent (+3 DC)")
    if weather in ("snow", "hail"):
        mod += 2
        notes.append("snow dulls scent (+2 DC)")
    if weather == "wind":
        mod += 2
        notes.append("wind disperses scent (+2 DC)")
    if rained:
        mod += 5
        notes.append("recent rain (+5 DC)")
    return mod, " · ".join(notes)


def _time_dc_mod(time_of_day: str, category: str) -> tuple[int, str]:
    if category not in ("tracking", "stealth"):
        return 0, ""
    if time_of_day == "night":
        return 2, "Moonhigh dark (+2 DC on scent/sight)"
    if time_of_day == "dusk":
        return 1, "Half-light (+1 DC)"
    return 0, ""


def _apply_social_standing(attacker, defender, scenario_key: str, *, won: bool) -> str:
    if scenario_key != "social_dominance" or not won:
        return ""
    if not attacker.get("pack_id") or attacker["pack_id"] != defender.get("pack_id"):
        return ""
    db.adjust_wolf_standing(attacker["discord_id"], 1)
    db.adjust_wolf_standing(defender["discord_id"], -1)
    return "\n_Pack standing: you **+1**, they **−1**._"


def _run_opposed(
    attacker,
    defender,
    scenario,
    *,
    day: int,
    weather: str,
    rained: bool,
) -> tuple[bool, str]:
    spec = OPPOSED_SPECS[scenario.key]
    att_name = attacker["wolf_name"]
    def_name = defender["wolf_name"] if defender else "The plant"

    if spec.plant_dc_range:
        plant_dc = random.randint(*spec.plant_dc_range)
        result = resolve_check(
            attacker,
            attr_keys=scenario.attr_keys,
            skill=scenario.skill_label,
            dc=plant_dc,
            proficient=_proficient(attacker, scenario.skill_key),
            skill_key=scenario.skill_key,
            game_day=day,
        )
        lines = [
            format_roll_result(result),
            f"_Plant poison DC **{plant_dc}**._",
        ]
        if result["success"]:
            lines.append(scenario.success)
            return True, "\n\n".join(lines)
        dmg = random.randint(1, 4)
        new_hp = max(0, int(attacker["hp"]) - dmg)
        db.set_user_conditions(attacker["discord_id"], hp=new_hp)
        lines.append(scenario.failure)
        lines.append(f"**−{dmg} HP** from the taste.")
        _append_setback_on_failure(
            attacker,
            lines,
            skill_key=scenario.skill_key,
            outcome=result["outcome"],
            day=day,
            total=result["total"],
            dc=plant_dc,
        )
        return False, "\n\n".join(lines)

    att_roll = roll_contest(
        attacker,
        attr_keys=scenario.attr_keys,
        skill_key=scenario.skill_key,
        skill_label=scenario.skill_label,
        game_day=day,
        proficient=_proficient(attacker, scenario.skill_key),
    )
    def_roll = roll_contest(
        defender,
        attr_keys=spec.defender_attr_keys,
        skill_key=spec.defender_skill_key,
        skill_label=spec.defender_skill_label,
        game_day=day,
        flat_bonus=spec.defender_flat_bonus,
        proficient=_proficient(defender, spec.defender_skill_key),
    )
    att_total = att_roll["contest_total"]
    def_total = def_roll["contest_total"]
    lines = [
        format_contest_roll(att_name, att_roll),
        format_contest_roll(def_name, def_roll),
    ]
    if att_roll["die"] == 20 or def_roll["die"] == 1:
        lines.append(scenario.success)
        lines.append(_apply_social_standing(attacker, defender, scenario.key, won=True))
        return True, "\n\n".join(lines)
    if att_roll["die"] == 1 or def_roll["die"] == 20:
        lines.append(scenario.failure)
        if scenario.fail_damage:
            dmg = random.randint(*scenario.fail_damage)
            new_hp = max(0, int(attacker["hp"]) - dmg)
            db.set_user_conditions(attacker["discord_id"], hp=new_hp)
            lines.append(f"**−{dmg} HP**")
        setback_outcome = "critical_failure" if att_roll["die"] == 1 else "failure"
        _append_setback_on_failure(
            attacker,
            lines,
            skill_key=scenario.skill_key,
            outcome=setback_outcome,
            day=day,
            margin=max(0, def_total - att_total) if setback_outcome == "failure" else None,
        )
        return False, "\n\n".join(lines)
    if att_total > def_total:
        lines.append(f"**{att_name}** wins (**{att_total}** vs **{def_total}**).")
        lines.append(scenario.success)
        lines.append(_apply_social_standing(attacker, defender, scenario.key, won=True))
        return True, "\n\n".join(lines)
    if att_total < def_total:
        lines.append(f"**{def_name}** wins (**{def_total}** vs **{att_total}**).")
        lines.append(scenario.failure)
        if scenario.fail_damage:
            dmg = random.randint(*scenario.fail_damage)
            new_hp = max(0, int(attacker["hp"]) - dmg)
            db.set_user_conditions(attacker["discord_id"], hp=new_hp)
            lines.append(f"**−{dmg} HP**")
        if scenario.fail_mood:
            db.adjust_mood(attacker["id"], -scenario.fail_mood)
        _append_setback_on_failure(
            attacker,
            lines,
            skill_key=scenario.skill_key,
            outcome="failure",
            day=day,
            margin=max(0, def_total - att_total),
        )
        return False, "\n\n".join(lines)
    lines.append(f"Tie at **{att_total}**; edge to the defender.")
    lines.append(scenario.failure)
    _append_setback_on_failure(
        attacker,
        lines,
        skill_key=scenario.skill_key,
        outcome="failure",
        day=day,
        margin=1,
    )
    return False, "\n\n".join(lines)


def run_skill_scenario(
    user,
    scenario_key: str,
    *,
    day: int,
    weather: str = "clear",
    time_of_day: str = "day",
    rained: bool = False,
    yarrow_bonus: bool = False,
    opponent=None,
) -> tuple[bool, str, dict]:
    scenario = SKILL_SCENARIOS.get(scenario_key)
    if not scenario:
        return False, "Unknown skill check.", {}

    if opponent_required(scenario_key) and not opponent:
        return (
            False,
            "This check is **opposed**; pick an **opponent** packmate or rival wolf.",
            {},
        )

    if scenario.opposed and scenario.key in OPPOSED_SPECS:
        ok, body = _run_opposed(
            user,
            opponent,
            scenario,
            day=day,
            weather=weather,
            rained=rained,
        )
        return ok, body, {}

    dc = scenario.dc
    extra_notes = []
    if scenario.category == "tracking":
        mod, note = _weather_scent_dc_mod(weather, rained=rained)
        dc += mod
        if note:
            extra_notes.append(note)
    if scenario.key == "track_blood" and rained:
        dc += 5
        extra_notes.append("blood trail washed (+5 DC)")
    time_mod, time_note = _time_dc_mod(time_of_day, scenario.category)
    dc += time_mod
    if time_note:
        extra_notes.append(time_note)

    use_yarrow = yarrow_bonus
    if scenario.key == "surv_stabilize" and not use_yarrow and has_yarrow(user):
        use_yarrow = True
        consume_yarrow_from_bag(user)
        extra_notes.append("Yarrow applied (+2 stabilize).")

    if use_yarrow and scenario.key == "surv_stabilize":
        dc = max(5, dc - 2)

    result = resolve_check(
        user,
        attr_keys=scenario.attr_keys,
        skill=scenario.skill_label,
        dc=dc,
        proficient=_proficient(user, scenario.skill_key),
        skill_key=scenario.skill_key,
        game_day=day,
        weather_key=weather,
    )
    from engine.herb_buffs import consume_herb_check_buffs

    consume_fields = consume_herb_check_buffs(user, skill_key=scenario.skill_key)
    if consume_fields:
        db.update_user(user["discord_id"], wolf_id=user["id"], **consume_fields)

    effects: dict = {}
    lines = [format_roll_result(result)]
    if extra_notes:
        lines.append("_" + " · ".join(extra_notes) + "_")

    if result["outcome"] == "critical_failure" and scenario.crit_fail:
        lines.append(scenario.crit_fail)
        if scenario.category == "spiritual" and scenario.key == "spirit_ancestors":
            db.adjust_mood(user["id"], -scenario.fail_mood)
            db.set_user_conditions(user["discord_id"], exhaustion=min(6, int(user["exhaustion"]) + 1))
        if scenario.key == "surv_set_bone":
            from engine.long_term_injuries import add_long_term_injury

            add_long_term_injury(user["id"], "limp")
            lines.append("_The bone sets wrong; a permanent **limp** may follow._")
        success = False
    elif result["success"]:
        lines.append(scenario.success)
        success = True
        if scenario.success_flag == "sneak_advantage":
            db.update_user(user["discord_id"], wolf_id=user["id"], commanding_howl_buff=1)
            lines.append("_Sneak success; next attack/check gains advantage._")
        if scenario.key == "surv_stabilize":
            cap = effective_max_hp(user)
            db.set_user_conditions(user["discord_id"], hp=max(1, min(cap, 1)), condition="stable")
        if scenario.key == "spirit_cleanse":
            from engine.supernatural import lift_spirit_curse

            if lift_spirit_curse(user["id"]):
                lines.append("_Curse scent lifts from the pelt._")
        _append_success_recovery(
            user, lines, skill_key=scenario.skill_key, day=day, dc=dc
        )
    else:
        lines.append(scenario.failure)
        success = False
        if scenario.fail_mood:
            db.adjust_mood(user["id"], -scenario.fail_mood)
        if scenario.fail_damage:
            dmg = random.randint(*scenario.fail_damage)
            new_hp = max(0, int(user["hp"]) - dmg)
            db.set_user_conditions(user["discord_id"], hp=new_hp)
            lines.append(f"**−{dmg} HP**")
        if scenario.key == "spirit_cleanse":
            from engine.supernatural import apply_spirit_curse

            apply_spirit_curse(user["id"], source="botched cleansing ritual")
            lines.append("_Smoke wrong; the curse clings._")
        if scenario.key == "spirit_ancestors" and not result["success"]:
            from engine.supernatural import apply_spirit_curse

            if random.random() < 0.35:
                apply_spirit_curse(user["id"], source="ancestor silence turned cruel")
                lines.append("_The ancestors do not answer; something darker does._")
        if scenario.key == "surv_set_bone":
            from engine.long_term_injuries import add_long_term_injury

            add_long_term_injury(user["id"], "limp")
            lines.append("_Splint fails; risk of permanent **limp** (GM may assign)._")
        if scenario.key == "surv_blizzard_shelter":
            db.set_user_conditions(
                user["discord_id"],
                exhaustion=min(6, int(user["exhaustion"]) + 1),
            )
            lines.append("+1 exhaustion from exposure.")

    if not success:
        _append_setback_on_failure(
            user,
            lines,
            skill_key=scenario.skill_key,
            outcome=result["outcome"],
            day=day,
            total=result["total"],
            dc=dc,
        )

    return success, "\n\n".join(lines), effects
