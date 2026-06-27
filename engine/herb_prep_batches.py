"""Mechanical outcomes for /skills herb_prep scenarios."""

from __future__ import annotations

import random

import database as db
from config import HERB_DRIED_STORAGE_DAYS
from engine.diseases import encode_disease, parse_disease
from engine.herb_buffs import grant_disease_save_advantage, merge_buff_fields
from herbs import HERBS

HERB_PREP_KEYS = frozenset(
    {
        "prep_chew_poultice",
        "prep_mix_tonic",
        "prep_dry_storage",
        "prep_decoct",
        "prep_antidote",
        "prep_sedative",
        "prep_incomplete_antidote",
        "prep_preserve_rare",
        "prep_taste_test",
    }
)

RARE_RARITIES = frozenset({"rare", "very_rare"})
POULTICE_HERBS = frozenset({"plantain", "common_mallow", "catchweed", "arnica", "dock", "alder_bark"})
TONIC_HERBS = frozenset({"heather", "boneset", "feverfew", "sweet_sedge", "lizards_tail"})
DECOCT_HERBS = frozenset({"valerian", "chamomile", "pine_bark", "marsh_mallow", "elderberry"})
SEDATIVE_HERBS = frozenset({"poppy_seeds", "valerian", "dried_skullcap", "passionflower"})


def _guild_id(user, guild_id: int | None) -> int:
    if guild_id:
        return int(guild_id)
    if user and "guild_id" in user.keys() and user["guild_id"]:
        return int(user["guild_id"])
    return 0


def _herb_name(herb_key: str) -> str:
    return HERBS.get(herb_key, {}).get("name", herb_key.replace("_", " ").title())


def _fresh_stacks(wolf_id: int) -> list:
    return [s for s in db.get_herb_stacks(wolf_id) if s["form"] == "fresh"]


def _append_batch_line(lines: list[str], batch: str | None, *, extra: str = "") -> None:
    if batch:
        lines.append(batch + extra)
    else:
        lines.append(
            "_no **fresh** herbs in `/herbs action:bag`; technique holds but nothing stored._"
        )


def _promote_fresh(
    user,
    target_form: str,
    *,
    day: int,
    guild_id: int | None,
    potency: int = 100,
    prefer: frozenset[str] | None = None,
) -> str | None:
    stacks = _fresh_stacks(user["id"])
    if prefer:
        preferred = [s for s in stacks if s["herb_key"] in prefer]
        if preferred:
            stacks = preferred
    if not stacks:
        return None
    stack = random.choice(stacks)
    db.update_herb_stack(
        int(stack["id"]),
        form=target_form,
        acquired_day=day,
        potency=min(120, potency),
    )
    return f"**{_herb_name(stack['herb_key'])}** → **{target_form}** in your forage bag."


def _reduce_random_potency(user, *, amount: int = 25) -> str | None:
    stacks = db.get_herb_stacks(user["id"])
    if not stacks:
        return None
    stack = random.choice(stacks)
    new_pot = max(40, int(stack["potency"]) - amount)
    db.update_herb_stack(int(stack["id"]), potency=new_pot)
    return f"**{_herb_name(stack['herb_key'])}** potency drops to **{new_pot}%**."


def _remove_random_fresh(user) -> str | None:
    stacks = _fresh_stacks(user["id"])
    if not stacks:
        return None
    stack = random.choice(stacks)
    db.remove_herb_stack(int(stack["id"]))
    return f"**{_herb_name(stack['herb_key'])}** spoiled in the chew."


def _extend_rare_stack(user, *, day: int) -> str | None:
    stacks = [
        s
        for s in db.get_herb_stacks(user["id"])
        if HERBS.get(s["herb_key"], {}).get("rarity") in RARE_RARITIES
    ]
    if not stacks:
        return None
    stack = random.choice(stacks)
    db.update_herb_stack(int(stack["id"]), acquired_day=day, potency=min(120, int(stack["potency"]) + 10))
    form = stack["form"]
    return (
        f"**{_herb_name(stack['herb_key'])}** ({form}) sealed for winter; "
        "freshness clock reset (**~6 moons** dried storage)."
    )


def _grant_rare_dried(user, *, day: int, guild_id: int | None) -> str | None:
    gid = _guild_id(user, guild_id)
    if not gid:
        return None
    pool = [k for k, meta in HERBS.items() if meta.get("rarity") in RARE_RARITIES]
    if not pool:
        return None
    herb_key = random.choice(pool)
    db.add_herb_stack(
        user["id"],
        herb_key,
        guild_id=gid,
        acquired_day=day,
        form="dried",
        potency=100,
    )
    return f"preserved **{_herb_name(herb_key)}** (dried) added to your forage bag."


