import json
import random

from engine.character import attr_modifier, parse_proficiencies
from engine.exhaustion_effects import effective_max_hp
from engine.rolls import roll_d20
from herbs import EXHAUSTION_EFFECTS, INJURIES, INJURY_TABLE
from rpg_rules import PROFICIENCY_BONUS


def parse_injuries(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return list(data) if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def parse_injury_since(raw: str | None) -> dict[str, int]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return dict(data) if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def injury_heal_note(key: str, since: dict[str, int], day: int, user=None) -> str:
    """Show heal_days progress; injuries clear only via /treat, not time alone."""
    info = INJURIES.get(key)
    if not info or info.get("permanent"):
        return ""
    heal_days = info.get("heal_days")
    if not heal_days:
        return ""
    if user is not None:
        from engine.herb_buffs import bone_heal_days_reduction, injury_heal_multiplier

        heal_days = max(1, int(heal_days * injury_heal_multiplier(user)))
        if key in ("sprained_leg", "fractured_rib", "broken_jaw", "spinal_injury", "punctured_paw"):
            heal_days = max(1, heal_days - bone_heal_days_reduction(user))
    start = since.get(key)
    if start is not None and day > start:
        elapsed = day - start
        return (
            f" _({elapsed}d elapsed · ~{heal_days}d with rest; "
            f"clears via `/treat` only)_"
        )
    return f" _(~{heal_days}d with rest; clears via `/treat` only)_"


def format_conditions(user, *, day: int | None = None) -> str:
    lines = []
    exhaustion = user["exhaustion"] if "exhaustion" in user.keys() else 0
    if exhaustion:
        effect = EXHAUSTION_EFFECTS.get(exhaustion, "Unknown")
        lines.append(f"**Exhaustion {exhaustion}/6**; {effect}")

    smoke = int(user["smoke_debuff"]) if "smoke_debuff" in user.keys() else 0
    if smoke:
        lines.append("**Wildfire smoke**; disadvantage on Perception until next sunrise.")

    from engine.diseases import disease_display

    illness = disease_display(user)
    if illness:
        name, effect = illness
        lines.append(f"**{name}**; {effect}")

    from engine.quarantine import is_quarantined

    if is_quarantined(user):
        lines.append(
            "**Quarantined**; isolated in the sick den; cannot spread illness or leave for pack activities."
        )

    from engine.genetics import format_genetic_conditions

    genetic_text = format_genetic_conditions(user)
    if genetic_text:
        lines.append(genetic_text)

    injuries = parse_injuries(user["active_injuries"] if "active_injuries" in user.keys() else None)
    since = parse_injury_since(
        user["injury_since"] if "injury_since" in user.keys() else None
    )
    for key in injuries:
        info = INJURIES.get(key)
        if info:
            line = f"**{info['name']}**; {info['effect']}"
            if day is not None:
                line += injury_heal_note(key, since, day, user=user)
            if info.get("treatment"):
                line += f"\n_Treatment: {info['treatment']}_"
            lines.append(line)

    if day is not None:
        from engine.herb_buffs import broom_splint_active
        from engine.injury_effects import bone_rest_activity_block

        if broom_splint_active(user):
            lines.append(
                "**Broom splint**; move at half speed; break won't worsen this sunrise."
            )
        bone_note = bone_rest_activity_block(user, day=day)
        if bone_note:
            lines.append(bone_note)

    from engine.long_term_injuries import format_long_term_injuries

    lt = format_long_term_injuries(user)
    if lt:
        lines.append(lt)

    if bool(int(user["frightened_fire"] if "frightened_fire" in user.keys() else 0)):
        lines.append(
            "**Frightened (fire):** cannot move closer to flame; disadvantage on attacks and checks "
            "while fire is in sight. Move **30+ ft** away or wait until it is out."
        )

    if day is not None:
        from engine.sacred_visits import format_sacred_visit_reminder

        sacred = format_sacred_visit_reminder(user, day)
        if sacred:
            lines.append(sacred)

    if user["condition"] and user["condition"] != "healthy" and not lines:
        lines.append(f"**{user['condition'].title()}**")

    return "\n".join(lines) if lines else "Healthy: no active conditions."


def roll_injury() -> str:
    """Roll 1d10 on the injury table."""
    roll = random.randint(1, 10)
    return INJURY_TABLE[roll - 1]


def injury_roll_label(key: str) -> str:
    info = INJURIES.get(key)
    if not info:
        return key
    roll = info.get("roll", "?")
    return f"**{info['name']}** (rolled {roll}); {info['effect']}"


def add_injury(injuries: list[str], key: str) -> list[str]:
    if key not in injuries:
        injuries = list(injuries) + [key]
    return injuries


def validate_stats(role: str, stats: dict) -> str | None:
    from rpg_rules import ROLE_ATTRIBUTE_RANGES

    lo, hi = ROLE_ATTRIBUTE_RANGES.get(role, (16, 20))
    total = sum(stats[f"attr_{k}"] for k in ("str", "dex", "con", "int", "cha", "wis"))
    for key, val in stats.items():
        if val < 1 or val > 10:
            return "Each attribute must be between 1 and 10."
    if total < lo or total > hi:
        return f"Attribute total must be {lo}–{hi} for your role (yours: {total})."
    return None


def apply_meal_energy(user, prey_bones: int) -> tuple[int, int, int]:
    """
    Eating fresh-kill restores energy: −1 exhaustion and a little HP.
    Returns (new_hp, new_exhaustion, hp_gained).
    """
    exhaustion = int(user["exhaustion"]) if "exhaustion" in user.keys() else 0
    hp = int(user["hp"])
    max_hp = effective_max_hp(user)
    hp_gain = 0
    if hp < max_hp:
        hp_gain = min(max_hp - hp, max(1, prey_bones // 25))
    new_hp = hp + hp_gain
    new_exhaustion = max(0, exhaustion - 1)
    return new_hp, new_exhaustion, hp_gain


def apply_short_rest_healing(user, herb_heal: int = 0) -> int:
    """Without herbs: not short-rest healing. With herb: 1d4+1 up to 3/day tracked externally."""
    heal = herb_heal
    new_hp = min(user["max_hp"], user["hp"] + heal)
    return new_hp


def apply_long_rest_healing(user) -> tuple[int, int]:
    """1 HP without herbs; remove 1 exhaustion. Dying and dead wolves don't benefit."""
    cond = user["condition"] if "condition" in user.keys() else "healthy"
    if cond in ("dead", "dying"):
        hp = int(user["hp"]) if user["hp"] is not None else 0
        ex = int(user["exhaustion"]) if user["exhaustion"] is not None else 0
        return hp, ex
    heal = 1
    cap = effective_max_hp(user)
    new_hp = min(cap, user["hp"] + heal)
    exhaustion = max(0, user["exhaustion"] - 1)
    return new_hp, exhaustion


def _survival_or_con_mod(user) -> int:
    """Best of Survival (Wis) or Constitution modifier for infection saves."""
    profs = parse_proficiencies(user["skill_proficiencies"])
    wis = attr_modifier(user["attr_wis"])
    if "survival" in profs:
        wis += PROFICIENCY_BONUS
    con = attr_modifier(user["attr_con"])
    return max(wis, con)


def progress_injuries(user, *, day: int | None = None) -> dict:
    """Daily injury effects at sunrise (bleeding, infection).

    Injuries with heal_days do not auto-clear; only herbs and /treat remove them.
    """
    if day is None:
        day = int(user["last_rest_day"]) if "last_rest_day" in user.keys() else 0
    injuries = parse_injuries(user["active_injuries"] if "active_injuries" in user.keys() else None)
    if not injuries:
        return {"changed": False}

    result: dict = {
        "changed": False,
        "hp_loss": 0,
        "exhaustion_gain": 0,
        "messages": [],
    }

    if "deep_gash" in injuries:
        result["changed"] = True
        result["hp_loss"] += 1
        result["messages"].append("**Deep Gash**; bleeding costs **1 HP** until bandaged.")

    if "infected_wound" in injuries:
        from engine.herb_buffs import infection_ward_active

        if infection_ward_active(user, day):
            result["changed"] = True
            result["messages"].append(
                "**Infected Wound**: infection ward active; no save needed today."
            )
        else:
            die = roll_d20()
            mod = _survival_or_con_mod(user)
            total = die + mod
            dc = 12
            result["changed"] = True
            if total < dc:
                result["hp_loss"] += 1
                result["exhaustion_gain"] += 1
                result["messages"].append(
                    f"**Infected Wound**; save {total} vs DC {dc}: fail (−1 HP, +1 exhaustion)."
                )
            else:
                result["messages"].append(
                    f"**Infected Wound**; save {total} vs DC {dc}: held steady today."
                )

    return result


def progress_disease(user) -> dict:
    """Daily disease progression roll. Returns outcome dict."""
    from engine.diseases import encode_disease, get_stage_info, parse_disease
    from engine.herb_buffs import consume_disease_save_after_roll, roll_disease_save_die

    raw = user["disease"] if "disease" in user.keys() else None
    disease_key, stage = parse_disease(raw)
    if not disease_key or not stage:
        return {"changed": False}

    info = get_stage_info(disease_key, stage)
    if not info:
        return {"changed": False}

    die, _used_adv = roll_disease_save_die(user)
    mod = _survival_or_con_mod(user)
    buff = int(user["disease_save_buff"]) if "disease_save_buff" in user.keys() else 0
    days = int(user["disease_save_buff_days"]) if "disease_save_buff_days" in user.keys() else 0
    total = die + mod
    success = total >= info["dc"]

    result: dict = {
        "changed": True,
        "die": die,
        "modifier": mod,
        "total": total,
        "dc": info["dc"],
        "success": success,
        "disease_key": disease_key,
        "stage": stage,
        "hp_loss": 0,
        "exhaustion_gain": 0,
        "hunger_loss": 0,
        "thirst_loss": 0,
        "mood_loss": 0,
        "new_stage": encode_disease(disease_key, stage),
        "cleared": False,
        "consume_disease_buff": bool(buff or days),
        "messages": [],
    }

    # Daily symptoms (always apply when configured).
    if info.get("hp_loss"):
        hp = info["hp_loss"]
        if info.get("juvenile_hp_loss") and int(user["age_months"]) < 12:
            hp = int(info["juvenile_hp_loss"])
        result["hp_loss"] += hp
    if info.get("exhaustion_gain"):
        result["exhaustion_gain"] += int(info["exhaustion_gain"])
    if info.get("hunger_loss"):
        result["hunger_loss"] += int(info["hunger_loss"])
    if info.get("thirst_loss"):
        result["thirst_loss"] += int(info["thirst_loss"])
    if info.get("mood_loss"):
        result["mood_loss"] += int(info["mood_loss"])

    symptom_bits: list[str] = []
    if result["hp_loss"]:
        symptom_bits.append(f"−**{result['hp_loss']}** HP")
    if result["exhaustion_gain"]:
        symptom_bits.append(f"+**{result['exhaustion_gain']}** exhaustion")
    if result["hunger_loss"]:
        symptom_bits.append(f"−**{result['hunger_loss']}** hunger")
    if result["thirst_loss"]:
        symptom_bits.append(f"−**{result['thirst_loss']}** thirst")
    if result["mood_loss"]:
        symptom_bits.append(f"−**{result['mood_loss']}** mood")
    if symptom_bits:
        result["messages"].append(
            f"**{info['name']}**; {'; '.join(symptom_bits)} this sunrise."
        )

    if success:
        if info.get("cure_on_save"):
            result["cleared"] = True
            result["new_stage"] = None
            result["messages"].append(
                f"**{info['name']}**; save **{total}** vs DC **{info['dc']}**: **recovered**."
            )
            return result
        if disease_key == "cough" and stage == "deadly":
            result["messages"].append(
                f"**{info['name']}**; save **{total}** vs DC **{info['dc']}**: "
                f"held steady, but fever still cost HP."
            )
        else:
            result["messages"].append(
                f"**{info['name']}**; save **{total}** vs DC **{info['dc']}**: held steady."
            )
        return result

    if info.get("next"):
        new_stage = info["next"]
        result["new_stage"] = encode_disease(disease_key, new_stage)
        nxt = get_stage_info(disease_key, new_stage)
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs DC **{info['dc']}**: "
            f"worsened to **{nxt['name'] if nxt else new_stage}**."
        )
    elif disease_key == "cough" and stage == "deadly":
        extra = random.randint(1, 4)
        result["hp_loss"] += extra
        result["exhaustion_gain"] += 1
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs DC **{info['dc']}**: "
            f"fail (−**{extra}** HP, **+1 exhaustion**)."
        )
    elif disease_key == "yellowcough":
        extra = random.randint(1, 4)
        result["hp_loss"] += extra
        result["exhaustion_gain"] += 1
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs DC **{info['dc']}**: "
            f"yellow phlegm and fever spike (−**{extra}** HP, **+1 exhaustion**)."
        )
    elif disease_key == "rot_lung" and stage == "necrosis":
        extra = random.randint(1, 3)
        result["hp_loss"] += extra
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs DC **{info['dc']}**: "
            f"lung-rot spreads (−**{extra}** HP)."
        )
    elif disease_key == "shaking_sickness" and stage == "hemorrhage":
        extra = random.randint(0, 2)
        if extra:
            result["hp_loss"] += extra
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs DC **{info['dc']}**: "
            f"bleeding continues (−**{result['hp_loss']}** HP this sunrise)."
        )
    else:
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs DC **{info['dc']}**: symptoms persist."
        )

    return result


