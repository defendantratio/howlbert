"""Three-step treatment checklist for /vitals action:condition."""

from __future__ import annotations

from engine.conditions import parse_injuries
from engine.diseases import disease_display, parse_disease
from engine.surgery import SURGERY_PROCEDURES, matching_injury
from herbs import HERBS, INJURIES


def _herb_suggestions(cures: tuple[str, ...], limit: int = 4) -> str:
    names: list[str] = []
    for key, meta in HERBS.items():
        if meta.get("poison") or meta.get("rarity") == "restricted":
            continue
        herb_cures = meta.get("cures", ())
        if not herb_cures:
            continue
        if any(c in herb_cures for c in cures):
            names.append(meta.get("name", key.replace("_", " ").title()))
        if len(names) >= limit:
            break
    return ", ".join(names) if names else "comfrey, yarrow (general care)"


def _surgery_step(patient, injury_key: str | None) -> str:
    if not injury_key:
        return "None; herbs and rest should suffice."
    for proc in SURGERY_PROCEDURES.values():
        if injury_key in proc.injury_keys:
            herbs = ", ".join(
                HERBS.get(h, {}).get("name", h.replace("_", " ").title())
                for h in proc.herbs
                if h != "stick"
            )
            sticks = f" + **{proc.stick_count} stick(s)**" if proc.stick_count else ""
            return f"**{proc.label}** (DC {proc.dc}): {herbs}{sticks} via `/medic action:surgery`"
    return "Monitor; escalate to a full **Medic** if worsening."


def _rest_step(injury_key: str | None, disease_key: str | None) -> str:
    if injury_key:
        info = INJURIES.get(injury_key, {})
        days = info.get("heal_days")
        if days:
            return f"**{days}** sunrise(s) den rest; splint confinement after bone-setting."
        if info.get("permanent"):
            return "Lifelong den care; no full recovery expected."
        return "Short rest between treatments; avoid hunt and patrol."
    if disease_key == "cough":
        return "Quarantine (`/quarantine`); isolate **3-7** sunrises with herb doses."
    if disease_key == "rot_lung":
        return "Strict rest; mullein or marsh-mallow course; no ranging in cold air."
    if disease_key == "shock_emotional":
        return "Quiet den; comfort and ritual herbs; no forced activity."
    return "Long rest this sunrise; re-check after `/rollover`."


def build_treatment_checklist(user, *, day: int | None = None) -> str:
    """Return markdown for a 3-step care plan (herbs, surgery, rest)."""
    injuries = parse_injuries(user["active_injuries"] if "active_injuries" in user.keys() else None)
    raw = user["disease"] if "disease" in user.keys() else None
    disease_key, stage = parse_disease(raw)

    primary_injury: str | None = None
    if injuries:
        priority = (
            "infected_wound",
            "deep_gash",
            "spinal_injury",
            "fractured_rib",
            "sprained_leg",
            "broken_jaw",
            "punctured_paw",
        )
        for key in priority:
            if key in injuries:
                primary_injury = key
                break
        if not primary_injury:
            primary_injury = injuries[0]

    cure_keys: tuple[str, ...] = ()
    headline = "General wellness"
    if disease_key and stage:
        display = disease_display(user)
        headline = display[0] if display else disease_key
        cure_keys = (disease_key, stage)
    elif primary_injury:
        headline = INJURIES.get(primary_injury, {}).get("name", primary_injury)
        cure_keys = (primary_injury,)

    surgery_line = _surgery_step(user, primary_injury)
    for proc in SURGERY_PROCEDURES.values():
        if matching_injury(user, proc):
            surgery_line = _surgery_step(user, primary_injury)
            break

    return (
        f"**Care plan: {headline}**\n"
        f"1. **Herbs**: {_herb_suggestions(cure_keys)} (`/vitals action:treat`)\n"
        f"2. **Surgery**: {surgery_line}\n"
        f"3. **Rest**: {_rest_step(primary_injury, disease_key)}"
    )
