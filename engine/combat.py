import random

from engine.character import attr_modifier
from engine.character_traits import (
    trait_combat_modifier,
    trait_damage_reduction,
)
from engine.combat_guide import COMBAT_MANEUVERS
from engine.combat_status import attacker_roll_modifiers, maneuver_pin_block, roll_attack_die
from engine.rolls import roll_d20
from engine.injury_effects import attack_roll_modifiers, bite_attack_blocked
CRIT_HIT_EFFECTS = {
    1: "Bonus damage (+1d4)",
    2: "Knock target prone",
    3: "Disarm; target drops held item or loses grip",
    4: "Temporary bleed; target loses 1 HP per round for 3 rounds (3 HP now)",
}

CRIT_FUMBLE_EFFECTS = {
    1: "Drop guard; enemy gets a free attack on you",
    2: "Strain muscle; disadvantage on your next attack roll",
    3: "Stumble; you fall prone",
    4: "Bite own tongue: 1 damage; cannot speak or use vocal skills for 1 round",
}


def _apply_defender_damage_reduction(defender, damage: int, extra: str) -> tuple[int, str]:
    if damage <= 0:
        return damage, extra
    reduction, label = trait_damage_reduction(defender)
    if reduction <= 0:
        return damage, extra
    new_damage = max(0, damage - reduction)
    note = f"_{label}: −{reduction} damage._"
    extra = (extra + " " + note).strip() if extra else note
    return new_damage, extra


def _apply_crit_to_damage(damage: int) -> tuple[int, int, str]:
    effect = random.randint(1, 4)
    if effect == 1:
        damage += random.randint(1, 4)
    elif effect == 4:
        damage += 3
    return damage, effect, CRIT_HIT_EFFECTS[effect]


def _roll_fumble() -> tuple[int, str, int]:
    effect = random.randint(1, 4)
    self_damage = 1 if effect == 4 else 0
    return effect, CRIT_FUMBLE_EFFECTS[effect], self_damage


def _attack_result_base(attack_name: str) -> dict:
    return {
        "attack_name": attack_name,
        "hit": False,
        "crit": False,
        "fumble": False,
        "blocked": False,
        "block_reason": "",
        "attacker_roll": 0,
        "attacker_mod": 0,
        "attacker_total": 0,
        "defender_roll": 0,
        "defender_mod": 0,
        "defender_total": 0,
        "damage": 0,
        "extra": "",
        "crit_effect": None,
        "fumble_effect": None,
        "fumble_self_damage": 0,
    }


def _trait_skill_bonus(user, skill: str) -> int:
    from engine.character_traits import trait_check_adjustments
    from rpg_rules import SKILLS

    attr_keys = SKILLS.get(skill, ((),))[0]
    mod, _ = trait_check_adjustments(user, attr_keys, skill_key=skill)
    return mod


def _prof_bonus(user, skill: str) -> int:
    return _trait_skill_bonus(user, skill)


def overlay_fighter_hp(base_stats, fighter) -> dict:
    """merge encounter hp onto profile/npc stats for maneuver resolution."""
    stats = _combat_stats(base_stats)
    stats["hp"] = int(fighter["hp"])
    stats["max_hp"] = int(fighter["max_hp"])
    return stats


def _combat_stats(stats) -> dict:
    """normalize sqlite3.row or dict; row has no .get(), which breaks attack resolution."""
    if isinstance(stats, dict):
        return stats
    if hasattr(stats, "keys"):
        return {key: stats[key] for key in stats.keys()}
    return dict(stats)


def roll_initiative(user) -> tuple[int, int, int]:
    die = roll_d20()
    mod = attr_modifier(user["attr_dex"])
    return die, mod, die + mod


def npc_combat_stats(*, dex: int = 12, strength: int = 14) -> dict:
    """generic fallback stat block when no bestiary template is set."""
    return {
        "attr_str": strength,
        "attr_dex": dex,
        "attr_con": 10,
        "attr_int": 10,
        "attr_cha": 10,
        "attr_wis": 10,
        "skill_proficiencies": "[]",
    }


