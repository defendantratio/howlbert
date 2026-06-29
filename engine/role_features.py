"""Mechanical hooks for ROLE_FEATURES and bonus_role_feature purchases."""

from __future__ import annotations

import database as db
from config import ROGUE_KEY
from rpg_rules import ROLE_FEATURES, SKILLS

DROWN_SICK_ROLE = "drown_sick"
MISTMOOR_KEY = "mistmoor"

STEALTH_ADVANTAGE_ROLES = frozenset({"scout", "rogue", "lowbelly"})
BOG_BORN_ROLES = frozenset({"bog_born"})
PERCEPTION_BONUS_ROLES = frozenset({DROWN_SICK_ROLE})
CHARISMA_REROLL_ROLES = frozenset({"diplomat", "elder"})
CHARISMA_SKILL_KEYS = frozenset(
    key for key, (attrs, _) in SKILLS.items() if "attr_cha" in attrs
)
LIGHTLY_OBSCURED_WEATHER = frozenset(
    {"thick_fog", "fog", "mist", "freezing_fog", "light_fog"}
)


def wolf_role_key(user) -> str:
    if not user:
        return "hunter"
    return user["wolf_role"] if "wolf_role" in user.keys() else "hunter"


def role_keys(user) -> tuple[str, ...]:
    """active wolf role plus optional purchased bonus feature."""
    if not user:
        return ()
    keys: list[str] = []
    primary = wolf_role_key(user)
    if primary:
        keys.append(primary)
    if "bonus_role_feature" in user.keys() and user["bonus_role_feature"]:
        bonus = str(user["bonus_role_feature"])
        if bonus in ROLE_FEATURES and bonus not in keys:
            keys.append(bonus)
    return tuple(keys)


def has_any_role(user, *roles: str) -> bool:
    return bool(set(role_keys(user)) & set(roles))


def is_rogue_wolf(user) -> bool:
    if not user:
        return False
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    return has_any_role(user, "rogue") or gp == ROGUE_KEY


def is_full_medic(user) -> bool:
    return has_any_role(user, "medic")


def is_caretaker(user) -> bool:
    return has_any_role(user, "caretaker")


def role_check_adjustments(
    user,
    attr_keys: tuple[str, ...],
    *,
    skill_key: str | None = None,
    great_pack: str | None = None,
    weather_key: str | None = None,
) -> tuple[int, bool, bool]:
    """
    Role-based check modifiers.
    Returns (flat_modifier, advantage, extra_disadvantage).
    """
    if not user:
        return 0, False, False

    mod = 0
    advantage = False
    disadvantage = False
    pack = great_pack
    if pack is None and "great_pack" in user.keys():
        pack = user["great_pack"]

    if has_any_role(user, *PERCEPTION_BONUS_ROLES):
        in_fog_swamp = weather_is_lightly_obscured(weather_key) or pack == MISTMOOR_KEY
        if in_fog_swamp and skill_key in ("tracking", "stealth"):
            mod += 2
        elif in_fog_swamp and "attr_wis" in attr_keys:
            mod += 2

    if has_any_role(user, *BOG_BORN_ROLES) and pack == MISTMOOR_KEY:
        if skill_key in ("herblore", "survival") or "attr_con" in attr_keys:
            advantage = True

    if has_any_role(user, *STEALTH_ADVANTAGE_ROLES) and skill_key == "stealth":
        advantage = True

    if has_any_role(user, DROWN_SICK_ROLE) and skill_key in ("hunting", "intimidation"):
        disadvantage = True

    return mod, advantage, disadvantage


def role_hunt_multiplier(user, *, day: int | None = None) -> tuple[float, str]:
    """Hunt bone multiplier from role frailty."""
    from engine.herb_buffs import elder_hunt_speed_active

    ragwort = elder_hunt_speed_active(user, day)
    if has_any_role(user, DROWN_SICK_ROLE):
        if ragwort:
            return 1.0, "ragwort tonic; full hunt speed despite frailty."
        return 0.65, "drown-sick; frail; −35% hunt bones."
    if ragwort and has_any_role(user, "elder"):
        return 1.0, "ragwort tonic; elders hunt at full speed."
    return 1.0, ""


def hunter_bonus_damage(user, *, target_prone: bool = False, target_surprised: bool = False) -> int:
    if not has_any_role(user, "hunter"):
        return 0
    if target_prone or target_surprised:
        import random

        return random.randint(1, 6)
    return 0


def can_use_role_reroll(user, day: int) -> bool:
    if not has_any_role(user, *CHARISMA_REROLL_ROLES):
        return False
    used = int(user["last_role_reroll_day"]) if "last_role_reroll_day" in user.keys() else 0
    return used < day


def charisma_reroll_roles(user) -> tuple[str, ...]:
    return tuple(r for r in role_keys(user) if r in CHARISMA_REROLL_ROLES)


