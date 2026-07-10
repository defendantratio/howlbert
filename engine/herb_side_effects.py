# herb_side_effects.py
"""Herb side-effect engine.

Turns the previously cosmetic ``side_effects`` compendium text into real,
measurable outcomes. Every archetype below is gated so it stays occasional and
usually skill-avoidable, not a constant tax on healing.

Archetypes:
 ; toxic_ingest      eating an internal-only-dangerous herb: CON save or hp loss
 ; open_wound_toxic  applying a skin-absorbed toxin (comfrey, arnica) to an open
                      wound: toxins enter the blood, CON save or hp loss
 ; abortifacient     internal use on a pregnant wolf: risk of miscarriage (35%)
 ; mild_abortifacient  as above but a smaller risk (15%): herbs merely "avoid in pregnancy"
 ; sedative_overdose heavy sedatives: chance of grogginess (+1 exhaustion)
 ; allergy           allergenic herbs: chance of a mild reaction (mood/pain)
 ; laxative          strong-laxative herbs: chance to contract diarrhea
 ; bleeding_risk     salicylate/anticoagulant herbs used on an open wound: bleed

Addiction (poppy, valerian, willow, wild cherry) lives in
``engine.herb_addiction`` and is applied at rollover.
"""

from __future__ import annotations

import random

import database as db
from engine.character import parse_proficiencies

# forms applied to the skin; internal-only side effects never fire on these
EXTERNAL_FORMS = {"poultice", "ointment", "rub", "sap"}

# open-skin injuries where anticoagulant herbs raise the bleed risk
OPEN_WOUND_INJURIES = {"deep_gash", "torn_claw", "punctured_paw", "internal_bleeding"}

# herb_key -> tuple of side-effect archetype tags
HERB_SIDE_EFFECTS: dict[str, tuple[str, ...]] = {
    # toxic if eaten (culinary/medicinal herbs the compendium warns "toxic in
    # large amounts" / "do not eat" / "unsafe internally"); restricted poisons
    # are handled by the separate poison/toxic_if_fresh system, not here.
    "comfrey": ("toxic_ingest", "abortifacient", "open_wound_toxic"),
    "arnica": ("open_wound_toxic",),
    "coltsfoot": ("toxic_ingest",),
    "boneset": ("toxic_ingest", "laxative"),
    "borage": ("toxic_ingest",),
    "alder_bark": ("toxic_ingest",),
    "ragwort": ("toxic_ingest",),
    "tansy": ("toxic_ingest", "abortifacient"),
    "labrador_tea": ("toxic_ingest",),
    "lizards_tail": ("toxic_ingest",),
    "sweet_sedge": ("toxic_ingest",),
    "wood_sorrel": ("toxic_ingest",),
    "sorrel": ("toxic_ingest",),
    "skunk_cabbage": ("toxic_ingest",),
    "mountain_ash": ("toxic_ingest",),
    "elderberry": ("toxic_ingest",),
    "beech_leaves": ("toxic_ingest",),
    "celandine": ("toxic_ingest", "laxative"),
    "wild_cherry_bark": ("toxic_ingest",),
    "juniper_berry": ("toxic_ingest",),
    "sage": ("toxic_ingest",),
    "rosemary": ("toxic_ingest",),
    "edelweiss": ("toxic_ingest",),
    "horsetail": ("toxic_ingest",),
    "rush_stalks": ("toxic_ingest",),

    # abortifacient / dangerous in pregnancy
    "parsley": ("abortifacient",),
    "watermint": ("abortifacient",),
    "catmint": ("abortifacient",),
    "mugwort": ("abortifacient",),
    "shepherds_purse": ("abortifacient",),
    "pine_needle": ("abortifacient",),
    "raspberry_leaves": ("abortifacient",),
    "saffron": ("abortifacient",),
    "passionflower": ("abortifacient",),
    "slippery_elm": ("abortifacient",),  # compendium: "whole bark may be abortifacient / cause miscarriage"
    # smaller risk: compendium only says "avoid in pregnancy" / "safety not established".
    "cattail": ("mild_abortifacient",),
    "heather": ("mild_abortifacient",),

    # sedative overdose (grogginess)
    "poppy_seeds": ("sedative_overdose",),
    "valerian": ("sedative_overdose",),
    "dried_skullcap": ("sedative_overdose",),
    "snakeroot": ("sedative_overdose",),

    # allergenic
    "ragweed": ("allergy",),
    "coneflower": ("allergy",),
    "chamomile": ("allergy",),
    "cobnuts": ("allergy",),
    "oxeye_daisy": ("allergy",),
    "plantain": ("allergy",),
    "yarrow": ("allergy",),

    # strong laxative
    "bindweed": ("laxative",),

    # bleeding risk on open wounds (salicylates / anticoagulants)
    "willow_bark": ("bleeding_risk",),
    "meadowsweet": ("bleeding_risk",),
    "pine_bark": ("bleeding_risk",),
    "prickly_ash": ("bleeding_risk",),
    "feverfew": ("bleeding_risk",),  # inhibits platelets; raises bleed risk

    # cardiac-glycoside toxin: dangerous eaten, even though it cures pox/curse
    "swamp_milkweed": ("toxic_ingest",),
}

