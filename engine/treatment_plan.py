"""Three-step treatment checklist for /vitals action:condition."""

from __future__ import annotations

from engine.conditions import parse_injuries
from engine.diseases import illness_displays, is_mental_disease, parse_disease
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
        return "none; herbs and rest should suffice."
    for proc in SURGERY_PROCEDURES.values():
        if injury_key in proc.injury_keys:
            herbs = ", ".join(
                HERBS.get(h, {}).get("name", h.replace("_", " ").title())
                for h in proc.herbs
                if h != "stick"
            )
            sticks = f" + **{proc.stick_count} stick(s)**" if proc.stick_count else ""
            return f"**{proc.label}** (dc {proc.dc}): {herbs}{sticks} via `/medic action:surgery`"
    return "monitor; escalate to a full **medic** if worsening."


def _rest_step(injury_key: str | None, disease_key: str | None) -> str:
    if injury_key:
        info = INJURIES.get(injury_key, {})
        days = info.get("heal_days")
        if days:
            return f"**{days}** sunrise(s) den rest; splint confinement after bone-setting."
        if info.get("permanent"):
            return "lifelong den care; no full recovery expected."
        return "short rest between treatments; avoid hunt and patrol."
    if disease_key == "cough":
        return "quarantine (`/medic action:quarantine`); isolate **3-7** sunrises with herb doses."
    if disease_key == "rot_lung":
        return "strict rest; mullein or marsh-mallow course; no ranging in cold air."
    if disease_key == "shock_emotional":
        return "quiet den; comfort and ritual herbs; no forced activity."
    if disease_key == "shock_physical":
        return "stabilize immediately; warm den, no ranging until pulse steadies."
    if disease_key == "grief_melancholy":
        return "den rest with pack comfort; chamomile, lavender, or borage; no forced hunts."
    return "long rest this sunrise; re-check after `/rollover`."


def build_treatment_checklist(user, *, day: int | None = None) -> str:
    """Return markdown for a 3-step care plan (herbs, surgery, rest)."""
    cond = user["condition"] if "condition" in user.keys() else "healthy"
    hp = int(user["hp"]) if "hp" in user.keys() else 1
    if cond == "dying" or (hp <= 0 and cond != "dead"):
        return (
            "**care plan: dying**\n"
            "1. **death saves**: `/medic action:deathsaves` (3 rounds, con saves)\n"
            "2. **Stabilize**: Medic uses `/medic action:stabilize` (emergency cross-pack OK)\n"
            "3. **Rest**: Den confinement after stabilization; no hunt or combat"
        )
    injuries = parse_injuries(user["active_injuries"] if "active_injuries" in user.keys() else None)
    from engine.herb_buffs import get_buffs

    raw = user["disease"] if "disease" in user.keys() else None
    disease_key, stage = parse_disease(raw)
    overlay = get_buffs(user).get("mental_disease")
    o_key, o_stage = parse_disease(str(overlay)) if overlay else (None, None)

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
    displays = illness_displays(user)
    if displays:
        headline = displays[0][0]
        if disease_key and stage:
            cure_keys = (disease_key, stage)
        if o_key and o_stage and is_mental_disease(o_key):
            cure_keys = cure_keys + (o_key, o_stage)
    elif primary_injury:
        headline = INJURIES.get(primary_injury, {}).get("name", primary_injury)
        cure_keys = (primary_injury,)

    surgery_line = _surgery_step(user, primary_injury)
    for proc in SURGERY_PROCEDURES.values():
        if matching_injury(user, proc):
            surgery_line = _surgery_step(user, primary_injury)
            break

    return (
        f"**care plan: {headline}**\n"
        f"1. **herbs**: {_herb_suggestions(cure_keys)} (`/medic action:treat`)\n"
        f"2. **surgery**: {surgery_line}\n"
        f"3. **rest**: {_rest_step(primary_injury, disease_key)}"
    )
