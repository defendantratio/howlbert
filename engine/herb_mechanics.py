"""Mechanical descriptions for the herb compendium (/herbs action:guide)."""

from __future__ import annotations

from herbs import DISEASE_STAGES, HERBS, INJURIES

SPECIAL_MECHANICS: dict[str, str] = {
    "reduce_exhaustion": "Removes **1 exhaustion** when hunger/hydration are low; pup feed path via honey.",
    "march_shield": "Blocks the first **+1 exhaustion** from forced march this sunrise.",
    "hunger_shield": "Skip hunger-based exhaustion on the next sunrise.",
    "sorrel_restore": "Restores **+10 hunger** and eases bleeding exhaustion.",
    "jaw_meal_shield": "Broken jaw: eat and drink without pain until next sunrise.",
    "purslane_thirst": "Chew for **+12 hydration** without visiting the creek.",
    "ragweed_need_three": "Needs **3** in inventory to remove **1 exhaustion**.",
    "feed_pup_honey": "Starving pup: **+10 hunger** via nursing/honey feed.",
    "honey_needs_depletion": "Adult honey: **−1 exhaustion** when hunger/hydration are below **30**.",
    "honey_pup_not_depleted": "Honey helps pups only when hunger/hydration are low.",
}

STATIC_HINTS: dict[str, str] = {
    "comfrey": "Poultice heals **1d4 HP** on treat; splint injuries listed under **Treats**.",
    "cobwebs": "Auto-stabilizes **dying** wolves at **1 HP**; bandages deep gashes.",
    "bindweed": "Splint herb for **fractured rib**, **sprain**, **spinal injury**; with comfrey **−7 days** bone healing.",
    "stick": "Surgery supply: patient bites during stitch/set bone/amputate; **2 sticks** for set bone.",
    "deathberries": "Mercy dose (**Medic** only): ends suffering on a **dying** wolf.",
    "bloodroot": "Restricted poison: **3d6** damage (CON DC **16** half); non-Medic misuse **−4 standing**.",
    "oleander": "Restricted poison: **4d6** damage (CON DC **18** half); non-Medic misuse **−4 standing**.",
    "water_hemlock": "Restricted poison: violent seizures; often fatal (CON save); non-Medic **−4 standing**.",
    "foxglove": "Restricted poison: cardiac failure (CON DC **18**); non-Medic misuse **−4 standing**.",
    "deadly_nightshade": "Restricted poison: confusion then paralysis (WIS DC **15**); non-Medic **−4 standing**.",
    "holly_berries": "Restricted poison: **2d4** damage (CON DC **12** half); non-Medic **−4 standing**.",
    "poison_ivy": "Restricted contact toxin: CHA penalty; hoarding without Medic turn-in **−3 standing if caught**.",
    "wintergreen": "Avoid: resembles holly; toxic if eaten; non-Medic misuse **−4 standing**.",
    "wolfsbane": "Clears **long-term injuries**; **2 to 6 poison HP**; non-Medic misuse **−4 standing**.",
    "swamp_milkweed": "Clears **long-term injuries** without poison cost; soothes rheumatic pain.",
    "yarrow": "Treats **deep gash** / **infected wound**; **+2 stabilize** from herb stack; stops **shaking sickness** hemorrhage.",
    "oak_bark": "Treats bleeding wounds; **+2 stabilize** from herb stack.",
    "cattail": "Stops bleeding like yarrow; **+2 stabilize** from herb stack.",
    "horsetail": "Treats **torn claw** / **punctured paw**; **+3** on stabilize/death saves.",
    "saffron": "Stabilizes **dying** mothers at **1 HP** (birth hemorrhage); prevents heavy bleeding around birth.",
    "arnica": "On **sprain** / **punctured paw** treat: clears injury and **halves** recovery time (external only).",
    "tansy": "On **sprain** treat: clears injury and **halves** recovery time.",
    "stinging_nettle": "On bone-injury treat: **−1 day** off splint healing (with comfrey binding).",
    "alder_bark": "Numbs **toothache** and gum pain **1 sunrise**; treats **broken tooth** symptom ease.",
    "dock": "Treats **punctured paw**; soothes pad pain **1 sunrise**.",
    "daisy": "Treats joint sprains; ignores arthritis pain penalties **1 sunrise**.",
    "dried_skullcap": "Sedating rest **1 sunrise**; **2 doses** clear **delirium (Wandering)**; eases **anxiety**, **obsession**.",
    "meadowsweet": "Ignore **1 pain exhaustion**; eases **chronic stress** and **eating distress**.",
    "chamomile": "Calm **1 sunrise**; clears early **anxiety**, **insomnia**, **grief**, **shock (emotional)**.",
    "valerian": "Strong sedative **1 sunrise**; **2 doses/24h** for **insomnia (Sleepless)**.",
    "poppy_seeds": "Strong sedative **1 sunrise**; eases pain and panic; clears **insomnia** and severe anxiety.",
    "willow_bark": "Pain relief **1 sunrise**; cools marsh fever; treats **rot-lung** symptom ease.",
    "lavender": "Calm sleep **1 sunrise**; **2 doses/24h** for **insomnia (Sleepless)**; eases **night terrors**.",
    "passionflower": "Eases **anxiety**, **insomnia**, **night terrors**; advantage on next mental illness save.",
    "rosemary": "Masks death-scent; advantage on next save for **dementia**, **grief**, **obsession**.",
    "douglas_sagewort": "Infection ward **1 sunrise**; eases **chronic stress**, **anxiety**, **pack madness**.",
    "borage": "Courage **1 sunrise** for **anxiety** and **grief**; extra pup milk when nursing.",
    "purple_loosestrife": "Stanches **deep gash** bleeding; optional **+1** on stitch surgery.",
    "plantain": "Treats minor wounds; optional **+1** on extract surgery; **+1 HP** poultice if no match.",
    "witch_hazel": (
        "Astringent wash **1 sunrise**: eases **swelling**, **insect stings** (advantage on next venom save), "
        "and **bruises/sprains** (recovery halved on treat); treats eye strain."
    ),
    "shepherds_purse": "Staunches oozing cuts; **+2** on the next stabilize or bleeding treatment check.",
    "burdock_root": "Skin poultice: **infection ward 1 sunrise**; advantage on the next disease save.",
    "mugwort": "Rub through pelt: **flea ward 3 sunrises**, +2 mood; clears **fleas/mange** on treat.",
    "garlic_mustard": "Roadside rub: **flea ward 3 sunrises**; wild-garlic kin, advantage on next disease save when treating infection.",
    "knotgrass": "Astringent gut herb; **flea ward 2 sunrises**; eases flea itch and nausea **1 sunrise**.",
    "prickly_ash": "Warming bark clears **frostbite**; numbs tooth pain **1 sunrise**.",
    "heather": "Sweetens bitter teas; advantage on next disease save when ill.",
    "lizards_tail": "Fever tea: **−1 exhaustion** when ill; advantage on the next disease save.",
    "mullein": "Lung tea: advantage on next disease save for **yellowcough**, **rot-lung**, or **growth-sickness**.",
    "lungwort": "Lung ally: same lung-course support as mullein when scarce.",
    "marsh_mallow": "Soothes **rot-lung** fever and wheeze; pain relief **1 sunrise**.",
    "belly_rip_fungus": "Glow-fungus: **infection ward 1 sunrise**; essential for **rot-lung necrosis** on treat.",
    "pine_bark": "Inner bark tea suppresses cough until next sunrise; numbs frost-nipped paws.",
    "celandine": "Milky sap eases **eye strain** and surface wounds **1 sunrise**; clears partial blindness on treat.",
    "jewelweed": (
        "Crushed stem sap clears **poison-ivy rash** on treat; soothes **insect stings** and nettle burn **1 sunrise**."
    ),
    "catmint": "**2 doses/24h** clear **Blackcough (Severe)**; eases **anxiety (Uneasy)**.",
    "pine_needle": "**2 doses** before next sunrise to clear **Blackcough (Severe)**.",
    "chickweed": "**3 doses** to clear **Green-cough (Mild)**.",
    "coltsfoot": "**1 dose** to clear **Green-cough (Mild)**.",
    "wild_cherry_bark": "Suppresses cough until next sunrise; does **not** alone clear blackcough stage.",
    "labrador_tea": "Suppresses cough / wheeze until next sunrise.",
    "elder": "External poultice for **sprains** only; **toxic if eaten** (CON DC **14** or **2d4** poison).",
    "skunk_cabbage": "Expert-only respiratory aid; toxic if fresh (Survival DC on treat).",
    "sweet_sedge": "Sap eases internal gut infections on successful treat.",
}