def _halve_or_clear_poison(user, *, outcome: str) -> tuple[dict, list[str]]:
    cond: dict = {}
    lines: list[str] = []
    disease_key, stage = parse_disease(user["disease"] if "disease" in user.keys() else None)
    if disease_key != "mild_poison":
        return cond, lines
    if stage == "venom":
        cond["disease"] = encode_disease("mild_poison", "stung")
        lines.append("_venom burn eases to a common sting._")
    elif random.random() < (1.0 if outcome == "critical_success" else 0.55):
        cond["clear_disease"] = True
        lines.append("_poison clears from the blood._")
    else:
        lines.append("_poison lingers but slackens._")
    return cond, lines


def _try_clear_mild_poison(user, *, outcome: str) -> tuple[dict, list[str]]:
    cond: dict = {}
    lines: list[str] = []
    disease_key, _ = parse_disease(user["disease"] if "disease" in user.keys() else None)
    if disease_key != "mild_poison":
        return cond, lines
    chance = 1.0 if outcome == "critical_success" else 0.7
    if random.random() < chance:
        cond["clear_disease"] = True
        lines.append("_antidote takes hold; poison clears._")
    else:
        cond, extra = _halve_or_clear_poison(user, outcome=outcome)
        lines.extend(extra)
    return cond, lines


