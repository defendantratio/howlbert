"""Rival Great Pack standing actions; diplomatic howl, share, aid."""

from __future__ import annotations

import random

import database as db
from config import GREAT_PACKS
from engine.character import parse_proficiencies
from engine.pack_relations import can_aid_rival, can_share_territory
from engine.dice import format_roll_result, resolve_check
from engine.skill_runner import run_skill_scenario

DIPLOMATIC_HOWL_SUCCESS = (
    "Your howl carries clear intent; **{pack}** answers with lowered hackles.",
    "**{pack}** catches the tone; parley, not challenge, rides the ridge.",
    "A long, measured howl; **{pack}**'s scouts read respect on the wind.",
)

DIPLOMATIC_HOWL_FAIL = (
    "Your voice cracks; **{pack}** hears fear, not law.",
    "**{pack}** doesn't answer; the border stays cold.",
    "The howl dies in the pines; **{pack}** won't read it as peace.",
)

SHARE_FLAVORS = (
    "You open a stretch of **{territory}** for **{pack}** to hunt without challenge this sunrise.",
    "**{pack}** may cross your scent-line on **{territory}**; you vouch for them today.",
    "A shared run on **{territory}**; both dens eat from the same ground.",
)

AID_FLAVORS = (
    "**{pack}** is at war; you send scouts and muscle to their fight.",
    "You rally wolves beside **{pack}** while their den bleeds on the border.",
    "Aid for **{pack}**; your pack stands with them against their enemy.",
)


def _resolve_target_pack(target_pack: str):
    key = (target_pack or "").strip().lower()
    if key not in GREAT_PACKS:
        return None, f"Unknown den; pick **{', '.join(GREAT_PACKS[k]['name'] for k in GREAT_PACKS)}**."
    row = db.get_pack_by_key(key)
    if not row:
        return None, "That Great Pack isn't seeded in this server yet."
    return row, None


def _shared_territory_name(guild_id: int, pack_a_id: int, pack_b_id: int) -> str:
    territories = db.get_territories(guild_id)
    for t in territories:
        owner = t["owner_pack_id"]
        if owner and int(owner) in (pack_a_id, pack_b_id):
            return t["name"]
    if territories:
        return territories[0]["name"]
    return "the border"


def diplomatic_howl(
    user,
    pack,
    *,
    guild_id: int,
    day: int,
    target_pack: str,
    weather: str = "clear",
) -> tuple[bool, str]:
    target, err = _resolve_target_pack(target_pack)
    if err:
        return False, err
    if int(target["id"]) == int(pack["id"]):
        return False, "You can't parley-how at your own den; use `/howl` for unity."

    profs = parse_proficiencies(user["skill_proficiencies"])
    if "howling" in profs:
        ok, body, _ = run_skill_scenario(
            user,
            "howl_warning",
            day=day,
            weather=weather,
        )
    else:
        result = resolve_check(
            user,
            attr_keys=("attr_cha",),
            skill="Intimidation",
            dc=12,
            proficient="intimidation" in profs,
            skill_key="intimidation",
            game_day=day,
            weather_key=weather,
        )
        ok = result["success"]
        body = format_roll_result(result)

    target_name = GREAT_PACKS[target["key"]]["name"] if target["key"] in GREAT_PACKS else target["name"]
    if ok:
        new_standing = db.adjust_pack_relation(guild_id, pack["id"], target["id"], 1)
        flavor = random.choice(DIPLOMATIC_HOWL_SUCCESS).format(pack=target_name)
        return True, f"{body}\n\n{flavor}\n\nStanding **+1** with **{target_name}** (now **{new_standing}/10**)."
    flavor = random.choice(DIPLOMATIC_HOWL_FAIL).format(pack=target_name)
    return False, f"{body}\n\n{flavor}"


def share_territory(
    user,
    pack,
    *,
    guild_id: int,
    day: int,
    target_pack: str,
) -> tuple[bool, str]:
    target, err = _resolve_target_pack(target_pack)
    if err:
        return False, err
    if int(target["id"]) == int(pack["id"]):
        return False, "Share hunting ground with another Great Pack, not your own den."

    ok_rel, rel_err = can_share_territory(guild_id, pack["id"], target["id"])
    if not ok_rel:
        return False, rel_err

    if db.pack_diplomacy_done_today(guild_id, pack["id"], target["id"], "share", day):
        return False, (
            f"You already shared territory with **{target['name']}** this sunrise; "
            "try again after the next rollover."
        )

    terr_name = _shared_territory_name(guild_id, pack["id"], target["id"])
    db.record_pack_diplomacy(guild_id, pack["id"], target["id"], "share", day)
    new_standing = db.adjust_pack_relation(guild_id, pack["id"], target["id"], 1)
    flavor = random.choice(SHARE_FLAVORS).format(territory=terr_name, pack=target["name"])
    return True, f"{flavor}\n\nStanding **+1** with **{target['name']}** (now **{new_standing}/10**)."


def aid_rival_pack(
    user,
    pack,
    *,
    guild_id: int,
    day: int,
    target_pack: str,
) -> tuple[bool, str]:
    target, err = _resolve_target_pack(target_pack)
    if err:
        return False, err
    if int(target["id"]) == int(pack["id"]):
        return False, "Aid another Great Pack at war, not your own den."

    ok_rel, rel_err = can_aid_rival(guild_id, pack["id"], target["id"])
    if not ok_rel:
        return False, rel_err

    war = db.get_active_war_for_pack(guild_id, target["id"])
    if not war:
        return False, f"**{target['name']}** isn't fighting an active territory war right now."

    if db.pack_diplomacy_done_today(guild_id, pack["id"], target["id"], "aid", day):
        return False, (
            f"You already sent aid to **{target['name']}** this sunrise."
        )

    db.record_pack_diplomacy(guild_id, pack["id"], target["id"], "aid", day)
    new_standing = db.adjust_pack_relation(guild_id, pack["id"], target["id"], 2)
    flavor = random.choice(AID_FLAVORS).format(pack=target["name"])
    war_note = f"_They contest **{war['territory_name']}**._"
    return True, (
        f"{flavor}\n{war_note}\n\n"
        f"Standing **+2** with **{target['name']}** (now **{new_standing}/10**)."
    )
