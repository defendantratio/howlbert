"""Timed and one-shot herb effect buffs (stored as JSON on users.herb_buffs)."""

from __future__ import annotations

import json

from engine.rolls import roll_d20

BONE_INJURY_KEYS = frozenset(
    {"sprained_leg", "fractured_rib", "broken_jaw", "spinal_injury", "punctured_paw"}
)

# Cough and mental illness cures requiring multiple doses before stage clears
# (disease_key, stage, doses, window kind)
DISEASE_DOSE_HERBS: dict[str, tuple[str, str, int, str]] = {
    "chickweed": ("cough", "mild", 3, "cumulative"),
    "coltsfoot": ("cough", "mild", 1, "cumulative"),
    "catmint": ("cough", "severe", 2, "24h"),
    "pine_needle": ("cough", "severe", 2, "24h"),
    "valerian": ("insomnia", "sleepless", 2, "24h"),
    "lavender": ("insomnia", "sleepless", 2, "24h"),
    "chamomile": ("anxiety", "uneasy", 2, "24h"),
    "dried_skullcap": ("delirium", "wandering", 2, "cumulative"),
}

# Backward compat alias
COUGH_DOSE_HERBS: dict[str, tuple[str, int, str]] = {
    k: (stage, doses, window)
    for k, (disease, stage, doses, window) in DISEASE_DOSE_HERBS.items()
    if disease == "cough"
}

# Symptom suppression only; never hard-clear cough stages via /treat
COUGH_SUPPRESSION_HERBS = frozenset({"wild_cherry_bark", "labrador_tea", "thyme"})

POISON_MISUSE_HERBS = frozenset({"bloodroot", "oleander", "water_hemlock"})


def get_buffs(user) -> dict:
    raw = user["herb_buffs"] if user and "herb_buffs" in user.keys() else "{}"
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def buffs_json(buffs: dict) -> str:
    cleaned = {k: v for k, v in buffs.items() if v not in (None, 0, False, "", [])}
    return json.dumps(cleaned) if cleaned else "{}"


def merge_buff_fields(user, **updates) -> dict:
    """return db fields to set (herb_buffs plus scalar columns when used)."""
    buffs = get_buffs(user)
    scalar_keys = {
        "disease_save_buff",
        "disease_save_buff_days",
        "distressed",
        "extra_pup_milk",
    }
    fields: dict = {}
    for key, value in updates.items():
        if key in scalar_keys:
            fields[key] = value
        elif value is not None:
            if value in (0, False):
                buffs.pop(key, None)
            else:
                buffs[key] = value
    fields["herb_buffs"] = buffs_json(buffs)
    return fields


def grant_disease_save_advantage(user, *, days: int = 0) -> dict:
    """advantage on disease saves. days=0 means one save only."""
    fields = {"disease_save_buff": 1}
    if days > 0:
        fields["disease_save_buff_days"] = days
    return fields


def disease_save_uses_advantage(user) -> bool:
    days = int(user["disease_save_buff_days"]) if "disease_save_buff_days" in user.keys() else 0
    flag = int(user["disease_save_buff"]) if "disease_save_buff" in user.keys() else 0
    if flag > 0 or days > 0:
        return True
    buffs = get_buffs(user)
    day = int(user["last_rest_day"]) if user and "last_rest_day" in user.keys() else 0
    if buffs.get("sleep_aid_until_day") and int(buffs["sleep_aid_until_day"]) >= day:
        from engine.diseases import is_mental_disease, parse_disease

        disease_key, _ = parse_disease(user["disease"] if "disease" in user.keys() else None)
        if is_mental_disease(disease_key):
            return True
    return False


def roll_disease_save_die(user) -> tuple[int, bool]:
    if disease_save_uses_advantage(user):
        return max(roll_d20(), roll_d20()), True
    return roll_d20(), False


def consume_disease_save_after_roll(user) -> dict:
    """after a disease progression save, clear single-use buff unless multi-day."""
    days = int(user["disease_save_buff_days"]) if "disease_save_buff_days" in user.keys() else 0
    if days > 0:
        return {}
    if int(user["disease_save_buff"]) if "disease_save_buff" in user.keys() else 0:
        return {"disease_save_buff": 0}
    return {}


def tick_disease_save_days(user, new_day: int) -> dict:
    days = int(user["disease_save_buff_days"]) if "disease_save_buff_days" in user.keys() else 0
    if days <= 0:
        return {}
    remaining = days - 1
    if remaining > 0:
        return {"disease_save_buff_days": remaining, "disease_save_buff": 1}
    return {"disease_save_buff_days": 0, "disease_save_buff": 0}


def tick_buffs_for_rollover(user, new_day: int) -> dict:
    buffs = get_buffs(user)
    fields: dict = {}
    until_keys = (
        "pain_relief_until_day",
        "fear_immune_until_day",
        "sedated_until_day",
        "sleep_aid_until_day",
        "calm_until_day",
        "elder_hunt_speed_until_day",
        "infection_ward_until_day",
        "herb_storage_bonus_until_day",
        "frostbite_until_day",
        "flea_ward_until_day",
        "death_scent_masked_until_day",
        "courtship_blocked_until_day",
    )
    for key in until_keys:
        if buffs.get(key) and int(buffs[key]) < new_day:
            buffs.pop(key, None)
    # Clear one-shot injury buffs at sunrise
    for key in ("injury_heal_halved", "bone_heal_days_reduced", "broom_splint"):
        buffs.pop(key, None)
    fields["herb_buffs"] = buffs_json(buffs)
    fields.update(tick_disease_save_days(user, new_day))
    return fields


