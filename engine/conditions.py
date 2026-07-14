import json
import random

from engine.character import attr_modifier
from engine.exhaustion_effects import effective_max_hp
from engine.rolls import roll_d20
from herbs import EXHAUSTION_EFFECTS, INJURIES, INJURY_TABLE, SEVERE_INJURY_TABLE

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
    """show heal_days progress; injuries clear only via /treat, not time alone."""
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
        con = int(user["attr_con"]) if "attr_con" in user.keys() else 5
        survival_reduction = max(0, (con - 6) // 2)
        if survival_reduction:
            heal_days = max(1, heal_days - survival_reduction)
    start = since.get(key)
    if start is not None and day > start:
        elapsed = day - start
        return (
            f" _({elapsed}d elapsed · ~{heal_days}d with rest; "
            f"clears via `/medic action:treat` only)_"
        )
    return f" _(~{heal_days}d with rest; clears via `/medic action:treat` only)_"


def format_conditions(user, *, day: int | None = None) -> str:
    lines = []
    cond = user["condition"] if "condition" in user.keys() else "healthy"
    hp = int(user["hp"]) if "hp" in user.keys() else 1
    if cond == "dead":
        lines.append(
            "**dead**; permanently. `/rpg action:delete confirm:DELETE` then `/register` for a new wolf."
        )
    elif cond == "dying" or hp <= 0:
        rnd = (
            int(user["death_save_round"])
            if "death_save_round" in user.keys() and user["death_save_round"]
            else 1
        )
        succ = (
            int(user["death_save_successes"])
            if "death_save_successes" in user.keys() and user["death_save_successes"]
            else 0
        )
        lines.append(
            f"**dying** (death save **{rnd}**/3, **{succ}** success"
            f"{'' if succ == 1 else 'es'}); `/medic action:deathsaves` or medic "
            "`/medic action:stabilize`."
        )
    exhaustion = user["exhaustion"] if "exhaustion" in user.keys() else 0
    if exhaustion:
        from engine.exhaustion_effects import EXHAUSTION_MAX
        effect = EXHAUSTION_EFFECTS.get(exhaustion, "Unknown")
        lines.append(f"**exhaustion {exhaustion}/{EXHAUSTION_MAX}**; {effect}")

    smoke = int(user["smoke_debuff"]) if "smoke_debuff" in user.keys() else 0
    if smoke:
        lines.append("**wildfire smoke**; disadvantage on perception until next sunrise.")

    from engine.diseases import illness_displays

    for name, effect in illness_displays(user):
        lines.append(f"**{name}**; {effect}")

    from engine.quarantine import is_quarantined

    if is_quarantined(user):
        lines.append(
            "**quarantined**; isolated in the sick den; cannot spread illness or leave for pack activities."
        )

    from engine.genetics import GENETIC_CONDITIONS, parse_genetic_conditions

    for key in parse_genetic_conditions(
        user["genetic_conditions"] if user and "genetic_conditions" in user.keys() else None
    ):
        info = GENETIC_CONDITIONS[key]
        lines.append(f"**{info['name']}**; {info['effect']}")

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
                line += f"\n_treatment: {info['treatment']}_"
            lines.append(line)

    if day is not None:
        from engine.herb_buffs import broom_splint_active
        from engine.injury_effects import bone_rest_activity_block

        if broom_splint_active(user):
            lines.append(
                "**broom splint**; move at half speed; break won't worsen this sunrise."
            )
        bone_note = bone_rest_activity_block(user, day=day)
        if bone_note:
            lines.append(bone_note)

        from engine.herb_buffs import format_active_herb_buffs

        herb_buff_text = format_active_herb_buffs(user, day)
        if herb_buff_text:
            lines.append(herb_buff_text)

    from engine.long_term_injuries import format_long_term_injuries

    lt = format_long_term_injuries(user)
    if lt:
        lines.append(lt)

    if bool(int(user["frightened_fire"] if "frightened_fire" in user.keys() else 0)):
        lines.append(
            "**frightened (fire):** cannot move closer to flame; disadvantage on attacks and checks "
            "while fire is in sight. Move **30+ ft** away or wait until it is out."
        )

    if day is not None:
        from engine.sacred_visits import format_sacred_visit_reminder

        sacred = format_sacred_visit_reminder(user, day)
        if sacred:
            lines.append(sacred)

    from engine.blooding import format_blooding_status

    blooding = format_blooding_status(user)
    if blooding:
        lines.append(blooding)

    if user["condition"] and user["condition"] != "healthy" and not lines:
        lines.append(f"**{user['condition'].title()}**")

    return "\n".join(lines) if lines else "healthy: no active conditions."


def roll_injury() -> str:
    """roll 1d10 on the injury table."""
    roll = random.randint(1, 10)
    return INJURY_TABLE[roll - 1]


def roll_severe_injury() -> str:
    """roll on the severe injury table (critical hits outside spine_bite)."""
    return random.choice(SEVERE_INJURY_TABLE)




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
            return "each attribute must be between 1 and 10."
    if total < lo or total > hi:
        return f"attribute total must be {lo}; {hi} for your role (yours: {total})."
    return None


def apply_meal_energy(user, prey_bones: int) -> tuple[int, int, int]:
    """
    eating fresh-kill restores energy: −1 exhaustion and a little hp.
    returns (new_hp, new_exhaustion, hp_gained).
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






def apply_long_rest_benefits(user, *, season: str | None = None) -> dict[str, int]:
    """long rest: hp recovery, exhaustion relief, modest mood lift. does not replace eating or drinking."""
    from config import (
        HUNGER_LOW_THRESHOLD,
        LONG_REST_EXHAUSTION_RELIEF,
        LONG_REST_HP_GAIN,
        LONG_REST_MOOD_GAIN,
    )

    cond = user["condition"] if "condition" in user.keys() else "healthy"
    hp = int(user["hp"]) if user and "hp" in user.keys() and user["hp"] is not None else 0
    exhaustion = int(user["exhaustion"]) if user and "exhaustion" in user.keys() and user["exhaustion"] is not None else 0
    mood = int(user["mood"]) if user and "mood" in user.keys() and user["mood"] is not None else 50
    if cond in ("dead", "dying"):
        return {"hp": hp, "exhaustion": exhaustion, "mood": mood}
    cap = effective_max_hp(user)
    # recovery variance: injuries and hunger slow healing; winter denning helps a little
    injuries = parse_injuries(user["active_injuries"] if "active_injuries" in user.keys() else None)
    hunger = int(user["hunger"]) if "hunger" in user.keys() and user["hunger"] is not None else 100
    hp_gain = LONG_REST_HP_GAIN - len(injuries)
    if hunger < HUNGER_LOW_THRESHOLD:
        hp_gain -= 1
    if season == "winter":
        hp_gain += 1
    hp_gain = max(0, hp_gain)
    return {
        "hp": min(cap, hp + hp_gain),
        "exhaustion": max(0, exhaustion - LONG_REST_EXHAUSTION_RELIEF),
        "mood": min(100, mood + LONG_REST_MOOD_GAIN),
    }


def manual_long_rest_used_today(user, day: int) -> bool:
    """True if the player already used `/vitals` long rest this sunrise (rollover rest does not count)."""
    from engine.herb_buffs import get_buffs

    buffs = get_buffs(user)
    return int(buffs.get("manual_long_rest_day") or 0) == day


def mark_manual_long_rest(user, day: int) -> None:
    import database as db
    from engine.herb_buffs import buffs_json, get_buffs

    buffs = get_buffs(user)
    buffs["manual_long_rest_day"] = day
    db.update_user(user["discord_id"], wolf_id=user["id"], herb_buffs=buffs_json(buffs))


def _survival_or_con_mod(user) -> int:
    """Best of Survival (Wis) or Constitution modifier for infection saves."""
    from engine.character_traits import trait_check_adjustments

    wis = attr_modifier(user["attr_wis"])
    trait_mod, _ = trait_check_adjustments(
        user, ("attr_wis",), skill_key="survival", skill_label="Survival"
    )
    wis += trait_mod
    con = attr_modifier(user["attr_con"])
    return max(wis, con)


def progress_injuries(user, *, day: int | None = None) -> dict:
    """daily injury effects at sunrise (bleeding, infection).

    injuries with heal_days do not auto-clear; only herbs and /treat remove them.
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
        from engine.herb_buffs import bleed_dressed_active

        result["changed"] = True
        if bleed_dressed_active(user, day):
            result["messages"].append("**Deep Gash**; field-dressed, no bleeding this sunrise.")
        else:
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
                    f"**infected wound**; save {total} vs dc {dc}: fail (−1 hp, +1 exhaustion)."
                )
            else:
                result["messages"].append(
                    f"**infected wound**; save {total} vs dc {dc}: held steady today."
                )

    return result


