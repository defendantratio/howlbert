from rpg_rules import DC_TIERS
from engine.character import attr_modifier, best_modifier
from engine.disease_effects import disease_check_adjustments
from engine.genetics import genetic_check_adjustments
from engine.injury_effects import injury_check_adjustments
from engine.character_traits import trait_check_adjustments, trait_check_disadvantage
from engine.role_features import (
    role_check_adjustments,
    try_consume_blood_oath_buff,
    try_consume_commanding_howl_buff,
)
from engine.rolls import roll_d20


def resolve_check(
    user,
    *,
    attr_keys: tuple[str, ...],
    skill: str | None,
    dc: int,
    proficient: bool,
    allow_safe_roll: bool = False,
    has_safe_roll: bool = False,
    skill_key: str | None = None,
    game_day: int | None = None,
    weather_key: str | None = None,
    fear_context: str | None = None,
) -> dict:
    inj_pen, inj_disadv = injury_check_adjustments(user, attr_keys, skill)
    disease_mod, disease_disadv = disease_check_adjustments(user, attr_keys)
    gen_pen, gen_disadv = genetic_check_adjustments(user, attr_keys)
    trait_mod, trait_applied = trait_check_adjustments(
        user, attr_keys, skill_key=skill_key, skill_label=skill
    )
    trait_disadv = trait_check_disadvantage(
        user, attr_keys, skill_key=skill_key, skill_label=skill
    )
    from engine.herb_buffs import herb_check_adjustments, frostbite_dex_penalty

    herb_mod, herb_adv = herb_check_adjustments(user, attr_keys, skill_key=skill_key)
    frost_mod = frostbite_dex_penalty(user, game_day or 0) if "attr_dex" in attr_keys else 0
    role_mod, role_adv, role_dis = role_check_adjustments(
        user, attr_keys, skill_key=skill_key, weather_key=weather_key
    )
    howl_adv = try_consume_commanding_howl_buff(user)
    blood_oath_adv = try_consume_blood_oath_buff(
        user, attr_keys, skill_key=skill_key, game_day=game_day
    )
    from engine.long_term_injuries import check_adjustments as lt_adjustments
    from engine.fire_fear import is_frightened_of_fire

    lt_mod, lt_disadv, _lt_note = lt_adjustments(
        user,
        attr_keys=attr_keys,
        skill_key=skill_key,
        weather=weather_key or "",
        day_number=game_day or 0,
        first_physical_today=True,
    )
    from engine.long_term_injuries import fear_trigger_check

    fear_disadv, _fear_note = fear_trigger_check(
        user,
        fear_context=fear_context,
        skill_key=skill_key,
        game_day=game_day,
    )
    fire_disadv = is_frightened_of_fire(user) and skill_key not in ("tracking", "survival")
    omen_adv = False
    omen_disadv = False
    omen_buff = user["omen_buff"] if "omen_buff" in user.keys() else ""
    if omen_buff == "good":
        omen_adv = True
    elif omen_buff == "bad":
        omen_disadv = True
    exhaustion = int(user["exhaustion"]) if "exhaustion" in user.keys() else 0
    exhaust_disadv = exhaustion >= 1
    use_disadv = (
        inj_disadv or disease_disadv or gen_disadv or exhaust_disadv or role_dis
        or trait_disadv or lt_disadv or fire_disadv or omen_disadv or fear_disadv
    )
    use_adv = (
        (role_adv or howl_adv or blood_oath_adv or herb_adv or omen_adv) and not use_disadv
    )
    if use_adv:
        die = max(roll_d20(), roll_d20())
    elif use_disadv:
        die = min(roll_d20(), roll_d20())
    else:
        die = roll_d20()
    mod, attr_label = best_modifier(user, attr_keys)
    prof = 0
    rank_bonus = 0
    total = die + mod + prof + inj_pen + gen_pen + trait_mod + role_mod + herb_mod + lt_mod + frost_mod + disease_mod
    safe_roll_used = False
    first_die = die

    if die == 1:
        outcome = "critical_failure"
        success = False
    elif die == 20:
        outcome = "critical_success"
        success = True
    elif total >= dc:
        outcome = "success"
        success = True
    else:
        outcome = "failure"
        success = False
        if allow_safe_roll and has_safe_roll and die != 1:
            safe_roll_used = True
            if use_adv:
                die = max(roll_d20(), roll_d20())
            elif use_disadv:
                die = min(roll_d20(), roll_d20())
            else:
                die = roll_d20()
            total = die + mod + prof + inj_pen + gen_pen + trait_mod + role_mod + herb_mod + lt_mod + frost_mod + disease_mod
            if die == 1:
                outcome = "critical_failure"
                success = False
            elif die == 20:
                outcome = "critical_success"
                success = True
            elif total >= dc:
                outcome = "success"
                success = True
            else:
                outcome = "failure"
                success = False

    if omen_buff in ("good", "bad") and "id" in user.keys():
        import database as db

        db.update_user_by_id(user["id"], omen_buff="")

    consume_fields: dict = {}
    from engine.disease_effects import consume_disease_check_flags

    if game_day is not None:
        consume_fields = consume_disease_check_flags(user, game_day)
        if consume_fields and "id" in user.keys():
            import database as db

            db.update_user_by_id(user["id"], **consume_fields)

    return {
        "die": die,
        "first_die": first_die,
        "modifier": mod,
        "proficiency": prof,
        "rank_bonus": rank_bonus,
        "total": total,
        "dc": dc,
        "success": success,
        "outcome": outcome,
        "attr_label": attr_label,
        "skill": skill,
        "safe_roll_used": safe_roll_used,
        "injury_penalty": inj_pen,
        "injury_disadvantage": inj_disadv,
        "disease_disadvantage": disease_disadv,
        "exhaustion_disadvantage": exhaust_disadv,
        "trait_modifier": trait_mod,
        "traits_applied": trait_applied,
        "role_modifier": role_mod,
        "role_advantage": role_adv,
        "role_disadvantage": role_dis,
        "trait_disadvantage": trait_disadv,
        "commanding_howl_advantage": howl_adv,
        "blood_oath_advantage": blood_oath_adv,
    }