def injury_heal_multiplier(user) -> float:
    """arnica/tansy halve displayed and effective sprain recovery time."""
    return 0.5 if get_buffs(user).get("injury_heal_halved") else 1.0


def bone_heal_days_reduction(user) -> int:
    """flat days off bone-injury recovery (bindweed, stinging nettle + comfrey)."""
    return int(get_buffs(user).get("bone_heal_days_reduced") or 0)


def infection_ward_active(user, day: int) -> bool:
    until = get_buffs(user).get("infection_ward_until_day")
    return bool(until and int(until) >= day)


def frostbite_dex_penalty(user, day: int) -> int:
    until = get_buffs(user).get("frostbite_until_day")
    if until and int(until) >= day:
        return -1
    return 0


def grant_frostbite(user, *, day: int, duration: int = 7) -> dict:
    return merge_buff_fields(user, frostbite_until_day=day + duration)


def clear_frostbite(user) -> dict:
    buffs = get_buffs(user)
    if "frostbite_until_day" not in buffs:
        return {}
    buffs.pop("frostbite_until_day", None)
    return {"herb_buffs": buffs_json(buffs)}


def grant_flea_ward(user, *, day: int, duration: int = 3) -> dict:
    """insect-repellent oils (mugwort, garlic mustard, knotgrass)."""
    return merge_buff_fields(user, flea_ward_until_day=day + duration)


def flea_ward_active(user, day: int) -> bool:
    until = get_buffs(user).get("flea_ward_until_day")
    return bool(until and int(until) >= day)


def burial_scent_masked(user, day: int) -> bool:
    until = get_buffs(user).get("death_scent_masked_until_day")
    return bool(until and int(until) >= day)


def grant_burial_scent_mask(user, *, day: int, duration: int = 3) -> dict:
    return merge_buff_fields(user, death_scent_masked_until_day=day + duration)


def courtship_blocked(user, day: int) -> bool:
    until = get_buffs(user).get("courtship_blocked_until_day")
    return bool(until and int(until) >= day)


def grant_courtship_block(user, *, day: int) -> dict:
    """block courtship approaches until next sunrise (end of current day)."""
    return merge_buff_fields(user, courtship_blocked_until_day=day)


def is_cough_suppression_herb(herb_key: str) -> bool:
    return herb_key in COUGH_SUPPRESSION_HERBS


def apply_cough_dose(user, herb_key: str, *, day: int) -> tuple[bool, dict, str]:
    """
    Track multi-dose cough herbs. Returns (stage_cured, db_fields, progress_message).
    """
    return apply_disease_dose(user, herb_key, day=day)


def apply_disease_dose(user, herb_key: str, *, day: int) -> tuple[bool, dict, str]:
    """
    Track multi-dose disease herbs (cough and mental). Returns (stage_cured, db_fields, progress_message).
    """
    from engine.diseases import parse_disease

    spec = DISEASE_DOSE_HERBS.get(herb_key)
    if not spec:
        return True, {}, ""
    disease_required, stage_required, doses_needed, window = spec
    disease_key, stage = parse_disease(user["disease"] if "disease" in user.keys() else None)
    if disease_key != disease_required or stage != stage_required:
        return False, {}, f"**{herb_key.replace('_', ' ').title()}** does not match this illness stage."

    buffs = get_buffs(user)
    dose_key = f"{disease_key}:{herb_key}"
    doses = dict(buffs.get("disease_doses") or {})
    count = int(doses.get(dose_key, 0))

    if window == "24h":
        window_day = buffs.get("disease_dose_window_day")
        if window_day is not None and int(window_day) != day:
            doses = {dose_key: 1}
            fields = merge_buff_fields(
                user, disease_doses=doses, disease_dose_window_day=day
            )
            return False, fields, f"dose **1/{doses_needed}**; next dose before next sunrise."
        count += 1
        doses[dose_key] = count
        fields = merge_buff_fields(
            user, disease_doses=doses, disease_dose_window_day=day
        )
    else:
        count += 1
        doses[dose_key] = count
        fields = merge_buff_fields(user, disease_doses=doses)

    if count >= doses_needed:
        cleaned = merge_buff_fields(
            user, disease_doses=False, disease_dose_window_day=False
        )
        fields.update(cleaned)
        label = disease_required.replace("_", " ").title()
        return True, fields, f"dose **{count}/{doses_needed}**; **{label}** breaks."

    return False, fields, f"dose **{count}/{doses_needed}**; keep dosing."


