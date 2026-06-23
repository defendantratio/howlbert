"""Combined movement penalties for hunt payouts (exhaustion, injuries, disease)."""

from __future__ import annotations

from engine.character_traits import trait_hunt_multiplier
from engine.disease_effects import disease_hunt_multiplier
from engine.exhaustion_effects import user_exhaustion
from engine.genetics import genetic_hunt_multiplier
from engine.herb_buffs import broom_splint_active
from engine.injury_effects import has_injury
from engine.long_term_injuries import parse_long_term_injuries
from engine.role_features import role_hunt_multiplier


def apply_movement_hunt_penalty(amount: int, user) -> tuple[int, str]:
    """Apply the worst single movement penalty (penalties don't stack multiplicatively)."""
    if amount <= 0:
        return amount, ""

    mult = 1.0
    notes: list[str] = []
    ex = user_exhaustion(user)
    if ex >= 2:
        mult = min(mult, 0.5)
        notes.append(f"Exhaustion {ex}; speed halved (**−50%**)")
    if has_injury(user, "sprained_leg"):
        mult = min(mult, 0.5)
        notes.append("Sprained leg; movement halved (**−50%**)")
    if has_injury(user, "spinal_injury"):
        mult = min(mult, 0.25)
        notes.append("Spinal injury; drag-hunt only (**−75%**)")
    lt = parse_long_term_injuries(
        user["long_term_injuries"] if "long_term_injuries" in user.keys() else None
    )
    if "limp" in lt:
        mult = min(mult, 0.75)
        notes.append("Limp; speed **−25%**")
    if broom_splint_active(user):
        mult = min(mult, 0.5)
        notes.append("Broom splint; speed halved (**−50%**)")
    dis_mult, dis_note = disease_hunt_multiplier(user)
    if dis_mult < 1.0:
        mult = min(mult, dis_mult)
        notes.append(dis_note.replace(" hunt bones.", ""))
    gen_mult, gen_note = genetic_hunt_multiplier(user)
    if gen_mult < 1.0:
        mult = min(mult, gen_mult)
        notes.append(gen_note.replace(" hunt bones.", ""))
    trait_mult, trait_note = trait_hunt_multiplier(user)
    if trait_mult < 1.0:
        mult = min(mult, trait_mult)
        notes.append(trait_note.replace(" hunt bones.", ""))
    role_mult, role_note = role_hunt_multiplier(user)
    if role_mult < 1.0:
        mult = min(mult, role_mult)
        notes.append(role_note.replace(" hunt bones.", ""))

    if mult >= 1.0:
        return amount, ""

    reduced = max(0, int(amount * mult))
    suffix = " (worst penalty applies)" if len(notes) > 1 else ""
    return reduced, " · ".join(notes) + suffix + "."
