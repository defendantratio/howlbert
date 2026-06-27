"""Mechanical rolls for human-world hazards (/combat hazard)."""

from __future__ import annotations

import json
import random

import database as db
from engine.bestiary import HAZARD_TOPICS
from engine.character import parse_proficiencies
from engine.combat_injuries import apply_injury_to_list, injury_label
from engine.conditions import parse_injuries
from engine.dice import format_roll_result, resolve_check
from engine.disease_contract import try_contract_disease


def grant_field_injury(user, injury_key: str, *, day: int) -> str | None:
    injuries = parse_injuries(
        user["active_injuries"] if "active_injuries" in user.keys() else None
    )
    if injury_key in injuries:
        return None
    injuries = apply_injury_to_list(injuries, injury_key)
    db.update_user_by_id(user["id"], active_injuries=json.dumps(injuries))
    db.record_injury_since(user["id"], injury_key, day)
    return injury_label(injury_key)


def _append_hazard_damage(user, amount: int, lines: list[str]) -> int:
    from engine.vitals import apply_hp_damage

    _, extras = apply_hp_damage(user, amount)
    lines.extend(extras)
    return amount


def _proficient(user, skill_key: str) -> bool:
    profs = parse_proficiencies(user["skill_proficiencies"])
    return skill_key in profs or "herblore" in profs


def roll_human_hazard(user, *, day: int) -> tuple[bool, str]:
    ref_title, _ = HAZARD_TOPICS["humans"]
    result = resolve_check(
        user,
        attr_keys=("attr_dex",),
        skill="Stealth",
        dc=12,
        proficient=_proficient(user, "stealth"),
        skill_key="stealth",
        game_day=day,
        fear_context="twolegplace",
    )
    lines = [f"**{ref_title}**", format_roll_result(result)]
    if result["success"]:
        lines.append("you slip past soft-pawed; no thunderstick, no shouting.")
        return True, "\n".join(lines)

    lines.append("a **twoleg** spots you and raises a **thunderstick**.")
    escape = resolve_check(
        user,
        attr_keys=("attr_dex",),
        skill=None,
        dc=14,
        proficient=False,
        skill_key=None,
        game_day=day,
    )
    lines.append(format_roll_result(escape))
    if escape["success"]:
        lines.append("you dive into cover before the shot; heart hammering.")
        db.adjust_mood(user["id"], -3)
        lines.append("**−3 mood** from the close call.")
        return True, "\n".join(lines)

    human_roll = random.randint(1, 20) + 2
    dmg = random.randint(2, 12)
    lines.append(f"thunderstick fires (**{human_roll}** vs your cover). **−{dmg} hp**.")
    _append_hazard_damage(user, dmg, lines)
    if human_roll >= 20:
        inj = grant_field_injury(user, "sprained_leg", day=day)
        if inj:
            lines.append(f"critical hit; {inj}")
    db.adjust_mood(user["id"], -6)
    lines.append("**−6 mood**; flee before they call hearth-hounds.")
    return False, "\n".join(lines)