def herb_check_adjustments(
    user,
    attr_keys: tuple[str, ...],
    *,
    skill_key: str | None = None,
) -> tuple[int, bool]:
    """Flat modifier and advantage for skill checks from herb buffs."""
    buffs = get_buffs(user)
    mod = 0
    advantage = False
    if buffs.get("hunt_stealth_bonus") and skill_key == "stealth":
        mod += int(buffs["hunt_stealth_bonus"])
    if buffs.get("medicine_bonus_next") and skill_key in ("medicine", "herblore", None):
        if skill_key or "attr_wis" in attr_keys:
            mod += int(buffs["medicine_bonus_next"])
    if buffs.get("fear_immune_until_day"):
        day = int(user["last_rest_day"]) if "last_rest_day" in user.keys() else 0
        if int(buffs["fear_immune_until_day"]) >= day and skill_key in (
            "intimidation",
            "insight",
            None,
        ):
            advantage = True
    if buffs.get("calm_until_day"):
        day = int(user["last_rest_day"]) if "last_rest_day" in user.keys() else 0
        if int(buffs["calm_until_day"]) >= day and skill_key in (
            "intimidation",
            "insight",
            "persuasion",
            None,
        ):
            advantage = True
    if buffs.get("venom_save_advantage") and skill_key in ("survival", "medicine", None):
        if "attr_con" in attr_keys or "attr_wis" in attr_keys:
            advantage = True
    return mod, advantage


def consume_herb_check_buffs(user, *, skill_key: str | None = None) -> dict:
    buffs = get_buffs(user)
    changed = False
    if buffs.get("hunt_stealth_bonus") and skill_key == "stealth":
        buffs.pop("hunt_stealth_bonus", None)
        changed = True
    if buffs.get("medicine_bonus_next") and skill_key in ("medicine", "herblore", None):
        buffs.pop("medicine_bonus_next", None)
        changed = True
    if buffs.get("venom_save_advantage") and skill_key in ("survival", "medicine", None):
        buffs.pop("venom_save_advantage", None)
        changed = True
    if not changed:
        return {}
    return {"herb_buffs": buffs_json(buffs)}


def pain_relief_active(user, day: int) -> bool:
    buffs = get_buffs(user)
    until = buffs.get("pain_relief_until_day")
    return bool(until and int(until) >= day)


def elder_hunt_speed_active(user, day: int | None = None) -> bool:
    buffs = get_buffs(user)
    until = buffs.get("elder_hunt_speed_until_day")
    if not until:
        return False
    if day is None:
        return True
    return int(until) >= day


def broom_splint_active(user) -> bool:
    return bool(get_buffs(user).get("broom_splint"))


def birth_save_has_advantage(user) -> bool:
    return bool(get_buffs(user).get("birth_save_advantage"))


def consume_birth_save_advantage(user) -> dict:
    buffs = get_buffs(user)
    if not buffs.pop("birth_save_advantage", None):
        return {}
    return {"herb_buffs": buffs_json(buffs)}


def death_save_bonus(user) -> int:
    return int(get_buffs(user).get("death_save_bonus_next") or 0)


def consume_death_save_bonus(user) -> dict:
    buffs = get_buffs(user)
    if not buffs.pop("death_save_bonus_next", None):
        return {}
    return {"herb_buffs": buffs_json(buffs)}


def extra_pup_milk(user) -> bool:
    if int(user["extra_pup_milk"]) if user and "extra_pup_milk" in user.keys() else 0:
        return True
    return bool(get_buffs(user).get("extra_pup_milk"))


def herb_storage_multiplier(user, day: int) -> float:
    buffs = get_buffs(user)
    until = buffs.get("herb_storage_bonus_until_day")
    if until and int(until) >= day:
        return 1.5
    return 1.0