def bonus_feature_label(user) -> str | None:
    if not user or "bonus_role_feature" not in user.keys() or not user["bonus_role_feature"]:
        return None
    key = str(user["bonus_role_feature"])
    return ROLE_FEATURES.get(key)


def grant_commanding_howl_buffs(pack_id: int, *, exclude_wolf_id: int | None = None) -> int:
    """Alpha's howl; packmates gain advantage on their next skill check."""
    count = 0
    for member in db.get_pack_members(pack_id):
        if exclude_wolf_id and member["id"] == exclude_wolf_id:
            continue
        db.update_user(
            member["discord_id"],
            wolf_id=member["id"],
            commanding_howl_buff=1,
        )
        count += 1
    return count


def try_consume_commanding_howl_buff(user) -> bool:
    if not user or "commanding_howl_buff" not in user.keys():
        return False
    if not int(user["commanding_howl_buff"]):
        return False
    db.update_user(user["discord_id"], wolf_id=user["id"], commanding_howl_buff=0)
    return True


def try_consume_blood_oath_buff(
    user,
    attr_keys: tuple[str, ...],
    *,
    skill_key: str | None = None,
    game_day: int | None = None,
) -> bool:
    """Advisor; advantage on one Charisma check per sunrise."""
    if game_day is None or not has_any_role(user, "advisor"):
        return False
    charisma_check = "attr_cha" in attr_keys or (
        skill_key is not None and skill_key in CHARISMA_SKILL_KEYS
    )
    if not charisma_check:
        return False
    used = int(user["last_blood_oath_day"]) if "last_blood_oath_day" in user.keys() else 0
    if used >= game_day:
        return False
    db.update_user(user["discord_id"], wolf_id=user["id"], last_blood_oath_day=game_day)
    return True


def try_consume_commanding_howl_combat_buff(user) -> bool:
    """same buff applies to the wolf's next attack roll in combat."""
    return try_consume_commanding_howl_buff(user)


def guard_imposes_attack_disadvantage(
    encounter_id: int,
    attacker_fighter_id: int,
    defender_fighter_id: int,
) -> bool:
    """guard; impose disadvantage when a packmate is attacked."""
    for fighter in db.get_combat_fighters(encounter_id):
        fid = fighter["id"]
        if fid in (attacker_fighter_id, defender_fighter_id):
            continue
        user = db.get_user(fighter["discord_id"])
        if user and has_any_role(user, "guard"):
            return True
    return False


def mark_scout_hidden(user, day: int) -> None:
    """scout unseen paw; hidden until end of sunrise in fog/mist."""
    if not has_any_role(user, "scout"):
        return
    db.update_user(user["discord_id"], wolf_id=user["id"], scout_hidden_day=day)


def scout_is_hidden(user, day: int) -> bool:
    if not user or not has_any_role(user, "scout"):
        return False
    hidden = int(user["scout_hidden_day"]) if "scout_hidden_day" in user.keys() else 0
    return hidden >= day


def weather_is_lightly_obscured(weather_key: str | None) -> bool:
    if not weather_key:
        return False
    return weather_key.lower() in LIGHTLY_OBSCURED_WEATHER


def try_scout_hide_in_weather(user, *, weather_key: str | None, day: int) -> str | None:
    if not has_any_role(user, "scout"):
        return None
    if not weather_is_lightly_obscured(weather_key):
        return None
    mark_scout_hidden(user, day)
    return "unseen paw; you melt into the **fog** until this sunrise ends."


def caretaker_groom_mood_bonus(partner_mood: int, *, partner_distressed: bool = False) -> tuple[int, str]:
    """extra mood when a caretaker soothes a frightened wolf."""
    if partner_mood >= 30 and not partner_distressed:
        return 5, ""
    return 12, "\n_soothing lick; fear and panic ease under a caretaker's tongue._"


def can_grant_commanding_howl(user, pack) -> bool:
    """Pack Alpha or any wolf with the Alpha role feature."""
    from engine.pack_leadership import is_pack_alpha

    return is_pack_alpha(user, pack) or has_any_role(user, "alpha")


def scout_hide_after_check(
    user,
    *,
    weather_key: str | None,
    day: int,
    skill_key: str | None,
    success: bool,
) -> str:
    """Scout Unseen Paw after a successful Stealth check in obscured weather."""
    if not success or skill_key != "stealth":
        return ""
    note = try_scout_hide_in_weather(user, weather_key=weather_key, day=day)
    return f"\n\n_{note}_" if note else ""


def apply_scout_combat_hidden(
    user,
    fighter_id: int,
    *,
    day: int,
    weather_key: str | None,
) -> bool:
    """Mark a scout fighter hidden when obscured weather or Unseen Paw is active."""
    if not has_any_role(user, "scout"):
        return False
    hidden = scout_is_hidden(user, day) or weather_is_lightly_obscured(weather_key)
    if not hidden:
        return False
    db.update_fighter_combat_flags(fighter_id, obscured=True)
    return True
