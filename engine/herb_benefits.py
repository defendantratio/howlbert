# herb_benefits.py
"""Herb benefit engine.

Backs the recurring functional descriptors in the compendium ``effect`` text
that previously did nothing on their own. Each is now a small, reliable,
measurable effect applied when the herb is used.

Systemic effects (diuretic, nutritive, appetite, circulation, hypotensive,
analgesic, immune_boost) are the herb's physiological nature and only reach the
body when it is taken internally; external applications
(poultice/ointment/rub/sap) deliver none of them. Antiseptic is wound-applied,
so it fires on any form.
"""

from __future__ import annotations

import database as db

# systemic effects only reach the body when the herb is eaten/drunk
EXTERNAL_FORMS = {"poultice", "ointment", "rub", "sap"}

# liquid prep forms restore a little hydration on top of whatever the herb
# itself does, since the patient is actually drinking something. a gargle is
# rinsed and spat, not swallowed, so it doesn't count. simmered milk also has
# calories, so it nudges hunger too.
LIQUID_HYDRATION_FORMS = {"tea": 3, "simmered_milk": 3}
LIQUID_HUNGER_FORMS = {"simmered_milk": 3}

# herb_key -> benefit archetype tags
HERB_BENEFITS: dict[str, tuple[str, ...]] = {
    # diuretic: flushes the system; costs water but clears inflammation/toxins
    "burdock_root": ("diuretic",),
    "dandelion": ("diuretic",),
    "goldenrod": ("diuretic",),
    "lizards_tail": ("diuretic",),
    "sorrel": ("diuretic", "analgesic"),
    "oxeye_daisy": ("diuretic",),

    # nutritive: vitamins, antioxidants, nourishment
    "elderberry": ("nutritive",),
    "raspberry_leaves": ("nutritive",),
    "labrador_tea": ("nutritive",),
    "mountain_ash": ("nutritive",),  # choleretic: aids digestion of fats

    # appetite stimulant
    "chervil": ("appetite_stimulant",),

    # improves circulation to cold, aching extremities
    "prickly_ash": ("circulation",),

    # lowers blood pressure; eases the pounding, steadies the nerves
    "yarrow": ("hypotensive",),

    # antiseptic: dressing a wound wards off future infection (distinct from
    # curing an existing one)
    "cattail": ("antiseptic", "analgesic"),
    "lambs_ear": ("antiseptic",),
    "juniper_berry": ("antiseptic",),
    "watermint": ("antiseptic", "analgesic"),
    "honey": ("antiseptic",),
    "horsetail": ("antiseptic",),
    "sage": ("antiseptic",),
    "garden_mint": ("antiseptic",),

    # analgesic: eases pain for the sunrise
    "parsley": ("analgesic",),

    # immune-stimulating
    "pine_needle": ("immune_boost",),
}


def _is_internal(form: str) -> bool:
    return form not in EXTERNAL_FORMS


def _drop_pain_exhaustion(patient) -> bool:
    old_pe = int(patient["pain_exhaustion"]) if "pain_exhaustion" in patient.keys() else 0
    if old_pe <= 0:
        return False
    db.update_user(patient["discord_id"], wolf_id=patient["id"], pain_exhaustion=old_pe - 1)
    return True


def roll_herb_benefits(patient, herb_key: str, form: str, *, day: int) -> str:
    """Apply the herb's benefits to ``patient``. Returns a note (or '')."""
    if patient["condition"] in ("dead", "dying"):
        return ""
    tags = HERB_BENEFITS.get(herb_key, ())
    notes: list[str] = []
    buff_updates: dict = {}

    if form in LIQUID_HYDRATION_FORMS:
        new_thirst = db.adjust_thirst(patient["id"], LIQUID_HYDRATION_FORMS[form])
        notes.append(f"_you drink it down; hydration **{new_thirst}**, +{LIQUID_HYDRATION_FORMS[form]}._")
    if form in LIQUID_HUNGER_FORMS:
        new_hunger = db.adjust_hunger(patient["id"], LIQUID_HUNGER_FORMS[form])
        notes.append(f"_the milk has some substance to it; satiety **{new_hunger}**, +{LIQUID_HUNGER_FORMS[form]}._")

    if not tags:
        return ("\n" + "\n".join(notes)) if notes else ""

    internal = _is_internal(form)

    if internal and "diuretic" in tags:
        new_thirst = db.adjust_thirst(patient["id"], -5)
        flushed = _drop_pain_exhaustion(patient)
        flush_note = "; toxins flush, **-1 pain exhaustion**" if flushed else ""
        notes.append(f"_diuretic; you pass more water (hydration **{new_thirst}**, -5){flush_note}._")

    if internal and "nutritive" in tags:
        new_hunger = db.adjust_hunger(patient["id"], 4)
        notes.append(f"_nourishing; vitamins and antioxidants settle the gut (satiety **{new_hunger}**, +4)._")

    if internal and "appetite_stimulant" in tags:
        new_hunger = db.adjust_hunger(patient["id"], 5)
        notes.append(f"_whets the appetite; you feel hungrier (satiety **{new_hunger}**, +5)._")

    if internal and "circulation" in tags:
        if _drop_pain_exhaustion(patient):
            notes.append("_warmth returns to cold, aching limbs; **-1 pain exhaustion**._")

    if internal and "hypotensive" in tags:
        new_mood = db.adjust_mood(patient["id"], 2)
        notes.append(f"_the pounding eases; nerves steady (mood **{new_mood}**, +2)._")

    # --- buff-based effects (merged into one herb_buffs write) ---
    if "antiseptic" in tags:  # wound-applied; any form
        buff_updates["infection_ward_until_day"] = day + 1
        notes.append("_antiseptic; the wound is warded against infection until next sunrise._")

    if internal and "analgesic" in tags:
        buff_updates["pain_relief_until_day"] = day
        notes.append("_analgesic; pain eases for the sunrise._")

    if buff_updates:
        from engine.herb_buffs import merge_buff_fields
        fresh = db.get_user_by_id(patient["id"]) or patient
        fields = merge_buff_fields(fresh, **buff_updates)
        db.update_user(patient["discord_id"], wolf_id=patient["id"], **fields)

    if internal and "immune_boost" in tags:
        from engine.herb_buffs import grant_disease_save_advantage
        fresh_i = db.get_user_by_id(patient["id"]) or patient
        db.update_user(patient["discord_id"], wolf_id=patient["id"], **grant_disease_save_advantage(fresh_i))
        notes.append("_immune-stimulating; advantage on your next disease save._")

    return ("\n" + "\n".join(notes)) if notes else ""