def _attack_roll_modifiers(attacker, attack_type, attacker_f, defender_f):
    encounter_id = None
    if attacker_f is not None and "encounter_id" in attacker_f.keys():
        encounter_id = attacker_f["encounter_id"]
    disadvantage, advantage, fear_note = attacker_roll_modifiers(
        attacker,
        attack_type,
        attacker_f,
        defender_f,
        encounter_id=encounter_id,
    )
    from engine.role_features import try_consume_commanding_howl_combat_buff

    if attacker and try_consume_commanding_howl_combat_buff(attacker):
        if disadvantage and advantage:
            advantage = False
        elif not disadvantage:
            advantage = True
    return disadvantage, advantage, fear_note


def _resolve_attack_profile(
    attacker,
    defender,
    attack_type: str,
    profile: dict,
    *,
    attacker_f=None,
    defender_f=None,
) -> dict:
    """Opposed attack using a bestiary NPC attack profile."""
    disadvantage, advantage, fear_note = _attack_roll_modifiers(
        attacker, profile.get("type", attack_type), attacker_f, defender_f
    )
    a_die = roll_attack_die(disadvantage=disadvantage, advantage=advantage)
    d_die = roll_d20()

    atk_type = profile.get("type", attack_type)
    attr_field = profile.get("attr", "str" if atk_type in ("bite", "kick", "gore") else "dex")
    if attr_field == "str":
        a_mod = attr_modifier(attacker["attr_str"])
    elif attr_field == "dex":
        a_mod = attr_modifier(attacker["attr_dex"])
    else:
        a_mod = attr_modifier(attacker.get(f"attr_{attr_field}", attacker["attr_str"]))
    if profile.get("skill"):
        a_mod += _prof_bonus(attacker, profile["skill"])
    a_mod += profile.get("hit_bonus", 0)
    a_mod += trait_combat_modifier(attacker)
    d_mod = attr_modifier(defender["attr_dex"])
    attack_name = profile.get("name", "Attack")

    a_total = a_die + a_mod
    d_total = d_die + d_mod

    if a_die == 20 and d_die != 20:
        hit, crit, fumble = True, True, False
    elif a_die == 1:
        hit, crit, fumble = False, False, True
    elif d_die == 20 and a_die != 20:
        hit, crit, fumble = False, False, False
    elif d_die == 1:
        hit, crit, fumble = True, False, False
    else:
        hit = a_total >= d_total
        crit = a_die == 20
        fumble = a_die == 1

    damage = 0
    extra = ""
    crit_effect = None
    fumble_effect = None
    fumble_self_damage = 0
    if hit:
        damage = random.randint(1, profile["die"]) + profile.get("flat_damage", 0)
        if crit:
            damage, crit_effect, extra = _apply_crit_to_damage(damage)
        if profile.get("on_hit"):
            extra = (extra + " " + profile["on_hit"]).strip()
    elif fumble:
        fumble_effect, extra, fumble_self_damage = _roll_fumble()

    if fear_note:
        extra = (extra + " " + fear_note).strip() if extra else fear_note.strip("_")

    if hit:
        damage, extra = _apply_defender_damage_reduction(defender, damage, extra)

    result = _attack_result_base(attack_name)
    result.update(
        {
            "hit": hit,
            "crit": crit,
            "fumble": fumble,
            "attacker_roll": a_die,
            "attacker_mod": a_mod,
            "attacker_total": a_total,
            "defender_roll": d_die,
            "defender_mod": d_mod,
            "defender_total": d_total,
            "damage": max(0, damage),
            "extra": extra,
            "crit_effect": crit_effect,
            "fumble_effect": fumble_effect,
            "fumble_self_damage": fumble_self_damage,
        }
    )
    return result


