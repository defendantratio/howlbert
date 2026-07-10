# herb_properties.py
"""fresh vs prepared herb rules; toxicity, required prep, potency."""

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
    requires_tea: bool = False
    fresh_only_bonus: bool = False
    dried_only: bool = False
    notes: str = ""


# per-herb overrides; inventory herbs are always dried by default
HERB_FORM_RULES: dict[str, HerbFormRule] = {
    "skunk_cabbage": HerbFormRule(
        toxic_if_fresh=True,
        toxic_dc=12,
        must_dry_before_use=True,
        notes="fresh leaves burn the mouth; dry before cough use.",
    ),
    "elder": HerbFormRule(
        toxic_if_fresh=True,
        toxic_dc=14,
        toxic_damage=(2, 4),
        external_only=True,
        requires_poultice=True,
        notes="elder bark/leaves are poultice-only; never swallow.",
    ),
    "stinging_nettle": HerbFormRule(
        requires_poultice=True,
        notes="raw nettles sting; chew into poultice or dry first.",
    ),
    "foxglove": HerbFormRule(toxic_if_fresh=True, toxic_dc=18, notes="heart poison; medic knowledge only."),
    "deadly_nightshade": HerbFormRule(toxic_if_fresh=True, toxic_dc=15, notes="confusion poison."),
    "holly_berries": HerbFormRule(toxic_if_fresh=True, toxic_dc=12, toxic_damage=(2, 4)),
    "bloodroot": HerbFormRule(toxic_if_fresh=True, toxic_dc=16, toxic_damage=(3, 6)),
    "oleander": HerbFormRule(toxic_if_fresh=True, toxic_dc=18, toxic_damage=(4, 6)),
    "water_hemlock": HerbFormRule(toxic_if_fresh=True, toxic_dc=20, toxic_damage=(6, 6)),
    "deathberries": HerbFormRule(toxic_if_fresh=True, toxic_dc=18, notes="mercy-killing herb only."),
    "feverfew": HerbFormRule(requires_tea=True, fresh_only_bonus=True, notes="tea works best fresh."),
    "yarrow": HerbFormRule(fresh_only_bonus=True, notes="fresh yarrow staunches faster (+2 stabilize)."),
    "comfrey": HerbFormRule(
        requires_poultice=True,
        notes="promotes bone knitting and tissue repair; for bruises, sprains, and closed injuries. never apply to open wounds (toxins absorb through broken skin) or ingest.",
    ),
    "goldenrod": HerbFormRule(requires_poultice=True),
    "dried_skullcap": HerbFormRule(dried_only=True),
    "meadowsweet": HerbFormRule(requires_tea=True),
    "labrador_tea": HerbFormRule(requires_tea=True),
    "arnica": HerbFormRule(external_only=True, requires_poultice=True),
    "death_cap": HerbFormRule(
        toxic_if_fresh=True,
        toxic_dc=18,
        toxic_damage=(3, 6),
        notes="intensely toxic; organ failure and seizures.",
    ),
    "wintergreen": HerbFormRule(
        toxic_if_fresh=True,
        toxic_dc=10,
        toxic_damage=(1, 4),
        external_only=True,
        notes="oil unsafe to eat; external use only.",
    ),
    "wolfsbane": HerbFormRule(
        toxic_if_fresh=True,
        toxic_dc=20,
        toxic_damage=(2, 6),
        notes="extremely toxic; all parts poisonous; absorbed through skin.",
    ),
    # add new rules if needed
}


def herb_form_rule(herb_key: str) -> HerbFormRule:
    if herb_key in HERB_FORM_RULES:
        return HERB_FORM_RULES[herb_key]
    meta = HERBS.get(herb_key, {})
    if meta.get("poison"):
        return HerbFormRule(
            toxic_if_fresh=True,
            toxic_dc=14,
            notes="restricted poison plant.",
        )
    return HerbFormRule()


def form_label(form: str) -> str:
    return {
        "fresh": "fresh",
        "dried": "dried",
        "poultice": "poultice",
        "juice": "juice",
        "tea": "tea",
        "ointment": "ointment",
        "sap": "sap",
        "rub": "rub",
        "cooked": "eaten cooked",
        "raw": "eaten raw",
        "gargle": "gargle",
        "sweetened": "sweetened",
        "simmered_milk": "simmered milk",
    }.get(form, form)


def can_use_form(rule: HerbFormRule, form: str, *, complex_wound: bool) -> tuple[bool, str]:
    if rule.must_dry_before_use and form == "fresh":
        return False, "must **dry** this herb before use."
    if rule.dried_only and form != "dried":
        return False, "only the **dried** form is safe to use."
    if rule.external_only and form != "poultice":
        if form == "fresh":
            return False, "external poultice only; do not swallow fresh."
    if rule.requires_tea and form not in ("tea", "dried"):
        return False, "needs a **tea** (steeped)."
    if rule.requires_poultice and form == "fresh" and complex_wound:
        return False, "complex wound needs a proper **poultice** (dc 10) or heals less."
    return True, ""