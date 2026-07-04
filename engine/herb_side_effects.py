"""Herb side-effect engine.

Turns the previously cosmetic ``side_effects`` compendium text into real,
measurable outcomes. Every archetype below is gated so it stays occasional and
usually skill-avoidable, not a constant tax on healing.

Archetypes:
 ; toxic_ingest      eating an internal-only-dangerous herb: CON save or hp loss
 ; open_wound_toxic  applying a skin-absorbed toxin (comfrey, arnica) to an open
                      wound: toxins enter the blood, CON save or hp loss
 ; abortifacient     internal use on a pregnant wolf: risk of miscarriage
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

    if "abortifacient" in tags and internal:
        is_preg = int(patient["is_pregnant"]) if "is_pregnant" in patient.keys() else 0
        if is_preg and random.random() < 0.35 and not _con_save(patient, 14):
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

    return ("\n" + "\n".join(notes)) if notes else ""
