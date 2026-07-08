"""Paginated herb compendium for /herbs action:guide."""

from __future__ import annotations

from herbs import DISEASE_STAGES, HERBS, INJURIES

HABITAT_LABELS = {
    "wild": "territory",
    "roadside": "thunderpath verge",
    "compound": "twoleg edge",
}

HERBS_PER_PAGE = 5

FILTER_LABELS = {
    "all": "all herbs",
    "wild": "territory (wild)",
    "roadside": "thunderpath verge",
    "compound": "twoleg compound edge",
}

OVERVIEW_BODY = (
    "**gathering**\n"
    "· `/field action:forage`; pack territory (wild habitat)\n"
    "· `/field action:verge verge_site:roadside`; thunderpath shoulder weeds\n"
    "· `/field action:verge verge_site:compound`; Twoleg fence-lines & gardens\n"
    "· **Foragers**; unlimited territory + verge forage each sunrise\n\n"
    "**Using herbs**\n"
    "· `/medic action:treat herb:herb_yarrow`; keys from `/bones action:inventory`\n"
    "· Matching **injury** or **disease** → auto-cures on success\n"
    "· No match → often needs **Medicine DC 15** (Medics / Herblore help)\n"
    "· `/vitals action:rest rest_type:short use_herb:true`; comfrey heal (3/day, Medics unlimited)\n"
    "· **Medics**; unlimited `/medic action:treat` per sunrise\n\n"
    "_Flip pages below. Filter by where plants grow or browse everything._"
)


# keyword in an herb's `preparation` text -> the prep method it implies.
_PREP_TEXT_METHODS: tuple[tuple[str, str], ...] = (
    ("poultice", "poultice"),
    ("juice", "juice"),
    ("gargle", "gargle"),
    ("ointment", "ointment"),
    ("salve", "ointment"),
    ("sap", "sap"),
    ("rub", "rub"),
    ("simmered in milk", "simmered milk"),
    ("in milk", "simmered milk"),
    ("cooked", "eaten cooked"),
    ("tea", "tea"),
    ("infusion", "tea"),
    ("decoction", "tea"),
    ("gruel", "eaten cooked"),
    ("eaten raw", "eaten raw"),
    ("raw", "eaten raw"),
    ("chewed", "poultice"),
    ("dried", "dried"),
)


def _derive_prep_methods(herb_key: str, meta: dict) -> list[str]:
    """Preparation methods that make sense for an herb, read from its own
    `preparation` text (dry first, then tea/rub/juice/poultice/etc, and a tea or
    gargle can be sweetened). Explicit prep_methods still win when present."""
    explicit = meta.get("prep_methods") or ()
    if explicit:
        return list(explicit)
    from engine.herb_properties import herb_form_rule

    text = (meta.get("preparation") or "").lower()
    methods: list[str] = []
    for needle, method in _PREP_TEXT_METHODS:
        if needle in text and method not in methods:
            methods.append(method)
    # fold in the herb's form rule so a poultice/tea herb still lists the right
    # method even when its preparation text uses a different word.
    rule = herb_form_rule(herb_key)
    if rule.dried_only:
        return ["dried"]
    if (rule.requires_poultice or rule.external_only) and "poultice" not in methods:
        methods.append("poultice")
    if rule.requires_tea and "tea" not in methods:
        methods.append("tea")
    # every gathered herb can at least be dried for storage.
    if "dried" not in methods:
        methods.insert(0, "dried")
    if len(methods) == 1:  # only "dried" derived; default to a usable form
        methods.append("eaten raw")
    return methods


def _cure_labels(cures: tuple) -> str:
    if not cures:
        return ""
    from engine.genetics import GENETIC_CONDITIONS, HERB_CURABLE_GENETICS

    labels: list[str] = []
    for key in cures[:10]:
        if key in INJURIES:
            labels.append(INJURIES[key]["name"])
        elif key in GENETIC_CONDITIONS:
            if key in HERB_CURABLE_GENETICS:
                labels.append(GENETIC_CONDITIONS[key]["name"])
        elif key in DISEASE_STAGES:
            labels.append(DISEASE_STAGES[key]["name"])
        else:
            labels.append(key.replace("_", " ").title())
    suffix = "…" if len(cures) > 10 else ""
    return f"\n**treats:** {', '.join(labels)}{suffix}" if labels else ""


def _usage_hint(herb_key: str, meta: dict) -> str:
    from engine.herb_mechanics import build_usage_hint

    return build_usage_hint(herb_key, meta)


def format_herb_block(herb_key: str, meta: dict) -> str:
    habitats = ", ".join(HABITAT_LABELS.get(h, h) for h in meta.get("habitat", ("wild",)))
    block = (
        f"**{meta['name']}** · `{herb_key}` · _{meta['rarity']}_\n"
        f"_{habitats}_\n"
        f"{meta['effect']}"
        f"{_cure_labels(meta.get('cures', ()))}\n"
        f"{_usage_hint(herb_key, meta)}"
    )
    return block


def list_herb_keys(filter_key: str = "all") -> list[str]:
    keys = sorted(HERBS.keys(), key=lambda k: HERBS[k]["name"].lower())
    if filter_key == "all":
        return keys
    return [k for k in keys if filter_key in HERBS[k].get("habitat", ("wild",))]


def total_pages(filter_key: str = "all") -> int:
    count = len(list_herb_keys(filter_key))
    if count == 0:
        return 1
    return max(1, (count + HERBS_PER_PAGE - 1) // HERBS_PER_PAGE)


def build_herb_guide_embed(*, page: int = 0, filter_key: str = "all") -> tuple[str, str]:
    """Return (title, body) for one guide page."""
    if page == 0:
        title = "herb guide; overview"
        return title, OVERVIEW_BODY

    keys = list_herb_keys(filter_key)
    content_page = page - 1
    start = content_page * HERBS_PER_PAGE
    chunk = keys[start : start + HERBS_PER_PAGE]
    if not chunk:
        return "herb guide", "_no herbs in this filter._"

    filter_label = FILTER_LABELS.get(filter_key, filter_key)
    title = f"herb guide: {filter_label}"
    blocks = [format_herb_block(k, HERBS[k]) for k in chunk]
    body = "\n\n".join(blocks)
    footer_note = f"page **{page + 1}** of **{total_pages(filter_key) + 1}** · `/medic action:treat herb:herb_<key>`"
    return title, f"{body}\n\n_{footer_note}_"