def resolve_attack(
    attacker,
    defender,
    attack_type: str,
    *,
    attacker_f=None,
    defender_f=None,
) -> dict:
    """attack_type: bite | claw"""
    if attack_type == "bite" and bite_attack_blocked(attacker):
        result = _attack_result_base("Bite")
        result["blocked"] = True
        result["block_reason"] = (
            "**Broken Jaw**; you cannot bite. Use claw attacks or treat the jaw first."
        )
        return result

    attacker = _combat_stats(attacker)
    defender = _combat_stats(defender)

    profile = attacker.get("npc_attack_profile")
    if profile:
        return _resolve_attack_profile(
            attacker, defender, attack_type, profile,
            attacker_f=attacker_f, defender_f=defender_f,
        )

    disadvantage, advantage, fear_note = _attack_roll_modifiers(
        attacker, attack_type, attacker_f, defender_f
    )
    a_die = roll_attack_die(disadvantage=disadvantage, advantage=advantage)
    d_die = roll_d20()

    damage_mod, _ = attack_roll_modifiers(attacker, attack_type)

    if attack_type == "bite":
        a_mod = attr_modifier(attacker["attr_str"]) + _prof_bonus(attacker, "hunting")
        d_mod = attr_modifier(defender["attr_dex"])
        damage_die = 6
        str_mod = attr_modifier(attacker["attr_str"])
        attack_name = "Bite"
    else:
        a_mod = attr_modifier(attacker["attr_dex"])
        d_mod = attr_modifier(defender["attr_dex"])
        damage_die = 4
        str_mod = attr_modifier(attacker["attr_dex"])
        attack_name = "Claw"

    a_mod += trait_combat_modifier(attacker)

    plot_dmg_bonus = 0
    plot_combat_note = ""
    if attacker_f:
        from engine.collab_combat import collab_assist_bonus

        a_mod += collab_assist_bonus(attacker_f["encounter_id"], attacker_f["id"])

        from engine.plot_blinking import plot_combat_bonus

        _p_atk, plot_dmg_bonus, plot_combat_note = plot_combat_bonus(attacker, attacker_f, attack_type)
        a_mod += _p_atk

    a_total = a_die + a_mod
    d_total = d_die + d_mod

    # Nat 20 / 1 overrides
    if a_die == 20 and d_die != 20:
        hit = True
        crit = True
        fumble = False
    elif a_die == 1:
        hit = False
        crit = False
        fumble = True
    elif d_die == 20 and a_die != 20:
        hit = False
        crit = False
        fumble = False
    elif d_die == 1:
        hit = True
        crit = False
        fumble = False
    else:
        hit = a_total >= d_total
        crit = a_die == 20
        fumble = a_die == 1

    damage = 0
    extra = ""
    crit_effect = None
    fumble_effect = None
    fumble_self_damage = 0
    if hit:
        damage = random.randint(1, damage_die) + max(0, str_mod) + damage_mod
        if attacker_f is not None and defender_f is not None:
            from engine.combat_status import parse_combat_flags
            from engine.role_features import hunter_bonus_damage

            d_flags = parse_combat_flags(defender_f)
            hunter_extra = hunter_bonus_damage(
                attacker,
                target_prone=bool(d_flags.get("prone") or d_flags.get("pinned")),
            )
            if hunter_extra:
                damage += hunter_extra
                extra = (extra + " " if extra else "") + f"_killer's instinct: +{hunter_extra}._"
        if plot_dmg_bonus:
            damage += plot_dmg_bonus
        if crit:
            damage, crit_effect, extra = _apply_crit_to_damage(damage)
    elif fumble:
        fumble_effect, extra, fumble_self_damage = _roll_fumble()

    if hit:
        damage, extra = _apply_defender_damage_reduction(defender, damage, extra)

    if fear_note:
        extra = (extra + " " + fear_note).strip() if extra else fear_note.strip("_")

    if plot_combat_note and plot_combat_note not in (extra or ""):
        extra = (extra + " " + f"_{plot_combat_note}_").strip() if extra else f"_{plot_combat_note}_"

    result = _attack_result_base(attack_name)
    result.update(
        {
            "hit": hit,
            "crit": crit,
            "fumble": fumble,
            "attacker_roll": a_die,
            "attacker_mod": a_mod,
            "attacker_total": a_total,
            "defender_roll": d_die,
            "defender_mod": d_mod,
            "defender_total": d_total,
            "damage": max(0, damage),
            "extra": extra,
            "crit_effect": crit_effect,
            "fumble_effect": fumble_effect,
            "fumble_self_damage": fumble_self_damage,
        }
    )
    return result