def treat_with_herb(user, herb_key: str, herb_meta: dict) -> str:
    """Returns outcome: cured_disease, cured_injury, cured_genetic, healed, stabilized, rabies_ease, no_effect."""
    from engine.diseases import disease_matches_cure, parse_disease
    from engine.genetics import genetic_keys_matching_cures
    from engine.herb_buffs import DISEASE_DOSE_HERBS, is_cough_suppression_herb

    cures = herb_meta.get("cures", ())
    raw = user["disease"] if "disease" in user.keys() else None
    disease_key, stage = parse_disease(raw)
    injuries = parse_injuries(user["active_injuries"] if "active_injuries" in user.keys() else None)

    if (
        disease_key == "rabies"
        and stage in ("incubation", "prodrome")
        and herb_key in ("boneset", "goldenrod")
    ):
        return "rabies_ease"
    if herb_key in DISEASE_DOSE_HERBS:
        spec = DISEASE_DOSE_HERBS[herb_key]
        if disease_key == spec[0] and stage == spec[1]:
            return "cough_dose"
    if disease_key and disease_matches_cure(disease_key, stage, cures, herb_key=herb_key):
        if is_cough_suppression_herb(herb_key):
            return "symptom_ease"
        return "cured_disease"
    if genetic_keys_matching_cures(user, cures):
        return "cured_genetic"
    for inj in list(injuries):
        if inj in cures:
            return "cured_injury"
    cond = user["condition"] if "condition" in user.keys() else "healthy"
    if herb_key in ("cobwebs", "saffron") and (int(user["hp"]) <= 0 or cond == "dying"):
        return "stabilized"
    if "dying" in cures and cond == "dying":
        return "stabilized"
    if herb_key == "comfrey":
        return "healed"
    if cures and herb_meta.get("poison"):
        return "poison_herb"
    if cures:
        return "symptom_ease"
    return "no_effect"