def apply_herb_prep_outcome(
    user,
    scenario_key: str,
    *,
    success: bool,
    outcome: str,
    day: int,
    guild_id: int | None = None,
) -> tuple[dict, dict, list[str]]:
    """
    Apply herb_prep /skills mechanics.
    Returns (update_user_fields, set_user_conditions_kwargs, extra_lines).
    """
    if scenario_key not in HERB_PREP_KEYS:
        return {}, {}, []

    user_fields: dict = {}
    cond_fields: dict = {}
    lines: list[str] = []

    if outcome == "critical_failure":
        if scenario_key == "prep_incomplete_antidote":
            from engine.disease_contract import try_contract_disease

            note = try_contract_disease(user, "mild_poison", "stung", chance=0.65)
            if note:
                lines.append(f"poison surges: {note}")
        elif scenario_key == "prep_decoct":
            stacks = [
                s
                for s in db.get_herb_stacks(user["id"])
                if s["form"] in ("decoction", "tonic", "poultice")
            ]
            if stacks:
                stack = random.choice(stacks)
                db.remove_herb_stack(int(stack["id"]))
                lines.append(f"**{_herb_name(stack['herb_key'])}** batch boiled over and ruined.")
            else:
                db.adjust_mood(user["id"], -3)
                lines.append("_decoction ruined; **−3 mood**._")
        return user_fields, cond_fields, lines

    if not success:
        if scenario_key == "prep_chew_poultice" and random.random() < 0.4:
            note = _remove_random_fresh(user)
            if note:
                lines.append(note)
        elif scenario_key == "prep_mix_tonic":
            db.adjust_mood(user["id"], -3)
            lines.append("_contaminated draught; **−3 mood**._")
        elif scenario_key == "prep_dry_storage":
            note = _reduce_random_potency(user, amount=30)
            if note:
                lines.append(f"poor drying; {note}")
            else:
                lines.append("_herbs wilt early; storage botched._")
        elif scenario_key == "prep_decoct":
            note = _reduce_random_potency(user, amount=40)
            if note:
                lines.append(f"ruined batch; {note}")
            else:
                db.adjust_mood(user["id"], -2)
                lines.append("_batch ruined; **−2 mood**._")
        elif scenario_key == "prep_antidote":
            from engine.disease_contract import try_contract_disease

            note = try_contract_disease(user, "mild_poison", "stung", chance=0.55)
            if note:
                lines.append(f"poison wins: {note}")
        elif scenario_key == "prep_sedative":
            db.adjust_mood(user["id"], -2)
            lines.append("_bitter draught; **−2 mood**._")
        elif scenario_key == "prep_incomplete_antidote":
            from engine.disease_contract import try_contract_disease

            note = try_contract_disease(user, "mild_poison", "stung", chance=0.35)
            if note:
                lines.append(f"poison worsens: {note}")
        elif scenario_key == "prep_preserve_rare":
            stacks = [
                s
                for s in db.get_herb_stacks(user["id"])
                if HERBS.get(s["herb_key"], {}).get("rarity") in RARE_RARITIES
            ]
            if stacks:
                stack = random.choice(stacks)
                fade_day = day - max(1, HERB_DRIED_STORAGE_DAYS - 30)
                db.update_herb_stack(int(stack["id"]), acquired_day=fade_day, potency=max(40, int(stack["potency"]) - 20))
                lines.append(
                    f"**{_herb_name(stack['herb_key'])}** fades within **1 moon**; potency lost."
                )
            else:
                lines.append("_rare seal failed; nothing preserved._")
        return user_fields, cond_fields, lines

    # --- success paths ---
    if scenario_key == "prep_chew_poultice":
        from engine.conditions import parse_injuries

        injuries = parse_injuries(
            user["active_injuries"] if "active_injuries" in user.keys() else None
        )
        cond = user["condition"] if "condition" in user.keys() else "healthy"
        if injuries or cond in ("injured", "stable", "dying"):
            user_fields.update(
                merge_buff_fields(user, infection_ward_until_day=day + 1, pain_relief_until_day=day + 1)
            )
            lines.append("_poultice paste: **infection ward** and pain ease until next sunrise._")
        else:
            user_fields.update(merge_buff_fields(user, pain_relief_until_day=day + 1))
            lines.append("_chewed poultice ready: **pain relief** for **1 sunrise**._")
        batch = _promote_fresh(
            user, "poultice", day=day, guild_id=guild_id, prefer=POULTICE_HERBS
        )
        _append_batch_line(lines, batch)

    elif scenario_key == "prep_mix_tonic":
        user_fields.update(grant_disease_save_advantage(user, days=1))
        lines.append("_clean tonic brewed; **advantage** on disease saves **1 sunrise**._")
        batch = _promote_fresh(user, "tonic", day=day, guild_id=guild_id, prefer=TONIC_HERBS)
        _append_batch_line(lines, batch)

    elif scenario_key == "prep_dry_storage":
        duration = 21 if outcome == "critical_success" else 14
        user_fields.update(merge_buff_fields(user, herb_storage_bonus_until_day=day + duration))
        lines.append(
            f"_leaf-wrapped stores keep **50% longer** for **{duration} sunrises**._"
        )
        batch = _promote_fresh(
            user,
            "dried",
            day=day,
            guild_id=guild_id,
            potency=100 if outcome == "critical_success" else 90,
        )
        _append_batch_line(lines, batch)

    elif scenario_key == "prep_decoct":
        days = 3 if outcome == "critical_success" else 1
        user_fields.update(grant_disease_save_advantage(user, days=days))
        potency = 120 if outcome == "critical_success" else 110
        batch = _promote_fresh(
            user, "decoction", day=day, guild_id=guild_id, potency=potency, prefer=DECOCT_HERBS
        )
        lines.append(
            f"_decoction at **{potency}%** potency; disease-save advantage **{days} sunrise(s)**._"
        )
        _append_batch_line(
            lines, batch, extra=" Cure timers **halved** when used." if batch else ""
        )

    elif scenario_key == "prep_antidote":
        user_fields.update(grant_disease_save_advantage(user))
        lines.append("_antidote drawn; advantage on the **next disease save**._")
        poison_cond, poison_lines = _try_clear_mild_poison(user, outcome=outcome)
        cond_fields.update(poison_cond)
        lines.extend(poison_lines)
        batch = _promote_fresh(
            user,
            "tonic",
            day=day,
            guild_id=guild_id,
            potency=100,
            prefer=frozenset({"snakeroot", "sticklewort", "blackberry", "witch_hazel", "jewelweed"}),
        )
        _append_batch_line(lines, batch)

    elif scenario_key == "prep_sedative":
        if outcome == "critical_success":
            user_fields.update(
                merge_buff_fields(
                    user,
                    sedated_until_day=day + 1,
                    sleep_aid_until_day=day + 1,
                    calm_until_day=day + 1,
                )
            )
            lines.append(
                "_honeyed sedative: **calm**, deep rest, and sleep aid until next sunrise._"
            )
        else:
            user_fields.update(
                merge_buff_fields(user, calm_until_day=day + 1, sleep_aid_until_day=day + 1)
            )
            lines.append("_sedative draught ready: **calm** and sleep aid until next sunrise._")
        batch = _promote_fresh(
            user, "tonic", day=day, guild_id=guild_id, prefer=SEDATIVE_HERBS
        )
        _append_batch_line(lines, batch)

    elif scenario_key == "prep_incomplete_antidote":
        user_fields.update(grant_disease_save_advantage(user))
        poison_cond, poison_lines = _halve_or_clear_poison(user, outcome=outcome)
        cond_fields.update(poison_cond)
        lines.append("_improvised antidote: poison **halved**; advantage on next disease save._")
        lines.extend(poison_lines)
        batch = _promote_fresh(
            user,
            "tonic",
            day=day,
            guild_id=guild_id,
            potency=85,
            prefer=frozenset({"snakeroot", "sticklewort", "blackberry", "witch_hazel", "jewelweed"}),
        )
        _append_batch_line(lines, batch)

    elif scenario_key == "prep_preserve_rare":
        note = _extend_rare_stack(user, day=day)
        if note:
            lines.append(note)
        else:
            granted = _grant_rare_dried(user, day=day, guild_id=guild_id)
            if granted:
                user_fields.update(merge_buff_fields(user, herb_storage_bonus_until_day=day + 180))
                lines.append(granted)
                lines.append("_rare stock sealed; bag herbs keep **50% longer** for **6 moons**._")
            else:
                user_fields.update(merge_buff_fields(user, herb_storage_bonus_until_day=day + 30))
                lines.append("_wrapping technique learned; storage **50% longer** for **1 moon**._")

    elif scenario_key == "prep_taste_test":
        user_fields.update(merge_buff_fields(user, venom_save_advantage=True))
        lines.append("_tongue learns the bite; advantage on the **next venom or poison save**._")

    return user_fields, cond_fields, lines