def resolve_maneuver(
    attacker,
    defender,
    maneuver_key: str,
    *,
    attacker_f=None,
    defender_f=None,
) -> dict:
    """Resolve a special combat maneuver from combat_guide.COMBAT_MANEUVERS."""
    spec = COMBAT_MANEUVERS.get(maneuver_key)
    if not spec:
        raise ValueError("unknown_maneuver")

    attacker = _combat_stats(attacker)
    defender = _combat_stats(defender)
    defender_max = int(defender.get("max_hp") or defender.get("hp") or 1)
    defender_hp = int(defender.get("hp", defender_max))

    pin_block = None
    if attacker_f and defender_f:
        pin_block = maneuver_pin_block(
            spec,
            attacker_f,
            defender_f,
            defender_hp=defender_hp,
            defender_max_hp=defender_max,
            attacker_stats=attacker,
            defender_stats=defender,
        )
    if pin_block:
        return {
            "attack_name": spec["name"],
            "hit": False,
            "crit": False,
            "fumble": False,
            "blocked": True,
            "block_reason": pin_block,
            "attacker_roll": 0,
            "attacker_mod": 0,
            "attacker_total": 0,
            "defender_roll": 0,
            "defender_mod": 0,
            "defender_total": 0,
            "damage": 0,
            "extra": "",
        }

    disadvantage, advantage, _ = _attack_roll_modifiers(
        attacker, "claw", attacker_f, defender_f
    )
    a_die = roll_attack_die(disadvantage=disadvantage, advantage=advantage)
    d_die = roll_d20()

    attr_key = spec.get("attr", "str")
    attr_field = {
        "str": "attr_str",
        "dex": "attr_dex",
        "wis": "attr_wis",
        "cha": "attr_cha",
    }.get(attr_key, "attr_str")
    a_mod = attr_modifier(attacker[attr_field]) + spec.get("attack_bonus", 0)
    if spec.get("prof_skill"):
        a_mod += _prof_bonus(attacker, spec["prof_skill"])
    a_mod += trait_combat_modifier(attacker)
    if attacker_f:
        from engine.collab_combat import collab_assist_bonus

        a_mod += collab_assist_bonus(attacker_f["encounter_id"], attacker_f["id"])
    d_mod = attr_modifier(defender["attr_dex"]) + spec.get("defense_bonus", 0)

    a_total = a_die + a_mod
    d_total = d_die + d_mod

    if a_die == 20 and d_die != 20:
        hit = True
        crit = True
        fumble = False
    elif a_die == 1:
        hit = False
        crit = False
        fumble = True
    elif d_die == 20 and a_die != 20:
        hit = False
        crit = False
        fumble = False
    elif d_die == 1:
        hit = True
        crit = False
        fumble = False
    else:
        hit = a_total >= d_total
        crit = a_die == 20
        fumble = a_die == 1

    damage_die = spec.get("damage_die", 4)
    damage_mod = attr_modifier(attacker[attr_field])
    damage = 0
    extra = ""
    crit_effect = None
    fumble_effect = None
    fumble_self_damage = 0
    if hit and damage_die > 0:
        damage = random.randint(1, damage_die) + max(0, damage_mod)
        if crit:
            damage, crit_effect, extra = _apply_crit_to_damage(damage)
        if spec.get("vulnerable"):
            extra = (extra + "; vulnerable-area strike.").strip(" -")
        if spec.get("lethal"):
            extra = (extra + " **Lethal technique.**").strip()
    elif fumble:
        fumble_effect, extra, fumble_self_damage = _roll_fumble()
    elif spec.get("defense_bonus"):
        extra = "Defensive maneuver; you hold your ground."

    if hit and damage > 0:
        damage, extra = _apply_defender_damage_reduction(defender, damage, extra)

    result = _attack_result_base(spec["name"])
    result.update(
        {
            "hit": hit,
            "crit": crit,
            "fumble": fumble,
            "blocked": False,
            "block_reason": "",
            "attacker_roll": a_die,
            "attacker_mod": a_mod,
            "attacker_total": a_total,
            "defender_roll": d_die,
            "defender_mod": d_mod,
            "defender_total": d_total,
            "damage": max(0, damage),
            "extra": extra,
            "crit_effect": crit_effect,
            "fumble_effect": fumble_effect,
            "fumble_self_damage": fumble_self_damage,
        }
    )
    return result