def _probe_user(**overrides) -> dict:
    base = {
        "disease": "",
        "exhaustion": 0,
        "mood": 50,
        "hp": 10,
        "max_hp": 10,
        "herb_buffs": "{}",
        "last_rest_day": 5,
        "active_injuries": "[]",
        "condition": "healthy",
        "genetic_conditions": "[]",
        "skill_proficiencies": "[]",
        "attr_wis": 3,
        "hunger": 50,
        "thirst": 50,
        "age_months": 24,
    }
    base.update(overrides)
    return base


def _probe_supplemental_message(herb_key: str, *, day: int = 5) -> str | None:
    from engine.herb_treatment import apply_flavor_herb

    probes = (
        _probe_user(),
        _probe_user(active_injuries='["sprained_leg"]'),
        _probe_user(active_injuries='["punctured_paw"]'),
        _probe_user(active_injuries='["fractured_rib"]'),
        _probe_user(active_injuries='["infected_wound"]'),
        _probe_user(active_injuries='["deep_gash"]'),
        _probe_user(condition="dying", hp=0),
        _probe_user(disease="severe"),
        _probe_user(disease="mild"),
        _probe_user(disease="anxiety:uneasy"),
        _probe_user(disease="insomnia:sleepless"),
        _probe_user(disease="grief_melancholy:mourning"),
        _probe_user(disease="rabies:incubation"),
        _probe_user(genetic_conditions='["partial_blindness"]'),
    )
    for user in probes:
        flavor = apply_flavor_herb(herb_key, user, day=day)
        if flavor and flavor.get("message"):
            return str(flavor["message"])
    return None


