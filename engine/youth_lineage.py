"""Pup and juvenile birth names and adoption eligibility."""

from __future__ import annotations

import random

from config import JUVENILE_MAX_MOONS
from engine.aging import stage_for_age, stage_label
from utils.names import validate_display_name


def is_youth_age(age_months: int) -> bool:
    return int(age_months) < JUVENILE_MAX_MOONS


def parse_litter_names(raw: str, litter_size: int) -> tuple[list[str] | None, str | None]:
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if len(parts) < litter_size:
        return None, (
            f"provide **{litter_size}** name(s), comma-separated "
            f"(litter size is **{litter_size}**)."
        )
    names: list[str] = []
    seen: set[str] = set()
    for index, part in enumerate(parts[:litter_size]):
        cleaned, err = validate_display_name(part, label=f"name {index + 1}")
        if err:
            return None, err
        key = cleaned.lower()
        if key in seen:
            return None, f"duplicate name **{cleaned}** in the list."
        seen.add(key)
        names.append(cleaned)
    return names, None


def adoption_eligibility_error(youth, adopter, partner) -> str | None:
    if youth["id"] in (adopter["id"], partner["id"]):
        return "you cannot adopt one of yourselves."
    if youth["condition"] == "dead":
        return "a dead wolf cannot be adopted."
    if not is_youth_age(youth["age_months"]):
        stage = stage_label(stage_for_age(youth["age_months"]))
        return (
            f"**{youth['wolf_name']}** is a **{stage}**; only pups and juveniles "
            f"(under **{JUVENILE_MAX_MOONS}** moons) can be adopted."
        )
    if "adopt_parent_1_id" in youth.keys() and youth["adopt_parent_1_id"]:
        return f"**{youth['wolf_name']}** already has adoptive parents."
    return None


def random_birth_sex() -> str:
    return random.choice(("female", "male"))