def roll_thunderpath_hazard(user, *, day: int) -> tuple[bool, str]:
    ref_title, _ = HAZARD_TOPICS["thunderpath"]
    scenario = random.randint(1, 20)
    lines = [f"**{ref_title}**"]
    if scenario <= 10:
        lines.append("_the verge is quiet; no monster roar on the wind._")
        result = resolve_check(
            user,
            attr_keys=("attr_dex",),
            skill=None,
            dc=8,
            proficient=False,
            skill_key=None,
            game_day=day,
        )
        lines.append(format_roll_result(result))
        if result["success"]:
            lines.append("you cross the black stone in a breath.")
            return True, "\n".join(lines)
        dmg = random.randint(1, 4)
        _append_hazard_damage(user, dmg, lines)
        lines.append(f"you stumble on loose grit; **−{dmg} hp** but you're across.")
        return False, "\n".join(lines)

    if scenario <= 17:
        monster = random.randint(1, 20) + 8
        lines.append(f"_a **monster** roars closer; you judge the gap (needs **{monster}**)._")
        result = resolve_check(
            user,
            attr_keys=("attr_int", "attr_wis"),
            skill="Survival",
            dc=monster,
            proficient=_proficient(user, "survival"),
            skill_key="survival",
            game_day=day,
        )
        lines.append(format_roll_result(result))
        if result["success"]:
            lines.append("you flatten in the culvert until the roar fades.")
            return True, "\n".join(lines)
        if result["outcome"] == "critical_failure":
            dmg = random.randint(4, 29)
            _append_hazard_damage(user, dmg, lines)
            inj = grant_field_injury(user, "fractured_rib", day=day) or grant_field_injury(
                user, "sprained_leg", day=day
            )
            lines.append(f"you're on the path when it hits; **−{dmg} hp**.")
            if inj:
                lines.append(inj)
            return False, "\n".join(lines)
        db.adjust_mood(user["id"], -4)
        lines.append("you abort the crossing; **−4 mood**.")
        return False, "\n".join(lines)

    lines.append("_headlights sweep the fog; a **monster** bears down fast._")
    result = resolve_check(
        user,
        attr_keys=("attr_dex",),
        skill="Sprint",
        dc=20,
        proficient=_proficient(user, "stealth"),
        skill_key="stealth",
        game_day=day,
    )
    lines.append(format_roll_result(result))
    if result["success"]:
        lines.append("you clear the thunderpath on three legs and a prayer.")
        return True, "\n".join(lines)
    if result["outcome"] == "critical_failure":
        lines.append("the impact is instant; the pack will have to drag you off.")
        _append_hazard_damage(user, int(user["hp"]), lines)
        return False, "\n".join(lines)
    dmg = random.randint(4, 29)
    _append_hazard_damage(user, dmg, lines)
    inj = grant_field_injury(user, "sprained_leg", day=day)
    lines.append(f"glancing blow; **−{dmg} hp**.")
    if inj:
        lines.append(inj)
    return False, "\n".join(lines)


def roll_trap_hazard(user, *, day: int) -> tuple[bool, str]:
    ref_title, _ = HAZARD_TOPICS["traps"]
    result = resolve_check(
        user,
        attr_keys=("attr_int",),
        skill="Tracking",
        dc=15,
        proficient=_proficient(user, "tracking"),
        skill_key="tracking",
        game_day=day,
    )
    lines = [f"**{ref_title}**", format_roll_result(result)]
    if result["success"]:
        lines.append("iron-stink on the wind; you skirt the jaws before they bite.")
        return True, "\n".join(lines)

    dmg = random.randint(2, 10)
    _append_hazard_damage(user, dmg, lines)
    lines.append(f"**caught**; trap jaws close. **−{dmg} hp**.")
    trap_dc = random.randint(1, 20) + 5
    escape = resolve_check(
        user,
        attr_keys=("attr_str",),
        skill=None,
        dc=trap_dc,
        proficient=False,
        skill_key=None,
        game_day=day,
    )
    lines.append(f"escape (trap strength **{trap_dc}**): {format_roll_result(escape)}")
    if escape["success"]:
        lines.append("you wrench free, bleeding but mobile.")
        return False, "\n".join(lines)
    extra = random.randint(1, 4)
    _append_hazard_damage(user, extra, lines)
    inj = grant_field_injury(user, "sprained_leg", day=day)
    lines.append(f"the trap bites again; **−{extra} hp**.")
    if inj:
        lines.append(inj)
    lines.append("_untreated: infection risk; see a medic._")
    return False, "\n".join(lines)


def roll_twoleg_nest_hazard(user, *, day: int, guild_id: int) -> tuple[bool, str]:
    ref_title, _ = HAZARD_TOPICS["twoleg_nests"]
    stealth = resolve_check(
        user,
        attr_keys=("attr_dex",),
        skill="Stealth",
        dc=15,
        proficient=_proficient(user, "stealth"),
        skill_key="stealth",
        game_day=day,
        fear_context="twolegplace",
    )
    lines = [f"**{ref_title}**", format_roll_result(stealth)]
    if not stealth["success"]:
        dmg = random.randint(1, 4)
        _append_hazard_damage(user, dmg, lines)
        ex = min(6, int(user["exhaustion"]) + 1)
        db.set_user_conditions(user["discord_id"], wolf_id=user["id"], exhaustion=ex)
        db.adjust_mood(user["id"], -5)
        lines.append(
            f"a porch light and shouting; **−{dmg} hp**, **+1 exhaustion**, **−5 mood**."
        )
        return False, "\n".join(lines)

    forage = resolve_check(
        user,
        attr_keys=("attr_wis",),
        skill="Survival",
        dc=8,
        proficient=_proficient(user, "survival"),
        skill_key="survival",
        game_day=day,
    )
    lines.append(format_roll_result(forage))
    if not forage["success"]:
        lines.append("the rubbish heap is picked clean.")
        return False, "\n".join(lines)

    if random.random() < 0.55:
        bones = random.randint(4, 10)
        db.add_bones(user["discord_id"], bones, wolf_id=user["id"])
        lines.append(f"scrap and string; **+{bones} bones**.")
    else:
        from engine.herb_habitat import herbs_for_verge

        pool = herbs_for_verge("compound") or ["dandelion"]
        herb_key = random.choice(pool)
        stack_id = db.add_herb_stack(
            user["id"], herb_key, guild_id=guild_id, acquired_day=day
        )
        from herbs import HERBS

        name = HERBS.get(herb_key, {}).get("name", herb_key)
        lines.append(f"windfall **{name}**; stack `#{stack_id}`.")

    poison = resolve_check(
        user,
        attr_keys=("attr_con",),
        skill="Constitution",
        dc=12,
        proficient=False,
        skill_key=None,
        game_day=day,
    )
    lines.append(format_roll_result(poison))
    if not poison["success"]:
        note = try_contract_disease(user, "mild_poison", "stung", chance=1.0)
        if note:
            lines.append(f"spoiled twoleg scraps; {note}")
        return False, "\n".join(lines)
    lines.append("you melt back to the treeline with full jaws.")
    return True, "\n".join(lines)