def _format_cure_list(cures: tuple) -> str:
    from engine.genetics import GENETIC_CONDITIONS, HERB_CURABLE_GENETICS

    labels: list[str] = []
    for key in cures[:8]:
        if key in INJURIES:
            labels.append(INJURIES[key]["name"])
        elif key in GENETIC_CONDITIONS and key in HERB_CURABLE_GENETICS:
            labels.append(GENETIC_CONDITIONS[key]["name"])
        elif key in DISEASE_STAGES:
            labels.append(DISEASE_STAGES[key]["name"])
        elif key == "dying":
            labels.append("Dying (stabilize)")
        else:
            labels.append(key.replace("_", " ").title())
    if not labels:
        return ""
    suffix = "…" if len(cures) > 8 else ""
    return f"clears on treat: {', '.join(labels)}{suffix}."


def build_usage_hint(herb_key: str, meta: dict | None = None) -> str:
    """Single-line mechanical hint for compendium pages."""
    meta = meta or HERBS.get(herb_key, {})
    if meta.get("poison") or meta.get("rarity") == "restricted":
        return f"_{STATIC_HINTS.get(herb_key, 'restricted; medic knowledge only.')}_"

    if herb_key in STATIC_HINTS:
        return f"_{STATIC_HINTS[herb_key]}_"

    from engine.conditions import herb_special_effect

    special = herb_special_effect(herb_key, _probe_user())
    if special and special in SPECIAL_MECHANICS:
        return f"_{SPECIAL_MECHANICS[special]}_"

    supplemental = _probe_supplemental_message(herb_key)
    cures = meta.get("cures", ())
    cure_line = _format_cure_list(cures) if cures else ""

    if supplemental and cure_line:
        return f"_{supplemental} {cure_line}_"
    if supplemental:
        return f"_{supplemental}_"
    if cure_line:
        effect = (meta.get("effect") or "").strip()
        if effect and effect not in cure_line:
            return f"_{cure_line} {effect}_"
        return f"_{cure_line}_"

    effect = (meta.get("effect") or "").strip()
    if effect:
        return f"_{effect} use via `/medic action:treat`._"
    return "_use via `/medic action:treat`._"