def format_roll_result(r: dict) -> str:
    skill = f" ({r['skill']})" if r.get("skill") else ""
    lines = [
        f"**1d20** → **{r['die']}** + {r['modifier']} {r['attr_label']} = **{r['total']}** vs dc **{r['dc']}**{skill}",
    ]
    if r.get("safe_roll_used"):
        lines.insert(
            0,
            f"🎲 **safe roll**; first die was **{r['first_die']}**; rerolled.",
        )
    if r.get("injury_disadvantage"):
        lines.append("_injury; disadvantage on this check._")
    if r.get("disease_disadvantage"):
        lines.append("_disease; disadvantage on this check._")
    if r.get("exhaustion_disadvantage"):
        lines.append("_exhaustion; disadvantage on this check._")
    if r.get("injury_penalty"):
        lines.append(f"_injury modifier: {r['injury_penalty']:+d}._")
    if r.get("trait_modifier"):
        names = ", ".join(r.get("traits_applied") or [])
        lines.append(f"_character trait: **{r['trait_modifier']:+d}** ({names})._")
    if r.get("role_modifier"):
        lines.append(f"_role feature: **{r['role_modifier']:+d}**._")
    if r.get("role_advantage"):
        lines.append("_role feature; advantage on this check._")
    if r.get("trait_disadvantage"):
        lines.append("_character trait; disadvantage on this check._")
    if r.get("commanding_howl_advantage"):
        lines.append("_commanding howl; advantage on this check._")
    if r.get("blood_oath_advantage"):
        lines.append("_blood oath; advantage on this charisma check._")
    if r.get("role_disadvantage"):
        lines.append("_role feature; disadvantage on this check._")
    if r["outcome"] == "critical_success":
        lines.append("**critical success**; exceptional outcome or lasting boon.")
    elif r["outcome"] == "critical_failure":
        lines.append("**critical failure**; something goes badly wrong.")
    elif r["success"]:
        lines.append("**success.**")
    else:
        lines.append("**failure.**")
    return "\n".join(lines)


def format_contest_roll(name: str, r: dict) -> str:
    skill = f" ({r['skill']})" if r.get("skill") else ""
    extra = ""
    if r.get("flat_bonus"):
        extra = f" +{r['flat_bonus']} situational"
    return (
        f"**{name}**: 1d20 → **{r['die']}** + {r['modifier']} {r['attr_label']}{extra} "
        f"= **{r['total']}**{skill}"
    )


def roll_contest(
    user,
    *,
    attr_keys: tuple[str, ...],
    skill_key: str | None,
    skill_label: str,
    game_day: int | None,
    flat_bonus: int = 0,
    proficient: bool = False,
) -> dict:
    """Roll a contest total (no DC) for opposed checks."""
    result = resolve_check(
        user,
        attr_keys=attr_keys,
        skill=skill_label,
        dc=30,
        proficient=proficient,
        skill_key=skill_key,
        game_day=game_day,
    )
    result["contest_total"] = result["total"] + flat_bonus
    result["flat_bonus"] = flat_bonus
    return result
