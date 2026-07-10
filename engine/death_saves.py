
from engine.character import attr_modifier
from engine.dice import roll_d20
DEATH_SAVE_DCS = (10, 12, 15)


def roll_death_save(user) -> dict:
    """Round 1 to 3: CON save vs escalating DC. Three successes → stabilize at 1 HP."""
    round_num = user["death_save_round"] if user["death_save_round"] else 1
    round_num = min(3, max(1, round_num))
    dc = DEATH_SAVE_DCS[round_num - 1]

    die = roll_d20()
    mod = attr_modifier(user["attr_con"])
    from engine.herb_buffs import consume_death_save_bonus, death_save_bonus

    herb_bonus = death_save_bonus(user)
    mod += herb_bonus
    total = die + mod

    if die == 1:
        success = False
        auto_fail = True
    elif die == 20:
        success = True
        auto_fail = False
    else:
        success = total >= dc
        auto_fail = False

    consume_fields = consume_death_save_bonus(user) if herb_bonus else {}

    return {
        "die": die,
        "modifier": mod,
        "total": total,
        "dc": dc,
        "round": round_num,
        "success": success,
        "auto_fail": auto_fail,
        "nat20": die == 20,
        "consume_fields": consume_fields,
    }


def stabilize_bonus(
    *,
    yarrow: bool = False,
    yarrow_fresh: bool = False,
    oak_bark: bool = False,
    cattail: bool = False,
) -> int:
    bonus = 0
    if yarrow or yarrow_fresh:
        bonus += 2
    if oak_bark:
        bonus += 2
    if cattail:
        bonus += 2
    return bonus


def stabilize_check(
    healer,
    target_has_herblore: bool = False,
    *,
    yarrow: bool = False,
    yarrow_fresh: bool = False,
    oak_bark: bool = False,
    cattail: bool = False,
    patient=None,
) -> dict:
    die = roll_d20()
    mod = attr_modifier(healer["attr_wis"])
    from engine.character_traits import trait_check_adjustments

    trait_mod, _ = trait_check_adjustments(
        healer, ("attr_wis",), skill_key="medicine", skill_label="Medicine"
    )
    mod += stabilize_bonus(
        yarrow=yarrow,
        yarrow_fresh=yarrow_fresh,
        oak_bark=oak_bark,
        cattail=cattail,
    )
    from engine.herb_buffs import consume_death_save_bonus, death_save_bonus

    bonus_target = patient or healer
    herb_bonus = death_save_bonus(bonus_target)
    mod += herb_bonus
    total = die + mod + trait_mod
    dc = 15
    consume_fields = consume_death_save_bonus(bonus_target) if herb_bonus else {}
    return {
        "die": die,
        "modifier": mod,
        "proficiency": trait_mod,
        "total": total,
        "dc": dc,
        "success": total >= dc or die == 20,
        "consume_fields": consume_fields,
    }
