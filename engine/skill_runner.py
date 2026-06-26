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
    if not db.row_val(attacker, "pack_id") or db.row_val(attacker, "pack_id") != db.row_val(defender, "pack_id"):
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
    guild_id: int | None = None,
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
            if scenario.key == "prep_taste_test":
                _apply_herb_prep_mechanics(
                    attacker,
                    scenario.key,
                    success=True,
                    outcome=result.get("outcome", "success"),
                    day=day,
                    guild_id=guild_id,
                    lines=lines,
                )
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


def apply_scenario_mechanics(
    user,
    scenario,
    result: dict,
    *,
    day: int,
    weather: str = "clear",
    opponent=None,
    guild_id: int | None = None,
) -> tuple[bool, list[str]]:
    """Apply DB outcomes from a resolved roll. Returns (success, extra lines)."""
    lines: list[str] = []
    success = bool(result.get("success"))
    outcome = result.get("outcome", "failure")

    if outcome == "critical_failure" and scenario.crit_fail:
        lines.append(scenario.crit_fail)
        if scenario.category == "spiritual" and scenario.key == "spirit_ancestors":
            if scenario.fail_mood:
                db.adjust_mood(user["id"], -scenario.fail_mood)
            db.set_user_conditions(user["discord_id"], exhaustion=min(6, int(user["exhaustion"]) + 1))
        if scenario.key == "surv_set_bone":
            from engine.long_term_injuries import add_long_term_injury

            add_long_term_injury(user["id"], "limp")
            lines.append("_The bone sets wrong; a permanent **limp** may follow._")
        if scenario.key == "track_faint":
            db.update_user(user["discord_id"], wolf_id=user["id"], last_track_day=day)
            lines.append("_Today's track is spent._")
        if scenario.key == "nav_blizzard_camp":
            db.set_user_conditions(
                user["discord_id"],
                exhaustion=min(6, int(user["exhaustion"]) + 2),
            )
            lines.append("+2 exhaustion; you crossed into hostile ground.")
        _append_setback_on_failure(
            user,
            lines,
            skill_key=scenario.skill_key,
            outcome="critical_failure",
            day=day,
            total=result.get("total"),
            dc=result.get("dc"),
        )
        success = False
    elif success:
        lines.append(scenario.success)
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
        if scenario.key == "surv_blizzard_shelter":
            ex = max(0, int(user["exhaustion"]) - 1)
            db.set_user_conditions(user["discord_id"], wolf_id=user["id"], exhaustion=ex)
            db.adjust_mood(user["id"], 4)
            lines.append("_Lee found; **−1 exhaustion**, **+4 mood**._")
        if scenario.key == "nav_blizzard_camp":
            ex = max(0, int(user["exhaustion"]) - 1)
            db.set_user_conditions(user["discord_id"], wolf_id=user["id"], exhaustion=ex)
            db.adjust_mood(user["id"], 3)
            lines.append("_Camp found; **−1 exhaustion**, **+3 mood**._")
        if scenario.category == "howling":
            db.adjust_mood(user["id"], 2)
            lines.append("_The song carries; **+2 mood**._")
        if scenario.key == "spirit_vision":
            db.adjust_mood(user["id"], 3)
            lines.append("_Vision lingers; **+3 mood**._")
        if scenario.key == "spirit_omen":
            roll = random.random()
            buff = "good" if roll > 0.45 else "bad"
            db.update_user_by_id(user["id"], omen_buff=buff)
            lines.append(
                f"_Omen read **{buff}**; advantage on your first roll next sunrise._"
                if buff == "good"
                else "_Omen read **bad**; disadvantage on your first roll next sunrise._"
            )
        if scenario.key == "spirit_prophecy":
            db.adjust_mood(user["id"], 2)
            lines.append("_The ancestors whisper; **+2 mood**._")
        if scenario.key == "craft_splint":
            from engine.herb_buffs import merge_buff_fields

            fields = merge_buff_fields(user, broom_splint=True, bone_heal_days_reduced=2)
            db.update_user(user["discord_id"], wolf_id=user["id"], **fields)
            lines.append("_Splint ready; bone injuries heal **2 days** faster._")
        if scenario.key == "craft_travois":
            ex = max(0, int(user["exhaustion"]) - 1)
            db.set_user_conditions(user["discord_id"], wolf_id=user["id"], exhaustion=ex)
            lines.append("_Travois lashed; **−1 exhaustion** hauling the wounded._")
        if scenario.key == "surv_dig_den":
            ex = max(0, int(user["exhaustion"]) - 1)
            db.set_user_conditions(user["discord_id"], wolf_id=user["id"], exhaustion=ex)
            lines.append("_Den scraped; **−1 exhaustion** from shelter work._")
        if scenario.key == "surv_diagnose":
            key, stage = parse_disease_from_user(user)
            if key:
                from engine.diseases import get_stage_info

                info = get_stage_info(key, stage)
                if info:
                    lines.append(f"_Diagnosis: **{info['name']}** — {info['effect']}_")
            else:
                lines.append("_No active illness; vitals read clear._")
        if scenario.key == "social_truce" and opponent:
            db.adjust_mood(user["id"], 2)
            db.adjust_mood(opponent["id"], 1)
            lines.append("_Tension eases; mood **+2** (you), **+1** (them)._")
            _maybe_cross_pack_relation(user, opponent, guild_id, delta=1, lines=lines)
        if scenario.key == "social_intimidate" and opponent:
            db.adjust_mood(opponent["id"], -2)
            lines.append(f"_{opponent['wolf_name']} flinches; **−2 mood**._")
        elif scenario.key == "social_intimidate":
            db.adjust_mood(user["id"], 2)
            lines.append("_They yield ground; **+2 mood**._")
        if scenario.key == "howl_warning" and db.row_val(user, "pack_id"):
            db.adjust_wolf_standing(user["discord_id"], 1)
            lines.append("_Border claimed; standing **+1**._")
        if scenario.key == "social_calm_pup":
            db.adjust_mood(user["id"], 3)
            lines.append("_Pup settles; **+3 mood**._")
        if scenario.key == "social_challenge_alpha":
            db.adjust_wolf_standing(user["discord_id"], 1)
            lines.append("_Challenge lodged; standing **+1**._")
        if scenario.key == "spirit_recall_patch":
            db.adjust_mood(user["id"], 2)
            lines.append("_The ground remembers; **+2 mood**._")
        _append_success_recovery(user, lines, skill_key=scenario.skill_key, day=day, dc=scenario.dc)
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
        if scenario.key in ("social_persuade_alpha", "social_apologize") and db.row_val(user, "pack_id"):
            db.adjust_wolf_standing(user["discord_id"], -1)
            lines.append("_Pack standing **−1**._")
        if scenario.key == "howl_storm":
            db.set_user_conditions(
                user["discord_id"],
                exhaustion=min(6, int(user["exhaustion"]) + 1),
            )
            lines.append("+1 exhaustion; the gale swallows your song.")
        if scenario.key == "spirit_cleanse":
            from engine.supernatural import apply_spirit_curse

            apply_spirit_curse(user["id"], source="botched cleansing ritual")
            lines.append("_Smoke wrong; the curse clings._")
        if scenario.key == "spirit_ancestors":
            from engine.supernatural import apply_spirit_curse

            if random.random() < 0.35:
                apply_spirit_curse(user["id"], source="ancestor silence turned cruel")
                lines.append("_The ancestors do not answer; something darker does._")
        if scenario.key == "surv_set_bone":
            from engine.long_term_injuries import add_long_term_injury

            add_long_term_injury(user["id"], "limp")
            lines.append("_Splint fails; risk of permanent **limp**._")
        if scenario.key == "surv_blizzard_shelter":
            db.set_user_conditions(
                user["discord_id"],
                exhaustion=min(6, int(user["exhaustion"]) + 1),
            )
            lines.append("+1 exhaustion from exposure.")
        if scenario.key == "nav_blizzard_camp":
            db.set_user_conditions(
                user["discord_id"],
                exhaustion=min(6, int(user["exhaustion"]) + 1),
            )
            lines.append("+1 exhaustion; you sleep exposed.")
        if scenario.key == "surv_thorn":
            from engine.disease_contract import try_contract_disease

            note = try_contract_disease(user, "mild_poison", "stung", chance=0.4)
            if note:
                lines.append(f"Puncture festers: {note}")
        if scenario.key == "stealth_no_scent":
            db.adjust_mood(user["id"], -3)
            lines.append("_Patrol catches your line; **−3 mood**._")
        if scenario.key == "howl_imitate":
            db.adjust_mood(user["id"], -2)
            lines.append("_Caught in the lie; **−2 mood**._")
        if scenario.key == "social_lie":
            db.adjust_mood(user["id"], -2)
            lines.append("_Ears twitch; **−2 mood**._")
        if scenario.key == "nav_landmark_unknown":
            db.set_user_conditions(
                user["discord_id"],
                exhaustion=min(6, int(user["exhaustion"]) + 1),
            )
            lines.append("+1 exhaustion; lost on the wrong ridge.")
        if scenario.key == "stealth_leaves":
            db.adjust_mood(user["id"], -2)
            lines.append("_Twigs betray you; **−2 mood**._")
        _append_setback_on_failure(
            user,
            lines,
            skill_key=scenario.skill_key,
            outcome=outcome,
            day=day,
            total=result.get("total"),
            dc=result.get("dc"),
            margin=result.get("margin"),
        )

    if scenario.category == "herb_prep" and scenario.key != "prep_taste_test":
        _apply_herb_prep_mechanics(
            user, scenario.key, success=success, outcome=outcome, day=day, guild_id=guild_id, lines=lines
        )

    from engine.activity_exhaustion import apply_activity_fatigue, skill_for_activity

    if scenario.key.startswith("track_"):
        act_key, sk = "track", "tracking"
    else:
        act_key, sk = "skill", scenario.skill_key
    fresh = db.get_user(user["discord_id"])
    if fresh:
        fatigue = apply_activity_fatigue(fresh, act_key, sk or skill_for_activity(act_key, fresh), day)
        if fatigue:
            lines.append(fatigue)

    return success, lines