def progress_disease(user, *, day: int = 0) -> dict:
    """daily disease progression roll. returns outcome dict."""
    from engine.diseases import encode_disease, get_stage_info, parse_disease
    from engine.herb_buffs import roll_disease_save_die

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
        symptom_bits.append(f"−**{result['hp_loss']}** hp")
    if result["exhaustion_gain"]:
        symptom_bits.append(f"+**{result['exhaustion_gain']}** exhaustion")
    if result["hunger_loss"]:
        symptom_bits.append(f"−**{result['hunger_loss']}** satiety")
    if result["thirst_loss"]:
        symptom_bits.append(f"−**{result['thirst_loss']}** hydration")
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
                f"**{info['name']}**; save **{total}** vs dc **{info['dc']}**: **recovered**."
            )
            return result
        if disease_key == "cough" and stage == "deadly":
            result["messages"].append(
                f"**{info['name']}**; save **{total}** vs dc **{info['dc']}**: "
                f"held steady, but fever still cost hp."
            )
        else:
            result["messages"].append(
                f"**{info['name']}**; save **{total}** vs dc **{info['dc']}**: held steady."
            )
        return result

    if info.get("next"):
        # herb-held chronic diseases stall instead of worsening this sunrise.
        from engine.diseases import is_chronic_disease

        if is_chronic_disease(disease_key):
            from engine.chronic_care import chronic_halt_active

            if chronic_halt_active(user, disease_key, day):
                result["messages"].append(
                    f"**{info['name']}**; save **{total}** vs dc **{info['dc']}**: "
                    f"held at bay by herb-care; it does not worsen."
                )
                return result
        new_stage = info["next"]
        result["new_stage"] = encode_disease(disease_key, new_stage)
        nxt = get_stage_info(disease_key, new_stage)
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs dc **{info['dc']}**: "
            f"worsened to **{nxt['name'] if nxt else new_stage}**."
        )
    elif disease_key == "cough" and stage == "deadly":
        extra = random.randint(1, 4)
        result["hp_loss"] += extra
        result["exhaustion_gain"] += 1
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs dc **{info['dc']}**: "
            f"fail (−**{extra}** hp, **+1 exhaustion**)."
        )
    elif disease_key == "yellowcough":
        extra = random.randint(1, 4)
        result["hp_loss"] += extra
        result["exhaustion_gain"] += 1
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs dc **{info['dc']}**: "
            f"yellow phlegm and fever spike (−**{extra}** hp, **+1 exhaustion**)."
        )
    elif disease_key == "rot_lung" and stage == "necrosis":
        extra = random.randint(1, 3)
        result["hp_loss"] += extra
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs dc **{info['dc']}**: "
            f"lung-rot spreads (−**{extra}** hp)."
        )
    elif disease_key == "shaking_sickness" and stage == "hemorrhage":
        extra = random.randint(0, 2)
        if extra:
            result["hp_loss"] += extra
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs dc **{info['dc']}**: "
            f"bleeding continues (−**{result['hp_loss']}** hp this sunrise)."
        )
    else:
        result["messages"].append(
            f"**{info['name']}**; save **{total}** vs dc **{info['dc']}**: symptoms persist."
        )

    return result


