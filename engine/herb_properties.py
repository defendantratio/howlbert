"""Fresh vs prepared herb rules; toxicity, required prep, potency."""

from __future__ import annotations

from dataclasses import dataclass

from herbs import HERBS


@dataclass(frozen=True)
class HerbFormRule:
    toxic_if_fresh: bool = False
    toxic_dc: int = 12
    toxic_damage: tuple[int, int] = (1, 4)
    must_dry_before_use: bool = False
    external_only: bool = False
    requires_poultice: bool = False
    requires_tonic: bool = False
    requires_decoction: bool = False
    fresh_only_bonus: bool = False
    dried_only: bool = False
    notes: str = ""


# Per-herb overrides; shop-stable inventory herbs skip stacks and use safe dried logic.
HERB_FORM_RULES: dict[str, HerbFormRule] = {
    "skunk_cabbage": HerbFormRule(
        toxic_if_fresh=True,
        toxic_dc=12,
        must_dry_before_use=True,
        notes="Fresh leaves burn the mouth; dry before cough use.",
    ),
    "elder": HerbFormRule(
        toxic_if_fresh=True,
        toxic_dc=14,
        toxic_damage=(2, 4),
        external_only=True,
        requires_poultice=True,
        notes="Elder bark/leaves are poultice-only; never swallow.",
    ),
    "stinging_nettle": HerbFormRule(
        requires_poultice=True,
        notes="Raw nettles sting; chew into poultice or dry first.",
    ),
    "foxglove": HerbFormRule(toxic_if_fresh=True, toxic_dc=18, notes="Heart poison; Medic knowledge only."),
    "deadly_nightshade": HerbFormRule(toxic_if_fresh=True, toxic_dc=15, notes="Confusion poison."),
    "holly_berries": HerbFormRule(toxic_if_fresh=True, toxic_dc=12, toxic_damage=(2, 4)),
    "bloodroot": HerbFormRule(toxic_if_fresh=True, toxic_dc=16, toxic_damage=(3, 6)),
    "oleander": HerbFormRule(toxic_if_fresh=True, toxic_dc=18, toxic_damage=(4, 6)),
    "water_hemlock": HerbFormRule(toxic_if_fresh=True, toxic_dc=20, toxic_damage=(6, 6)),
    "deathberries": HerbFormRule(toxic_if_fresh=True, toxic_dc=18, notes="Mercy-killing herb only."),
    "feverfew": HerbFormRule(requires_tonic=True, fresh_only_bonus=True, notes="Tonic tea works best fresh."),
    "yarrow": HerbFormRule(fresh_only_bonus=True, notes="Fresh yarrow staunches faster (+2 stabilize)."),
    "comfrey": HerbFormRule(
        requires_poultice=True,
        notes="Complex fractures need poultice (1d4); raw chew heals 1d2.",
    ),
    "goldenrod": HerbFormRule(requires_poultice=True),
    "dried_skullcap": HerbFormRule(dried_only=True),
    "meadowsweet": HerbFormRule(requires_tonic=True),
    "labrador_tea": HerbFormRule(requires_decoction=True),
    "arnica": HerbFormRule(external_only=True, requires_poultice=True),
}


def herb_form_rule(herb_key: str) -> HerbFormRule:
    if herb_key in HERB_FORM_RULES:
        return HERB_FORM_RULES[herb_key]
    meta = HERBS.get(herb_key, {})
    if meta.get("poison"):
        return HerbFormRule(
            toxic_if_fresh=True,
            toxic_dc=14,
            notes="Restricted poison plant.",
        )
    return HerbFormRule()


def form_label(form: str) -> str:
    return {
        "fresh": "fresh",
        "dried": "dried",
        "poultice": "poultice",
        "tonic": "tonic",
        "decoction": "decoction",
    }.get(form, form)


def can_use_form(rule: HerbFormRule, form: str, *, complex_wound: bool) -> tuple[bool, str]:
    if rule.must_dry_before_use and form == "fresh":
        return False, "Must **dry** this herb before use."
    if rule.dried_only and form != "dried":
        return False, "Only the **dried** form is safe to use."
    if rule.external_only and form in ("tonic", "fresh") and form != "poultice":
        if form == "fresh":
            return False, "External poultice only; do not swallow fresh."
    if rule.requires_decoction and form not in ("decoction", "dried"):
        return False, "Needs a **decoction** (boiled or hot-spring steeped)."
    if rule.requires_tonic and form not in ("tonic", "decoction", "fresh") and not complex_wound:
        if form == "dried":
            return True, ""
    if rule.requires_poultice and form == "fresh" and complex_wound:
        return False, "Complex wound needs a proper **poultice** (DC 10) or heals less."
    return True, ""