def format_attack(result: dict, attacker_name: str, defender_name: str) -> str:
    if result.get("blocked"):
        return result["block_reason"]
    lines = [
        f"**{result['attack_name']}**; {attacker_name} vs {defender_name}",
        (
            f"attack: {result['attacker_roll']} + {result['attacker_mod']} = "
            f"**{result['attacker_total']}** vs "
            f"defense: {result['defender_roll']} + {result['defender_mod']} = "
            f"**{result['defender_total']}**"
        ),
    ]
    if result["hit"]:
        lines.append(f"**hit!** {result['damage']} damage.")
        if result.get("extra"):
            lines.append(result["extra"])
    elif result["fumble"]:
        lines.append(f"**critical fumble!** {result['extra']}")
    else:
        lines.append("**miss.**")
    return "\n".join(lines)


def finalize_cross_pack_pvp_death(
    guild_id: int,
    killer_discord_id: int | None,
    victim_discord_id: int | None,
) -> str | None:
    """
    When a player wolf drops to 0 HP from another player's attack,
    worsen Great Pack standing if killer and victim belong to different dens.
    """
    import database as db
    from config import GREAT_PACKS

    if not killer_discord_id or not victim_discord_id:
        return None
    if killer_discord_id == victim_discord_id:
        return None

    killer = db.get_user(killer_discord_id)
    victim = db.get_user(victim_discord_id)
    if not killer or not victim:
        return None

    k_pack = int(killer["pack_id"]) if killer["pack_id"] else 0
    v_pack = int(victim["pack_id"]) if victim["pack_id"] else 0
    if not k_pack or not v_pack or k_pack == v_pack:
        return None

    k_gp = killer["great_pack"] if "great_pack" in killer.keys() else None
    v_gp = victim["great_pack"] if "great_pack" in victim.keys() else None
    if not k_gp or not v_gp or k_gp == v_gp:
        return None
    if k_gp not in GREAT_PACKS or v_gp not in GREAT_PACKS:
        return None

    from engine.pack_relations import format_standing_war_flash

    new_standing = db.adjust_pack_relation(guild_id, k_pack, v_pack, -3)
    victim_den = db.get_pack(v_pack)
    name = victim_den["name"] if victim_den else GREAT_PACKS[v_gp]["name"]
    note = f"pack standing with **{name}** **−3** (now **{new_standing}/10**)."
    note += format_standing_war_flash(guild_id, k_pack, v_pack, new_standing)
    from engine.battle_fatigue import record_pack_combat_day
    world = db.get_world(guild_id)
    if world:
        record_pack_combat_day(k_pack, world["day_number"])
        record_pack_combat_day(v_pack, world["day_number"])
        debt = db.add_pack_blood_debt(guild_id, k_pack, v_pack, world["day_number"])
        note += f"\n_a life taken; **{debt}** blood debt owed by {db.get_pack(k_pack)['name'] if db.get_pack(k_pack) else 'killer pack'} to {db.get_pack(v_pack)['name'] if db.get_pack(v_pack) else 'victim pack'}; clear it with `/pack tribute`._"
    return note