def roll_fence_hazard(user, *, day: int) -> tuple[bool, str]:
    ref_title, _ = HAZARD_TOPICS["fences"]
    fence = random.choice(("wooden", "wire", "electric"))
    lines = [f"**{ref_title}**", f"_fence type: **{fence}**._"]
    if fence == "wooden":
        result = resolve_check(
            user,
            attr_keys=("attr_dex",),
            skill=None,
            dc=10,
            proficient=False,
            skill_key=None,
            game_day=day,
        )
        lines.append(format_roll_result(result))
        if result["success"]:
            lines.append("over the top; splinters, but free.")
            return True, "\n".join(lines)
        dmg = random.randint(1, 4)
        _append_hazard_damage(user, dmg, lines)
        lines.append(f"fur catches on a nail; **−{dmg} hp**, but you're over.")
        return True, "\n".join(lines)

    if fence == "wire":
        result = resolve_check(
            user,
            attr_keys=("attr_str", "attr_con"),
            skill="Survival",
            dc=8,
            proficient=_proficient(user, "survival"),
            skill_key="survival",
            game_day=day,
        )
        lines.append(format_roll_result(result))
        if result["success"]:
            lines.append("you dig under the wire without a cut.")
            return True, "\n".join(lines)
        if result["outcome"] == "critical_failure":
            inj = grant_field_injury(user, "punctured_paw", day=day)
            lines.append("wire slices deep into the pad.")
            if inj:
                lines.append(inj)
            return False, "\n".join(lines)
        dmg = random.randint(1, 3)
        _append_hazard_damage(user, dmg, lines)
        lines.append(f"a barb tears fur; **−{dmg} hp**.")
        return False, "\n".join(lines)

    result = resolve_check(
        user,
        attr_keys=("attr_wis",),
        skill="Survival",
        dc=18,
        proficient=_proficient(user, "survival"),
        skill_key="survival",
        game_day=day,
    )
    lines.append(format_roll_result(result))
    if result["success"]:
        lines.append("you find a dead gap in the current.")
        return True, "\n".join(lines)
    dmg = random.randint(1, 6)
    _append_hazard_damage(user, dmg, lines)
    lines.append(f"**electric snap**; **−{dmg} hp**. you cannot move next beat (1 round).")
    return False, "\n".join(lines)


def resolve_combat_hazard(
    user,
    topic: str,
    *,
    day: int,
    guild_id: int | None = None,
) -> tuple[bool, str, str]:
    """Returns (success, title, body)."""
    title, ref = HAZARD_TOPICS.get(topic, HAZARD_TOPICS["humans"])
    if topic == "humans":
        ok, body = roll_human_hazard(user, day=day)
    elif topic == "thunderpath":
        ok, body = roll_thunderpath_hazard(user, day=day)
    elif topic == "traps":
        ok, body = roll_trap_hazard(user, day=day)
    elif topic == "twoleg_nests":
        ok, body = roll_twoleg_nest_hazard(
            user, day=day, guild_id=guild_id or 0
        )
    elif topic == "fences":
        ok, body = roll_fence_hazard(user, day=day)
    else:
        return True, title, ref

    body += f"\n\n_{ref.split(chr(10))[0]}_"
    return ok, title, body