def roll_poison_herb_misuse(user, herb_key: str, *, day: int) -> tuple[bool, str, dict]:
    """
    CON save for restricted poison herbs.
    Returns (survived_ok, message, db_fields).
    """
    import random

    import database as db

    from engine.dice import format_roll_result, resolve_check
    from engine.herb_properties import herb_form_rule
    from engine.restricted_herbs import is_restricted_herb

    if not is_restricted_herb(herb_key):
        return True, "", {}
    rule = herb_form_rule(herb_key)
    result = resolve_check(
        user,
        attr_keys=("attr_con",),
        skill="Constitution",
        dc=rule.toxic_dc,
        proficient=False,
        skill_key=None,
        game_day=day,
    )
    lo, hi = rule.toxic_damage
    dmg = random.randint(lo, hi)
    if result["success"]:
        dmg = max(1, dmg // 2)
    new_hp = max(0, int(user["hp"]) - dmg)
    db.set_user_conditions(user["discord_id"], hp=new_hp)
    note = "half damage on save" if result["success"] else "full poison damage"
    return (
        new_hp > 0,
        format_roll_result(result) + f"\n**Poison misuse**; **−{dmg} HP** ({note}).",
        {"hp": new_hp},
    )


def herb_special_effect(herb_key: str, user, *, inventory_qty: int = 1) -> str | None:
    """Non-cure herb outcomes: reduce_exhaustion, hunger_shield, ragweed_need_three, etc."""
    from config import HUNGER_LOW_THRESHOLD, THIRST_LOW_THRESHOLD
    from engine.diseases import parse_disease
    from engine.hunger import user_hunger
    from engine.thirst import user_thirst

    disease_key, _ = parse_disease(user["disease"] if "disease" in user.keys() else None)
    from engine.aging import stage_for_age

    if herb_key == "honey":
        age = int(user["age_months"] if "age_months" in user.keys() else 24)
        if stage_for_age(age) == "pup":
            if user_hunger(user) < HUNGER_LOW_THRESHOLD or user_thirst(user) < THIRST_LOW_THRESHOLD:
                return "feed_pup_honey"
            return "honey_pup_not_depleted"
        if user_hunger(user) < HUNGER_LOW_THRESHOLD or user_thirst(user) < THIRST_LOW_THRESHOLD:
            return "reduce_exhaustion"
        return "honey_needs_depletion"
    if herb_key == "fennel":
        return "hunger_shield"
    if herb_key == "burnet":
        return "march_shield"
    if herb_key == "sorrel":
        return "sorrel_restore"
    if herb_key == "slippery_elm":
        return "jaw_meal_shield"
    if herb_key == "ragweed":
        return "reduce_exhaustion" if inventory_qty >= 3 else "ragweed_need_three"
    if herb_key == "lizards_tail" and disease_key:
        return "reduce_exhaustion"
    if herb_key == "meadowsweet":
        return "reduce_exhaustion"
    if herb_key == "purslane":
        return "purslane_thirst"
    if herb_key == "honey" and not disease_key:
        return None
    return None


def medicine_check(user, dc: int = 15) -> dict:
    from engine.herb_buffs import herb_check_adjustments

    die = roll_d20()
    mod = attr_modifier(user["attr_wis"])
    profs = parse_proficiencies(user["skill_proficiencies"])
    prof = PROFICIENCY_BONUS if "medicine" in profs else 0
    from engine.role_features import is_full_medic

    if "herblore" in profs or is_full_medic(user):
        prof = max(prof, PROFICIENCY_BONUS)
    herb_mod, herb_adv = herb_check_adjustments(user, ("attr_wis",), skill_key="medicine")
    if herb_adv:
        die = max(roll_d20(), roll_d20())
    mod += herb_mod
    total = die + mod + prof
    return {
        "die": die,
        "modifier": mod,
        "proficiency": prof,
        "total": total,
        "dc": dc,
        "success": total >= dc,
    }