# herbs the compendium warns cause "nausea, vomiting" when eaten: an internal
# dose can bring the meal (and fluids) back up.
EMESIS_HERBS = frozenset({
    "adders_tongue", "alder_bark", "beech_leaves", "celandine", "mountain_ash",
    "sage", "rosemary", "saffron", "wood_sorrel", "sorrel", "elderberry",
    "edelweiss", "coltsfoot", "skunk_cabbage", "juniper_berry",
})

# prolonged internal overuse damages an organ. herb_key -> (long-term type,
# cumulative internal doses before the damage becomes permanent). Tracked in the
# ``herb_organ_log`` JSON column; unlike addiction, this tally does not decay.
ORGAN_TOXIC_HERBS: dict[str, tuple[str, int]] = {
    "alder_bark": ("low_potassium", 8),
    "juniper_berry": ("kidney_damage", 8),
    "sorrel": ("kidney_damage", 8),
    "wood_sorrel": ("kidney_damage", 8),
    "oak_bark": ("liver_damage", 8),
    "ragwort": ("liver_damage", 6),
    "comfrey": ("liver_damage", 8),
    "horsetail": ("thiamine_deficiency", 8),
    "rush_stalks": ("thiamine_deficiency", 8),
    "stinging_nettle": ("thiamine_deficiency", 10),
    "dock": ("kidney_damage", 10),        # oxalates strain the kidneys
    "witch_hazel": ("liver_damage", 10),   # high oral doses harm liver/kidney
    "burdock_root": ("liver_damage", 10),  # high doses may harm the liver
}


def _is_internal(form: str) -> bool:
    return form not in EXTERNAL_FORMS


def _skilled(user) -> bool:
    """A trained herbalist prepares carefully and dodges most reactions."""
    profs = parse_proficiencies(user["skill_proficiencies"] if "skill_proficiencies" in user.keys() else None)
    return "herblore" in profs or "medicine" in profs


def _con_save(user, dc: int) -> bool:
    from engine.character import attr_modifier
    mod = attr_modifier(int(user["attr_con"]) if "attr_con" in user.keys() else 5)
    return random.randint(1, 20) + mod >= dc