def _apply_herb_prep_mechanics(
    user,
    scenario_key: str,
    *,
    success: bool,
    outcome: str,
    day: int,
    guild_id: int | None,
    lines: list[str],
) -> None:
    from engine.herb_prep_batches import apply_herb_prep_outcome

    user_fields, cond_fields, prep_lines = apply_herb_prep_outcome(
        user,
        scenario_key,
        success=success,
        outcome=outcome,
        day=day,
        guild_id=guild_id,
    )
    if user_fields:
        db.update_user(user["discord_id"], wolf_id=user["id"], **user_fields)
    if cond_fields:
        db.set_user_conditions(user["discord_id"], wolf_id=user["id"], **cond_fields)
    lines.extend(prep_lines)


def parse_disease_from_user(user):
    from engine.diseases import parse_disease

    return parse_disease(user["disease"] if user and "disease" in user.keys() else None)


def _maybe_cross_pack_relation(user, opponent, guild_id, *, delta: int, lines: list[str]) -> None:
    if not guild_id:
        return
    gp_a = db.row_val(user, "great_pack") if user else None
    gp_b = db.row_val(opponent, "great_pack") if opponent else None
    if not gp_a or not gp_b or gp_a == gp_b:
        return
    pack_a = db.get_pack_by_key(gp_a)
    pack_b = db.get_pack_by_key(gp_b)
    if not pack_a or not pack_b:
        return
    new_standing = db.adjust_pack_relation(guild_id, pack_a["id"], pack_b["id"], delta)
    lines.append(f"_Pack relations **{delta:+d}** (now **{new_standing}**)._")


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
    guild_id: int | None = None,
    season: str | None = None,
    sniff_dc_reduction: int = 0,
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
            guild_id=guild_id,
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
    if scenario.category == "tracking" and season:
        from engine.season_effects import season_track_dc_label, season_track_dc_mod

        s_mod = season_track_dc_mod(season)
        if s_mod:
            dc += s_mod
            label = season_track_dc_label(season)
            if label:
                extra_notes.append(label)
    if scenario.category == "tracking" and sniff_dc_reduction > 0:
        dc = max(5, dc - sniff_dc_reduction)
        extra_notes.append(f"wind-read (−{sniff_dc_reduction} DC)")
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

    result_with_dc = dict(result)
    result_with_dc["dc"] = dc
    success, mech_lines = apply_scenario_mechanics(
        user,
        scenario,
        result_with_dc,
        day=day,
        weather=weather,
        opponent=opponent,
        guild_id=guild_id,
    )
    lines.extend(mech_lines)

    return success, "\n\n".join(lines), effects
