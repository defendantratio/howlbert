"""Herb-based supportive care for chronic diseases.

The normal cure path already clears diseases whose stage a herb can cure. This
module adds the two things chronic sickness needs that a cure does not cover:
  * **support** — comfort care that eases a chronic-diseased wolf's exhaustion
    and pain even when the disease itself can't be cured;
  * **halt** — the right herb holds a chronic disease's progression at bay for a
    few sunrises, so it stops worsening (useful for the no-cure ones like river
    rot, or the slow killers like cancer and wasting sickness).
"""

from __future__ import annotations

from engine.diseases import is_chronic_disease, parse_disease
from engine.herb_buffs import get_buffs, merge_buff_fields

# herbs that can ease / hold a chronic disease (herb_key -> chronic disease keys).
CHRONIC_CARE_HERBS: dict[str, tuple[str, ...]] = {
    "borage": ("wasting_sickness",),
    "parsley": ("wasting_sickness",),
    "mullein": ("cancer", "wasting_sickness"),
    "lungwort": ("cancer", "wasting_sickness"),
    "feverfew": ("cancer",),
    "goldenrod": ("cancer", "rabies"),
    "boneset": ("rabies",),
    "oak_bark": ("river_rot",),
    "bindweed": ("river_rot",),
    "watermint": ("river_rot",),
    "dried_skullcap": ("dementia", "feral_shift"),
    "rosemary": ("dementia",),
    "chamomile": ("dementia",),
    "passionflower": ("feral_shift",),
    "valerian": ("feral_shift",),
}

CHRONIC_HALT_DAYS = 3


def _wolf_chronic(user) -> tuple[str | None, str | None]:
    raw = user["disease"] if user and "disease" in user.keys() else None
    key, stage = parse_disease(raw)
    if key and is_chronic_disease(key):
        return key, stage
    return None, None


def herb_helps_chronic(user, herb_key: str) -> str | None:
    """The chronic disease this herb can ease/hold for the wolf, or None."""
    key, _ = _wolf_chronic(user)
    if not key:
        return None
    return key if key in CHRONIC_CARE_HERBS.get(herb_key, ()) else None


def apply_chronic_herb_support(user, herb_key: str) -> tuple[dict, str | None]:
    """Comfort care for a chronic-diseased wolf: eases exhaustion and pain by 1
    each. Returns (db fields, note) — empty when not applicable."""
    disease_key = herb_helps_chronic(user, herb_key)
    if not disease_key:
        return {}, None
    fields: dict = {}
    ex = int(user["exhaustion"]) if "exhaustion" in user.keys() and user["exhaustion"] is not None else 0
    pe = int(user["pain_exhaustion"]) if "pain_exhaustion" in user.keys() and user["pain_exhaustion"] is not None else 0
    if ex > 0:
        fields["exhaustion"] = max(0, ex - 1)
    if pe > 0:
        fields["pain_exhaustion"] = max(0, pe - 1)
    if not fields:
        return {}, None
    return fields, "supportive care eases the worst of it (−1 exhaustion, −1 pain)."


def grant_chronic_halt(user, herb_key: str, *, day: int, duration: int = CHRONIC_HALT_DAYS) -> tuple[dict, str | None]:
    """If the herb can hold the wolf's chronic disease, stall its progression for
    ``duration`` sunrises. Returns (db fields, note)."""
    disease_key = herb_helps_chronic(user, herb_key)
    if not disease_key or not day:
        return {}, None
    fields = merge_buff_fields(
        user,
        chronic_halt_until_day=day + duration,
        chronic_halt_disease=disease_key,
    )
    return fields, f"the sickness is held at bay for **{duration}** sunrises; it will not worsen."


def chronic_halt_active(user, disease_key: str, day: int) -> bool:
    """True if this wolf's chronic disease is currently herb-held from worsening."""
    if not day:
        return False
    buffs = get_buffs(user)
    until = buffs.get("chronic_halt_until_day")
    held = buffs.get("chronic_halt_disease")
    return bool(until and int(until) >= int(day) and held == disease_key)