def apply_supplemental_herb(herb_key: str, user, *, day: int, outcome: str) -> dict | None:
    """
    extra mechanical effects after /treat. returns {kind, message, fields} or none.
    runs even when a cure path fired (stacking buffs).
    """
    from engine.diseases import parse_disease
    from engine.role_features import is_full_medic

    disease_key, cough_stage = parse_disease(
        user["disease"] if "disease" in user.keys() else None
    )
    cond = user["condition"] if "condition" in user.keys() else "healthy"
    mood = int(user["mood"]) if "mood" in user.keys() else 75
    fields: dict = {}
    from engine.conditions import parse_injuries

    injuries = parse_injuries(
        user["active_injuries"] if "active_injuries" in user.keys() else None
    )
    injury_set = set(injuries)

    # --- disease save herbs ---
    if herb_key == "elderberry":
        fields.update(grant_disease_save_advantage(user, days=3))
        return {
            "kind": "disease_save_buff",
            "message": "advantage on disease saves for **3 sunrises**.",
            "fields": fields,
        }
    if herb_key in ("boneset", "feverfew", "lambs_ear", "coneflower", "wild_garlic"):
        fields.update(grant_disease_save_advantage(user))
        label = herb_key.replace("_", " ").title()
        return {
            "kind": "disease_save_buff",
            "message": f"**{label}**: advantage on your next disease save.",
            "fields": fields,
        }
    if herb_key == "douglas_sagewort":
        fields.update(grant_disease_save_advantage(user))
        fields.update(
            merge_buff_fields(
                user,
                infection_ward_until_day=day + 1,
                fear_immune_until_day=day + 1,
                calm_until_day=day + 1,
            )
        )
        if disease_key in ("chronic_stress", "anxiety", "pack_madness"):
            return {
                "kind": "disease_save_buff",
                "message": "stress warded **1 sunrise**; advantage vs fear and mental illness saves.",
                "fields": fields,
            }
        return {
            "kind": "disease_save_buff",
            "message": "infection warded **1 sunrise**; advantage vs fear until next sunrise.",
            "fields": fields,
        }

    if herb_key in ("wild_cherry_bark", "labrador_tea", "edelweiss", "sage", "thyme"):
        if disease_key in ("cough", "yellowcough"):
            fields["cough_suppressed"] = 1
            return {
                "kind": "symptom_relief",
                "message": "throat eases: coughing suppressed until next sunrise.",
                "fields": fields,
            }
        fields.update(merge_buff_fields(user, pain_relief_until_day=day))
        return {
            "kind": "minor_relief",
            "message": "minor pain and throat irritation fade for the sunrise.",
            "fields": fields,
        }

    if herb_key == "chamomile":
        fields.update(
            merge_buff_fields(
                user,
                fear_immune_until_day=day + 1,
                calm_until_day=day + 1,
                distressed=0,
            )
        )
        fields["mood"] = min(100, mood + 5)
        if disease_key in ("anxiety", "insomnia", "grief_melancholy", "shock_emotional"):
            return {
                "kind": "minor_relief",
                "message": "calm spreads: advantage vs fear until next sunrise; eases troubled mind.",
                "fields": fields,
            }
        return {
            "kind": "minor_relief",
            "message": "calm spreads: advantage vs fear until next sunrise.",
            "fields": fields,
        }

    if herb_key == "valerian":
        fields.update(
            merge_buff_fields(
                user,
                sedated_until_day=day + 1,
                sleep_aid_until_day=day + 1,
            )
        )
        fields["mood"] = min(100, mood + 6)
        if disease_key in ("insomnia", "night_terrors", "anxiety", "shock_emotional"):
            fields.update(grant_disease_save_advantage(user))
            return {
                "kind": "minor_relief",
                "message": (
                    "strong sedative: deep rest until next sunrise; "
                    "advantage on next mental illness save."
                ),
                "fields": fields,
            }
        return {
            "kind": "minor_relief",
            "message": "sedative: deep rest until next sunrise (**no strenuous field work**).",
            "fields": fields,
        }

    if herb_key == "poppy_seeds":
        fields.update(
            merge_buff_fields(
                user,
                sedated_until_day=day + 1,
                sleep_aid_until_day=day + 1,
                pain_relief_until_day=day + 1,
            )
        )
        fields["mood"] = min(100, mood + 4)
        if disease_key in ("insomnia", "anxiety", "shock_emotional", "night_terrors"):
            return {
                "kind": "minor_relief",
                "message": "sedative: unconscious rest until next sunrise; pain and panic fade.",
                "fields": fields,
            }
        return {
            "kind": "minor_relief",
            "message": "sedative: unconscious rest until next sunrise.",
            "fields": fields,
        }

    if herb_key in ("dandelion", "daisy", "willow_bark", "oxeye_daisy", "chicory", "garden_mint", "wood_sorrel"):
        fields.update(merge_buff_fields(user, pain_relief_until_day=day))
        fields["mood"] = min(100, mood + 3)
        return {
            "kind": "minor_relief",
            "message": "pain and nausea ease for the sunrise.",
            "fields": fields,
        }

    if herb_key == "blackberry":
        fields.update(merge_buff_fields(user, venom_save_advantage=True, pain_relief_until_day=day))
        fields["mood"] = min(100, mood + 2)
        return {
            "kind": "minor_relief",
            "message": "stings soothed; advantage on the next venom save.",
            "fields": fields,
        }

    if herb_key in ("snakeroot", "sticklewort", "adders_tongue"):
        fields.update(merge_buff_fields(user, venom_save_advantage=True))
        return {
            "kind": "minor_relief",
            "message": "advantage on the next venom or poison save.",
            "fields": fields,
        }

    if herb_key == "cobnuts":
        fields.update(merge_buff_fields(user, hunt_stealth_bonus=1))
        return {
            "kind": "minor_relief",
            "message": "**+1** on your next stealth approach this sunrise.",
            "fields": fields,
        }

    if herb_key == "tormentil":
        fields.update(merge_buff_fields(user, medicine_bonus_next=2))
        return {
            "kind": "minor_relief",
            "message": "**+2** on your next medicine or herblore treatment check.",
            "fields": fields,
        }

    if herb_key == "horsetail":
        fields.update(merge_buff_fields(user, death_save_bonus_next=3))
        return {
            "kind": "minor_relief",
            "message": "**+3** on the next stabilize or death save attempt.",
            "fields": fields,
        }

    if herb_key == "rush_stalks":
        fields.update(merge_buff_fields(user, medicine_bonus_next=2))
        return {
            "kind": "minor_relief",
            "message": "**+2 medicine** setting fractures on the next treatment.",
            "fields": fields,
        }

    if herb_key == "ragwort":
        fields.update(merge_buff_fields(user, elder_hunt_speed_until_day=day + 1))
        return {
            "kind": "minor_relief",
            "message": "elders hunt at full speed for **1 sunrise** (ignores frailty penalty).",
            "fields": fields,
        }

    if herb_key == "raspberry_leaves":
        fields.update(merge_buff_fields(user, birth_save_advantage=True))
        return {
            "kind": "minor_relief",
            "message": "advantage on the next birth hemorrhage save.",
            "fields": fields,
        }

    if herb_key == "borage":
        fields.update(merge_buff_fields(user, calm_until_day=day + 1, fear_immune_until_day=day + 1))
        if disease_key in ("anxiety", "grief_melancholy"):
            fields["mood"] = min(100, mood + 4)
            return {
                "kind": "minor_relief",
                "message": "courage returns; nerves steady until next sunrise.",
                "fields": fields,
            }
        fields["extra_pup_milk"] = 1
        return {
            "kind": "minor_relief",
            "message": "nursing strength: **+1 pup** on the next litter if birth succeeds.",
            "fields": fields,
        }

    if herb_key == "parsley":
        fields["extra_pup_milk"] = 0
        return {
            "kind": "minor_relief",
            "message": "milk dries within the sunrise: lactation ends.",
            "fields": fields,
        }

    if herb_key == "broom":
        fields.update(merge_buff_fields(user, broom_splint=True))
        return {
            "kind": "minor_relief",
            "message": "splint bound: move at half speed without worsening breaks this sunrise.",
            "fields": fields,
        }

    if herb_key == "bindweed" and (
        outcome in ("cured_injury", "healed", "symptom_ease") or injury_set & BONE_INJURY_KEYS
    ):
        fields.update(merge_buff_fields(user, bone_heal_days_reduced=7))
        return {
            "kind": "minor_relief",
            "message": "splint lashed: bone healing **−7 days** on supported breaks.",
            "fields": fields,
        }

    if herb_key == "catchweed":
        fields.update(merge_buff_fields(user, pain_relief_until_day=day + 1))
        return {
            "kind": "minor_relief",
            "message": "poultice held: pain relief lasts an extra sunrise.",
            "fields": fields,
        }

    if herb_key == "beech_leaves":
        fields.update(
            merge_buff_fields(
                user,
                infection_ward_until_day=day + 1,
                herb_storage_bonus_until_day=day + 14,
            )
        )
        return {
            "kind": "infection_ward",
            "message": (
                "nut oil on the wound: **infection ward** until next sunrise; "
                "leaf wraps keep stored herbs **50% longer** for **2 weeks**."
            ),
            "fields": fields,
        }

    if herb_key == "ivy_vines":
        fields.update(merge_buff_fields(user, herb_storage_bonus_until_day=day + 14))
        return {
            "kind": "minor_relief",
            "message": "ivy wrapping: herbs in your bag keep **50% longer** before fading (**2 weeks**).",
            "fields": fields,
        }

    if herb_key == "mountain_ash":
        fields.update(grant_disease_save_advantage(user))
        return {
            "kind": "disease_save_buff",
            "message": "spirit ward: advantage on the next disease save within the den.",
            "fields": fields,
        }

    if herb_key == "arnica" and injury_set & {"sprained_leg", "punctured_paw"}:
        fields.update(merge_buff_fields(user, injury_heal_halved=True))
        return {
            "kind": "minor_relief",
            "message": "bruise poultice: sprain recovery time **halved**.",
            "fields": fields,
        }

    if herb_key == "tansy" and "sprained_leg" in injury_set:
        fields.update(merge_buff_fields(user, injury_heal_halved=True))
        return {
            "kind": "minor_relief",
            "message": "sprain recovery time **halved** with rest.",
            "fields": fields,
        }

    if herb_key == "stinging_nettle" and injury_set & BONE_INJURY_KEYS:
        fields.update(merge_buff_fields(user, bone_heal_days_reduced=1))
        return {
            "kind": "minor_relief",
            "message": "with comfrey binding: **−1 day** off broken-bone healing.",
            "fields": fields,
        }

    if herb_key == "daisy" and injury_set & {"sprained_leg", "fractured_rib"}:
        fields.update(merge_buff_fields(user, pain_relief_until_day=day + 1))
        return {
            "kind": "minor_relief",
            "message": "joint ache fades: ignore arthritis pain penalties **1 sunrise**.",
            "fields": fields,
        }

    if herb_key == "dried_skullcap":
        fields.update(
            merge_buff_fields(
                user,
                sedated_until_day=day + 1,
                calm_until_day=day + 1,
            )
        )
        if disease_key in ("delirium", "anxiety", "dementia", "pack_madness", "obsession"):
            fields.update(grant_disease_save_advantage(user))
            return {
                "kind": "minor_relief",
                "message": (
                    "sedative rest **1 sunrise**; advantage on next mental illness save."
                ),
                "fields": fields,
            }
        return {
            "kind": "minor_relief",
            "message": "sedative rest **1 sunrise** (concussion / fevered mind).",
            "fields": fields,
        }

    if herb_key == "sweet_sedge":
        fields.update(grant_disease_save_advantage(user))
        return {
            "kind": "disease_save_buff",
            "message": "sap coats the gut: advantage on the next disease save.",
            "fields": fields,
        }

    if herb_key == "deathberries" and is_full_medic(user) and (cond == "dying" or int(user["hp"]) <= 0):
        return {
            "kind": "mercy",
            "message": "mercy dose: suffering ends under medic care.",
            "fields": {"condition": "dead", "hp": 0},
        }

    if herb_key == "saffron" and cond == "dying" and outcome != "stabilized":
        return {
            "kind": "stabilize",
            "message": "postpartum hemorrhage stabilized at **1 hp**.",
            "fields": {"hp": 1, "condition": "stable"},
        }

    if herb_key in ("mugwort", "garlic_mustard"):
        label = "Mugwort" if herb_key == "mugwort" else "Garlic mustard"
        ward_updates: dict = {"flea_ward_until_day": day + 3}
        if herb_key == "mugwort":
            ward_updates["infection_ward_until_day"] = day + 1
        fields.update(merge_buff_fields(user, **ward_updates))
        fields["mood"] = min(100, mood + 2)
        msg = (
            f"**{label}** rubbed through the pelt: fleas and mites scatter "
            "(**+2 mood**); **flea ward 3 sunrises**."
        )
        if disease_key in ("fleas", "mange"):
            fields.update(grant_disease_save_advantage(user))
            msg += " Antifungal oils ease the infestation."
        elif herb_key == "garlic_mustard" and disease_key:
            fields.update(grant_disease_save_advantage(user))
            msg += " Wild-garlic bite: advantage on the next disease save."
        return {"kind": "minor_relief", "message": msg, "fields": fields}

    if herb_key == "rosemary":
        fields["mood"] = min(100, mood + 3)
        if disease_key in ("dementia", "grief_melancholy", "obsession"):
            fields.update(grant_disease_save_advantage(user))
            return {
                "kind": "minor_relief",
                "message": (
                    "scent steadies memory and grief; advantage on next mental illness save."
                ),
                "fields": fields,
            }
        return {
            "kind": "minor_relief",
            "message": "death-scent masked; den mood steadies (**+3 mood**).",
            "fields": fields,
        }

    if herb_key == "common_mallow":
        cap = int(user["max_hp"])
        hp = min(cap, int(user["hp"]) + 1)
        return {"kind": "heal", "message": "soft poultice: **+1 hp**.", "fields": {"hp": hp}}

    if herb_key == "plantain":
        cap = int(user["max_hp"])
        hp = min(cap, int(user["hp"]) + 1)
        return {"kind": "heal", "message": "gentle poultice: **+1 hp**.", "fields": {"hp": hp}}

    if (
        disease_key == "rabies"
        and cough_stage in ("incubation", "prodrome")
        and herb_key in ("goldenrod", "boneset")
    ):
        fields.update(grant_disease_save_advantage(user))
        label = herb_key.replace("_", " ").title()
        return {
            "kind": "disease_save_buff",
            "message": (
                f"**{label}** may slow cloudmouth: advantage on the next disease save "
                "(no cure)."
            ),
            "fields": fields,
        }

    if herb_key == "goldenrod" and outcome not in ("cured_disease", "cured_injury"):
        from engine.exhaustion_effects import effective_max_hp

        cap = effective_max_hp(user)
        hp = min(cap, int(user["hp"] if "hp" in user.keys() else cap) + 2)
        return {
            "kind": "heal",
            "message": "restful poultice: **+2 hp** over the next rest.",
            "fields": {"hp": hp},
        }

    if herb_key in ("chervil", "watermint", "juniper_berry", "lavender"):
        bump = {"chervil": 4, "watermint": 3, "juniper_berry": 2, "lavender": 4}[herb_key]
        if herb_key == "juniper_berry" and disease_key:
            return None
        fields.update(merge_buff_fields(user, calm_until_day=day + 1, sleep_aid_until_day=day + 1))
        fields["mood"] = min(100, mood + bump)
        if disease_key in ("insomnia", "anxiety", "grief_melancholy", "night_terrors"):
            return {
                "kind": "minor_relief",
                "message": "calm and sleep come easier until next sunrise.",
                "fields": fields,
            }
        return {
            "kind": "minor_relief",
            "message": "gut and fever symptoms ease.",
            "fields": fields,
        }

    if herb_key == "meadowsweet":
        fields.update(
            merge_buff_fields(
                user,
                pain_relief_until_day=day + 1,
                calm_until_day=day + 1,
                pain_exhaustion_skip=1,
            )
        )
        fields["mood"] = min(100, mood + 3)
        msg = "Pain and stress ease; ignore **1** pain exhaustion this sunrise."
        if disease_key in ("chronic_stress", "eating_distress"):
            msg = "Pain and stress ease; chronic strain loosens until next sunrise."
        return {
            "kind": "minor_relief",
            "message": msg,
            "fields": fields,
        }

    if herb_key == "passionflower":
        fields.update(
            merge_buff_fields(
                user,
                calm_until_day=day + 1,
                sleep_aid_until_day=day + 1,
                fear_immune_until_day=day + 1,
            )
        )
        fields["mood"] = min(100, mood + 4)
        if disease_key in ("anxiety", "insomnia", "night_terrors"):
            fields.update(grant_disease_save_advantage(user))
            return {
                "kind": "minor_relief",
                "message": "dreams soften; advantage on next mental illness save until next sunrise.",
                "fields": fields,
            }
        return {
            "kind": "minor_relief",
            "message": "nerves unclench until next sunrise.",
            "fields": fields,
        }

    if herb_key == "catmint" and disease_key == "anxiety":
        fields.update(merge_buff_fields(user, calm_until_day=day + 1, distressed=0))
        fields["mood"] = min(100, mood + 3)
        return {
            "kind": "minor_relief",
            "message": "warrior-cat calm: anxiety eases until next sunrise.",
            "fields": fields,
        }

    if herb_key == "prickly_ash":
        buffs = get_buffs(user)
        buffs.pop("frostbite_until_day", None)
        buffs["pain_relief_until_day"] = day
        fields["herb_buffs"] = buffs_json(buffs)
        return {
            "kind": "minor_relief",
            "message": (
                "warming bark ends frozen-paw numbness; tooth pain numbed for the sunrise."
            ),
            "fields": fields,
        }

    if herb_key == "dock":
        fields.update(merge_buff_fields(user, pain_relief_until_day=day))
        fields["mood"] = min(100, mood + 2)
        return {
            "kind": "minor_relief",
            "message": "dock leaf soothes cracked pads and stinging skin **1 sunrise**.",
            "fields": fields,
        }

    if herb_key == "alder_bark":
        fields.update(merge_buff_fields(user, pain_relief_until_day=day))
        fields["mood"] = min(100, mood + 2)
        return {
            "kind": "minor_relief",
            "message": "chewed bark numbs toothache and sore gums **1 sunrise**.",
            "fields": fields,
        }

    if herb_key == "celandine":
        fields.update(merge_buff_fields(user, pain_relief_until_day=day + 1))
        if outcome == "cured_genetic":
            return {
                "kind": "minor_relief",
                "message": "eye clouding clears within the sunrise.",
                "fields": fields,
            }
        return {
            "kind": "minor_relief",
            "message": "milky sap eases eye strain and surface wounds **1 sunrise**.",
            "fields": fields,
        }

    if herb_key == "witch_hazel":
        buff_updates = {
            "pain_relief_until_day": day + 1,
            "venom_save_advantage": True,
        }
        if injury_set & {"sprained_leg", "punctured_paw", "torn_ear"}:
            buff_updates["injury_heal_halved"] = True
        fields.update(merge_buff_fields(user, **buff_updates))
        msg = (
            "Astringent wash: **swelling eases 1 sunrise**; insect stings soothed "
            "(advantage on next venom save); bruises fade faster with rest."
        )
        return {
            "kind": "minor_relief",
            "message": msg,
            "fields": fields,
        }

    if herb_key == "jewelweed":
        fields.update(
            merge_buff_fields(
                user,
                pain_relief_until_day=day + 1,
                venom_save_advantage=True,
                calm_until_day=day + 1,
            )
        )
        if disease_key in ("poison_ivy", "mild_poison"):
            fields.update(grant_disease_save_advantage(user))
        msg = "Touch-me-not sap cools the rash and sting; itch eases **1 sunrise**."
        if disease_key == "poison_ivy":
            msg = "Jewelweed sap clears the **poison-ivy** oils; itch eases **1 sunrise**."
        return {
            "kind": "minor_relief",
            "message": msg,
            "fields": fields,
        }

    if herb_key == "shepherds_purse":
        fields.update(merge_buff_fields(user, medicine_bonus_next=2, pain_relief_until_day=day))
        return {
            "kind": "minor_relief",
            "message": "seed-pods staunched the bleed; **+2** on the next stabilize or bleeding treatment.",
            "fields": fields,
        }

    if herb_key == "burdock_root":
        fields.update(
            merge_buff_fields(
                user,
                infection_ward_until_day=day + 1,
            )
        )
        fields.update(grant_disease_save_advantage(user))
        return {
            "kind": "infection_ward",
            "message": "root poultice draws infection; **infection ward 1 sunrise**; advantage on next disease save.",
            "fields": fields,
        }

    if herb_key == "knotgrass":
        fields.update(
            merge_buff_fields(
                user,
                pain_relief_until_day=day,
                flea_ward_until_day=day + 2,
            )
        )
        fields["mood"] = min(100, mood + 2)
        msg = (
            "Astringent leaves settle the gut; flea itch and nausea ease **1 sunrise** "
            "(**flea ward 2 sunrises**)."
        )
        if disease_key == "fleas":
            fields.update(grant_disease_save_advantage(user))
            msg += " Advantage on the next save to shed the mites."
        return {"kind": "minor_relief", "message": msg, "fields": fields}

    if herb_key == "lizards_tail":
        fields.update(grant_disease_save_advantage(user))
        if disease_key:
            ex = max(0, int(user["exhaustion"] if "exhaustion" in user.keys() else 0) - 1)
            fields["exhaustion"] = ex
            return {
                "kind": "minor_relief",
                "message": "fever tonic: **−1 exhaustion**; advantage on the next disease save.",
                "fields": fields,
            }
        return {
            "kind": "disease_save_buff",
            "message": "bitter root: advantage on the next disease save.",
            "fields": fields,
        }

    if herb_key in ("mullein", "lungwort"):
        label = "Mullein" if herb_key == "mullein" else "Lungwort"
        if disease_key in ("yellowcough", "rot_lung", "cancer"):
            fields.update(grant_disease_save_advantage(user))
            fields.update(merge_buff_fields(user, pain_relief_until_day=day + 1))
            return {
                "kind": "disease_save_buff",
                "message": (
                    f"**{label}** lung course: advantage on the next disease save; "
                    "wheeze and chest pain ease **1 sunrise**."
                ),
                "fields": fields,
            }
        if disease_key in ("cough",):
            fields["cough_suppressed"] = 1
            return {
                "kind": "symptom_relief",
                "message": f"**{label}** tea eases coughing until next sunrise.",
                "fields": fields,
            }
        fields.update(merge_buff_fields(user, pain_relief_until_day=day))
        return {
            "kind": "minor_relief",
            "message": f"**{label}** poultice soothes irritated lungs **1 sunrise**.",
            "fields": fields,
        }

    if herb_key == "marsh_mallow":
        fields.update(merge_buff_fields(user, pain_relief_until_day=day + 1))
        if disease_key == "rot_lung":
            fields.update(grant_disease_save_advantage(user))
            fields["mood"] = min(100, mood + 3)
            return {
                "kind": "disease_save_buff",
                "message": "marsh root soothes rot-lung fever; advantage on the next disease save.",
                "fields": fields,
            }
        fields["mood"] = min(100, mood + 2)
        return {
            "kind": "minor_relief",
            "message": "slippery root eases gut and chest irritation **1 sunrise**.",
            "fields": fields,
        }

    if herb_key == "belly_rip_fungus":
        fields.update(
            merge_buff_fields(
                user,
                infection_ward_until_day=day + 1,
            )
        )
        if disease_key == "rot_lung":
            fields.update(grant_disease_save_advantage(user))
            return {
                "kind": "infection_ward",
                "message": (
                    "glow-fungus ward **1 sunrise**; advantage on the next rot-lung save "
                    "(necrosis clears only on matched treat)."
                ),
                "fields": fields,
            }
        return {
            "kind": "infection_ward",
            "message": "glow-fungus poultice: **infection ward 1 sunrise**.",
            "fields": fields,
        }

    if herb_key == "pine_bark":
        if disease_key in ("cough", "yellowcough", "rot_lung"):
            fields["cough_suppressed"] = 1
            fields.update(merge_buff_fields(user, pain_relief_until_day=day))
            return {
                "kind": "symptom_relief",
                "message": "bark tea suppresses cough and eases frost-nipped paws **1 sunrise**.",
                "fields": fields,
            }
        if "punctured_paw" in injury_set:
            fields.update(merge_buff_fields(user, pain_relief_until_day=day + 1))
            return {
                "kind": "minor_relief",
                "message": "inner bark numbs cracked pads **1 sunrise**.",
                "fields": fields,
            }
        fields.update(merge_buff_fields(user, pain_relief_until_day=day))
        return {
            "kind": "minor_relief",
            "message": "bitter bark eases throat and paw soreness **1 sunrise**.",
            "fields": fields,
        }

    if herb_key == "heather":
        fields.update(grant_disease_save_advantage(user))
        fields["mood"] = min(100, mood + 3)
        msg = "Bitter mixture sweetened: tonic stays down; advantage on the next disease save."
        if disease_key in ("mild_poison", "diarrhea", "influenza"):
            msg = (
                "Heather honeying steadies a queasy gut; advantage on the next disease save."
            )
        return {"kind": "minor_relief", "message": msg, "fields": fields}

    if outcome in ("cured_disease", "cured_injury", "cured_genetic", "healed", "stabilized", "rabies_ease"):
        return None

    return None


