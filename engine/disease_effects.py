"""Mechanical effects of active disease stages on checks and movement."""

from __future__ import annotations

from engine.diseases import DISEASES, get_stage_info, parse_disease

PHYSICAL_ATTRS = frozenset({"attr_str", "attr_dex", "attr_con"})


def _parsed(user) -> tuple[str | None, str | None]:
    raw = user["disease"] if user and "disease" in user.keys() else None
    return parse_disease(raw)


def active_disease(user) -> str | None:
    """legacy helper; returns cough stage or disease key."""
    key, stage = _parsed(user)
    if key == "cough":
        return stage
    return key


def disease_check_adjustments(user, attr_keys: tuple[str, ...]) -> tuple[int, bool]:
    key, stage = _parsed(user)
    if not key:
        return 0, False
    attrs = set(attr_keys)

    if key == "pupcough":
        if stage == "active":
            from engine.herb_buffs import get_buffs

            used_day = get_buffs(user).get("pupcough_dex_used_day")
            day = int(user["last_rest_day"]) if user and "last_rest_day" in user.keys() else 0
            if "attr_dex" in attrs and used_day != day:
                return 0, True
        if stage == "weak_lungs" and "attr_con" in attrs:
            return -1, False
        return 0, False
    if key == "cough":
        suppressed = int(user["cough_suppressed"]) if user and "cough_suppressed" in user.keys() else 0
        if stage == "mild":
            return 0, (not suppressed) and ("attr_dex" in attrs)
        if stage == "severe":
            return 0, bool(attrs & {"attr_dex", "attr_str"})
        if stage == "deadly":
            return 0, bool(attrs & PHYSICAL_ATTRS)
    if key == "yellowcough":
        mental = bool(attrs & {"attr_int", "attr_wis"})
        weak_or_wheeze = bool(attrs & {"attr_str", "attr_dex"})
        return 0, mental or weak_or_wheeze
    if key == "rot_lung":
        return 0, bool(attrs & PHYSICAL_ATTRS)
    if key == "shaking_sickness":
        if stage == "shaking":
            return 0, "attr_dex" in attrs
        return 0, bool(attrs & PHYSICAL_ATTRS)
    if key == "milk_fever":
        return 0, bool(attrs & {"attr_dex", "attr_con"})
    if key in ("influenza", "distemper", "pox"):
        return 0, bool(attrs & PHYSICAL_ATTRS)
    if key == "hepatitis":
        return 0, "attr_con" in attrs
    if key == "mange":
        return 0, "attr_dex" in attrs
    if key == "mild_poison":
        return 0, bool(attrs & {"attr_dex", "attr_con"})
    if key == "poison_ivy":
        return 0, "attr_dex" in attrs
    if key == "rabies":
        from engine.mental_effects import mental_check_adjustments

        return mental_check_adjustments(user, attr_keys)
    if key in ("wasting_sickness", "cancer"):
        return 0, bool(attrs & PHYSICAL_ATTRS)
    if key in ("dementia", "feral_shift") or (
        key
        and key
        in (
            "insomnia",
            "anxiety",
            "grief_melancholy",
            "delirium",
            "pack_madness",
            "obsession",
            "night_terrors",
            "chronic_stress",
            "eating_distress",
            "shock_emotional",
        )
    ):
        from engine.mental_effects import mental_check_adjustments

        return mental_check_adjustments(user, attr_keys)
    return 0, False


def disease_hunt_multiplier(user) -> tuple[float, str]:
    key, stage = _parsed(user)
    if key == "cough" and stage == "severe":
        return 0.75, "blackcough; speed −25% hunt bones."
    if key in ("mange", "distemper", "yellowcough"):
        info = get_stage_info(key, stage or "active")
        mult = float(info.get("hunt_mult", 0.75)) if info else 0.75
        pct = int((1 - mult) * 100)
        label = {"mange": "Mange", "distemper": "Distemper", "yellowcough": "Yellowcough"}.get(
            key, key.title()
        )
        if key == "yellowcough":
            return mult, f"{label}; wheezing and weakness; −{pct}% hunt bones."
        return mult, f"{label}; speed −{pct}% hunt bones."
    if key == "rot_lung" and stage in ("wheeze", "necrosis"):
        info = get_stage_info(key, stage)
        mult = float(info.get("hunt_mult", 0.75)) if info else 0.75
        pct = int((1 - mult) * 100)
        return mult, f"rot-lung; −{pct}% hunt bones."
    if key in ("wasting_sickness", "cancer", "feral_shift", "insomnia", "chronic_stress", "obsession"):
        info = get_stage_info(key, stage or "active")
        mult = float(info.get("hunt_mult", 1.0)) if info else 1.0
        if mult < 1.0:
            pct = int((1 - mult) * 100)
            label = DISEASES.get(key, {}).get("label", key.replace("_", " ").title())
            return mult, f"{label}; −{pct}% hunt bones."
    return 1.0, ""


def disease_attack_disadvantage(user, attack_type: str) -> bool:
    key, stage = _parsed(user)
    if not key:
        return False
    if key == "cough":
        if stage == "deadly":
            return True
        if stage == "severe":
            return attack_type in ("bite", "kick", "gore", "claw", "charge")
        if stage == "mild":
            return attack_type == "bite"
    if key in ("influenza", "distemper", "pox", "yellowcough", "rot_lung", "shaking_sickness", "rabies"):
        return True
    return False


def consume_disease_check_flags(user, day: int) -> dict:
    """mark one-shot disease check flags after a roll."""
    from engine.herb_buffs import get_buffs, merge_buff_fields

    key, stage = _parsed(user)
    if key == "pupcough" and stage == "active":
        if get_buffs(user).get("pupcough_dex_used_day") != day:
            return merge_buff_fields(user, pupcough_dex_used_day=day)
    return {}