def progress_mental_overlay(user) -> dict:
    """progress fever-delirium stored in herb_buffs.mental_disease."""
    from engine.herb_buffs import get_buffs, merge_buff_fields

    overlay = get_buffs(user).get("mental_disease")
    if not overlay:
        return {"changed": False}
    pseudo = dict(user)
    pseudo["disease"] = str(overlay)
    outcome = progress_disease(pseudo)
    if not outcome.get("changed"):
        return outcome
    if outcome.get("cleared"):
        buff_fields = merge_buff_fields(user, mental_disease=False)
    else:
        buff_fields = merge_buff_fields(user, mental_disease=outcome["new_stage"])
    outcome["buff_fields"] = buff_fields
    outcome["overlay_only"] = True
    return outcome


def brief_condition_blurb(user, *, day: int | None = None) -> str | None:
    """one-line illness + herb buff summary for combat and activity embeds."""
    from engine.diseases import illness_displays
    from engine.herb_buffs import format_active_herb_buffs

    bits: list[str] = []
    for name, _effect in illness_displays(user):
        bits.append(f"**{name}**")
    if day is not None:
        herbs = format_active_herb_buffs(user, day)
        if herbs:
            first = herbs.split("\n", 1)[0]
            bits.append(first)
    from engine.quarantine import is_quarantined

    if is_quarantined(user):
        bits.append("**Quarantined**")
    return " · ".join(bits) if bits else None


def treat_with_herb(user, herb_key: str, herb_meta: dict) -> str:
    """returns outcome: cured_disease, cured_injury, cured_genetic, healed, stabilized, rabies_ease, no_effect."""
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
        return None
    if herb_key == "purslane":
        return "purslane_thirst"
    if herb_key == "cobnuts":
        return "cobnuts_energy"
    if herb_key == "honey" and not disease_key:
        return None
    return None


def medicine_check(user, dc: int = 15) -> dict:
    from engine.character_traits import trait_check_adjustments
    from engine.herb_buffs import herb_check_adjustments

    die = roll_d20()
    mod = attr_modifier(user["attr_wis"])
    trait_mod, _ = trait_check_adjustments(
        user, ("attr_wis",), skill_key="medicine", skill_label="Medicine"
    )
    herb_mod, herb_adv = herb_check_adjustments(user, ("attr_wis",), skill_key="medicine")
    if herb_adv:
        die = max(roll_d20(), roll_d20())
    mod += herb_mod
    total = die + mod + trait_mod
    return {
        "die": die,
        "modifier": mod,
        "proficiency": trait_mod,
        "total": total,
        "dc": dc,
        "success": total >= dc,
    }