def format_active_herb_buffs(user, day: int) -> str:
    """player-facing summary of timed herb effects."""
    lines: list[str] = []
    if pain_relief_active(user, day):
        lines.append("**pain relief**; wounds and strain hurt less this sunrise.")
    if sedated_blocks_activity(user, day):
        lines.append("**sedated**; drowsy from herbs — strenuous activity blocked.")
    if infection_ward_active(user, day):
        lines.append("**infection ward**; treated wounds resist festering.")
    if flea_ward_active(user, day):
        lines.append("**flea ward**; insect-repellent oils on the pelt.")
    if burial_scent_masked(user, day):
        lines.append("**burial scent masked**; carrion and filth exposure reduced.")
    pen = frostbite_dex_penalty(user, day)
    if pen:
        lines.append("**frostbitten paws**; dexterity penalty until herbs wear off.")
    if disease_save_uses_advantage(user):
        days = int(user["disease_save_buff_days"]) if "disease_save_buff_days" in user.keys() else 0
        if days > 0:
            lines.append(f"**disease save advantage**; illness saves roll twice ({days}d left).")
        else:
            lines.append("**disease save advantage**; next illness save rolls twice.")
    buffs = get_buffs(user)
    if buffs.get("cough_suppressed_until_day") and int(buffs["cough_suppressed_until_day"]) >= day:
        lines.append("**cough suppressed**; breathing eased by herbs.")
    if buffs.get("medicine_bonus_next"):
        lines.append(f"**medicine boost**; next treat gets +{buffs['medicine_bonus_next']} to the roll.")
    return "\n".join(lines)


def sedated_blocks_activity(user, day: int) -> bool:
    buffs = get_buffs(user)
    until = buffs.get("sedated_until_day")
    return bool(until and int(until) >= day)