def roll_herb_side_effects(patient, herb_key: str, form: str, *, day: int) -> str:
    """Apply any triggered side effects to ``patient``. Returns a note (or '')."""
    tags = HERB_SIDE_EFFECTS.get(herb_key, ())
    if not tags:
        return ""
    if patient["condition"] in ("dead", "dying"):
        return ""
    internal = _is_internal(form)
    skilled = _skilled(patient)
    notes: list[str] = []

    if "toxic_ingest" in tags and internal:
        # skilled preparers know the safe dose; laypeople gamble
        chance = 0.20 if skilled else 0.45
        if random.random() < chance and not _con_save(patient, 12):
            dmg = random.randint(1, 3)
            new_hp = max(0, int(patient["hp"]) - dmg)
            db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], hp=new_hp)
            notes.append(f"_the raw plant gripes the gut; **-{dmg} hp** from the toxins._")

    if "open_wound_toxic" in tags and not internal:
        from engine.conditions import parse_injuries
        injuries = parse_injuries(patient["active_injuries"] if "active_injuries" in patient.keys() else None)
        if any(i in OPEN_WOUND_INJURIES for i in injuries):
            chance = 0.25 if skilled else 0.50
            if random.random() < chance and not _con_save(patient, 12):
                dmg = random.randint(1, 4)
                new_hp = max(0, int(patient["hp"]) - dmg)
                db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], hp=new_hp)
                notes.append(f"_pressed to broken skin, the toxins seep into the blood; **-{dmg} hp**. use it only on closed injuries._")

    if ("abortifacient" in tags or "mild_abortifacient" in tags) and internal:
        is_preg = int(patient["is_pregnant"]) if "is_pregnant" in patient.keys() else 0
        # a full abortifacient is a real hazard; a mild one (herbs merely "avoid in
        # pregnancy") is a smaller risk.
        chance = 0.35 if "abortifacient" in tags else 0.15
        if is_preg and random.random() < chance and not _con_save(patient, 14):
            db.clear_pregnancy(patient["id"])
            db.adjust_mood(patient["id"], -15)
            notes.append("_the herb brings on cramping; the pregnancy is **lost**. mood plummets._")

    if "sedative_overdose" in tags and internal:
        if random.random() < 0.25:
            old_ex = int(patient["exhaustion"]) if "exhaustion" in patient.keys() else 0
            from engine.exhaustion_effects import EXHAUSTION_MAX
            new_ex = min(EXHAUSTION_MAX, old_ex + 1)
            if new_ex != old_ex:
                db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], exhaustion=new_ex)
                notes.append("_the sedative drags you under; groggy and slow, **+1 exhaustion**._")

    if "allergy" in tags and not skilled:
        if random.random() < 0.12:
            from engine.exhaustion_effects import PAIN_EXHAUSTION_MAX
            old_pe = int(patient["pain_exhaustion"]) if "pain_exhaustion" in patient.keys() else 0
            new_pe = min(PAIN_EXHAUSTION_MAX, old_pe + 1)
            db.update_user(patient["discord_id"], wolf_id=patient["id"], pain_exhaustion=new_pe)
            notes.append("_an allergic flare; itching and swelling, **+1 pain exhaustion**._")

    if "laxative" in tags and internal:
        if random.random() < 0.20:
            from engine.disease_contract import try_contract_disease
            got = try_contract_disease(patient, "diarrhea", chance=1.0)
            if got:
                notes.append(f"_the purgative runs straight through you. {got}_")

    if "bleeding_risk" in tags:
        from engine.conditions import parse_injuries
        injuries = parse_injuries(patient["active_injuries"] if "active_injuries" in patient.keys() else None)
        if any(i in OPEN_WOUND_INJURIES for i in injuries) and random.random() < 0.25:
            dmg = random.randint(1, 2)
            new_hp = max(0, int(patient["hp"]) - dmg)
            db.set_user_conditions(patient["discord_id"], wolf_id=patient["id"], hp=new_hp)
            notes.append(f"_the salicylates thin the blood; the open wound weeps afresh, **-{dmg} hp**._")

    # vomiting: an internal dose of a nauseating herb brings the meal back up,
    # costing hunger and fluids. skilled preparers pick a gentler dose.
    if herb_key in EMESIS_HERBS and internal:
        chance = 0.10 if skilled else 0.22
        if random.random() < chance and not _con_save(patient, 11):
            note = _apply_vomiting(patient)
            if note:
                notes.append(note)

    # cumulative organ toxicity from prolonged internal overuse.
    if herb_key in ORGAN_TOXIC_HERBS and internal:
        note = _tally_organ_toxicity(patient, herb_key, day=day)
        if note:
            notes.append(note)

    return ("\n" + "\n".join(notes)) if notes else ""


def _apply_vomiting(patient) -> str:
    """The wolf throws up the dose and its meal: lose hunger, fluids, and mood."""
    from config import HUNGER_MIN, THIRST_MIN
    hunger = int(patient["hunger"]) if "hunger" in patient.keys() and patient["hunger"] is not None else 100
    thirst = int(patient["thirst"]) if "thirst" in patient.keys() and patient["thirst"] is not None else 100
    new_hunger = max(HUNGER_MIN, hunger - 8)
    new_thirst = max(THIRST_MIN, thirst - 6)
    db.update_user(patient["discord_id"], wolf_id=patient["id"], hunger=new_hunger, thirst=new_thirst)
    db.adjust_mood(patient["id"], -3)
    return "_the herb turns the stomach; you retch it back up. **-8 hunger, -6 hydration, -3 mood**._"


def _tally_organ_toxicity(patient, herb_key: str, *, day: int) -> str:
    """Count lifetime internal doses of an organ-toxic herb; once the tally
    crosses the herb's threshold, the damage becomes a permanent long-term
    condition. Returns a note when the damage lands (or a near-warning)."""
    import json
    organ, threshold = ORGAN_TOXIC_HERBS[herb_key]
    raw = patient["herb_organ_log"] if "herb_organ_log" in patient.keys() else None
    try:
        log = json.loads(raw) if raw else {}
        if not isinstance(log, dict):
            log = {}
    except (json.JSONDecodeError, TypeError):
        log = {}
    # already damaged this organ? stop tallying this herb.
    from engine.long_term_injuries import parse_long_term_injuries, add_long_term_injury, LONG_TERM_TYPES
    existing = parse_long_term_injuries(patient["long_term_injuries"] if "long_term_injuries" in patient.keys() else None)
    if organ in existing:
        return ""
    count = int(log.get(herb_key, 0)) + 1
    log[herb_key] = count
    db.update_user(patient["discord_id"], wolf_id=patient["id"], herb_organ_log=json.dumps(log))
    if count >= threshold:
        add_long_term_injury(patient["id"], organ)
        label = LONG_TERM_TYPES[organ]["label"]
        return f"_years of leaning on {herb_key.replace('_', ' ')} have taken their toll; **{label}** has set in for good._"
    if count == threshold - 1:
        return f"_{herb_key.replace('_', ' ')} is straining the body; one more heavy dose may leave a permanent mark._"
    return ""
