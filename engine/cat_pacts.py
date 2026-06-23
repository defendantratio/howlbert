"""Pack-level treaties with forest cat clans."""

from __future__ import annotations

import random

import database as db
from config import (
    CAT_PACT_ALLIANCE_DC,
    CAT_PACT_ALLIANCE_DAYS,
    CAT_PACT_ALLIANCE_TRIBUTE,
    CAT_PACT_ALLIANCE_UNITY,
    CAT_PACT_DIPLOMAT_NEGOTIATE_BONUS,
    CAT_PACT_FORGE_FAIL_COOLDOWN_DAYS,
    CAT_PACT_GIFT_TRIBUTE,
    CAT_PACT_GIFT_TRUST,
    CAT_PACT_HUNTING_DC,
    CAT_PACT_HUNTING_DAYS,
    CAT_PACT_HUNTING_PERSONAL,
    CAT_PACT_HUNTING_TRIBUTE,
    CAT_PACT_MAX_ACTIVE,
    CAT_PACT_PATROL_TEMPLATES,
    CAT_PACT_TRUCE_DC,
    CAT_PACT_TRUCE_DAYS,
    CAT_PACT_TRUCE_TRIBUTE,
    CAT_PACT_TRUCE_UNITY,
    CAT_PACT_TRUST_HIGH,
    CAT_PACT_TRUST_LOW,
    CAT_PACT_VIOLATION_STANDING,
    CAT_PACT_VIOLATION_TRUST,
    CAT_PACT_VIOLATION_UNITY,
)
from engine.cat_clans import KNOWN_CAT_CLANS, pick_rival_clan, validate_clan_name
from engine.character import parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from engine.pack_leadership import can_forge_cat_pact, wolf_role_key

PACT_TYPE_LABELS = {
    "truce": "Border Truce",
    "alliance": "Clan Alliance",
    "hunting_rights": "Hunting Rights",
}

PACT_SPECS = {
    "truce": {
        "days": CAT_PACT_TRUCE_DAYS,
        "treasury": CAT_PACT_TRUCE_TRIBUTE,
        "personal": 0,
        "dc": CAT_PACT_TRUCE_DC,
        "unity": CAT_PACT_TRUCE_UNITY,
        "trust_start": 45,
        "border_mult": 0.20,
    },
    "alliance": {
        "days": CAT_PACT_ALLIANCE_DAYS,
        "treasury": CAT_PACT_ALLIANCE_TRIBUTE,
        "personal": 0,
        "dc": CAT_PACT_ALLIANCE_DC,
        "unity": CAT_PACT_ALLIANCE_UNITY,
        "trust_start": 60,
        "border_mult": 0.08,
    },
    "hunting_rights": {
        "days": CAT_PACT_HUNTING_DAYS,
        "treasury": CAT_PACT_HUNTING_TRIBUTE,
        "personal": CAT_PACT_HUNTING_PERSONAL,
        "dc": CAT_PACT_HUNTING_DC,
        "unity": 0,
        "trust_start": 40,
        "border_mult": 0.35,
    },
}


def pact_border_chance_multiplier(guild_id: int, pack_id: int | None) -> float:
    """Lower = fewer /sniff border cat fights."""
    if not pack_id:
        return 1.0
    pacts = db.list_active_cat_pacts(guild_id, pack_id)
    if not pacts:
        return 1.0
    mult = 1.0
    for pact in pacts:
        spec = PACT_SPECS.get(pact["pact_type"], PACT_SPECS["truce"])
        trust = int(pact["trust"])
        trust_bonus = 0.85 if trust >= CAT_PACT_TRUST_HIGH else (1.0 if trust >= CAT_PACT_TRUST_LOW else 1.15)
        mult *= spec["border_mult"] * trust_bonus
    return max(0.03, min(1.0, mult))


def pick_border_cat_for_pack(
    guild_id: int,
    pack_id: int | None,
) -> tuple[str, str, bool]:
    """
    Pick NPC template, clan name, and whether defeating them risks pact violation.
    Returns (template_key, clan_name, pact_violation_risk).
    """
    from engine.border_combat import pick_border_cat_template

    if not pack_id:
        clan = random.choice(KNOWN_CAT_CLANS)
        return pick_border_cat_template(), clan, False

    pacts = db.list_active_cat_pacts(guild_id, pack_id)
    if not pacts:
        clan = random.choice(KNOWN_CAT_CLANS)
        return pick_border_cat_template(), clan, False

    primary = max(pacts, key=lambda p: int(p["trust"]))
    trust = int(primary["trust"])
    allied = primary["clan_name"]

    if trust < CAT_PACT_TRUST_LOW:
        template = random.choice(["clan_warrior", "clan_deputy"])
        return template, allied, True

    if random.random() < 0.72:
        template = random.choice(["rogue_cat", "loner_cat", "kittypet"])
        return template, pick_rival_clan(allied), False

    template = pick_border_cat_template()
    if template in CAT_PACT_PATROL_TEMPLATES:
        return template, pick_rival_clan(allied), False
    return template, pick_rival_clan(allied), False


def format_pact_line(pact) -> str:
    label = PACT_TYPE_LABELS.get(pact["pact_type"], pact["pact_type"].title())
    trust = int(pact["trust"])
    days_left = max(0, int(pact["expires_day"]) - int(pact.get("current_day", pact["expires_day"])))
    tier = "steady" if trust >= CAT_PACT_TRUST_HIGH else ("strained" if trust < CAT_PACT_TRUST_LOW else "holding")
    note = f"; _{pact['terms_note']}_" if pact["terms_note"] else ""
    return (
        f"**{pact['clan_name']}**; {label} · trust **{trust}** ({tier}) · "
        f"**{days_left}** sunrises left{note}"
    )


def format_pacts_body(guild_id: int, pack_id: int, *, day: int) -> str:
    pacts = db.list_active_cat_pacts(guild_id, pack_id)
    if not pacts:
        return (
            "No cat pacts on the scent-line.\n\n"
            "**`/pack pact action:Forge`**; Alpha or **Diplomat** negotiates a truce, alliance, "
            "or seasonal hunting rights (tribute from treasury).\n"
            "Loners cannot forge den treaties; join a Great Pack first."
        )
    lines = []
    for pact in pacts:
        row = dict(pact)
        row["current_day"] = day
        lines.append(format_pact_line(row))
    lines.append(
        "\n_Breaking a pact or blood on an allied patrol shatters trust. "
        "Rogues and rival-clan cats do not count as violations._"
    )
    return "\n".join(lines)


def _negotiate_check(user, dc: int, *, game_day: int | None = None) -> dict:
    profs = parse_proficiencies(user["skill_proficiencies"])
    bonus = CAT_PACT_DIPLOMAT_NEGOTIATE_BONUS if wolf_role_key(user) == "diplomat" else 0
    result = resolve_check(
        user,
        attr_keys=("attr_cha", "attr_wis"),
        skill="persuasion",
        dc=dc + bonus,
        proficient="persuasion" in profs,
        skill_key="persuasion",
        game_day=game_day,
    )
    if bonus:
        result["diplomat_dc_ease"] = bonus
    return result


def forge_cat_pact(
    user,
    pack,
    *,
    guild_id: int,
    clan_name: str,
    pact_type: str,
    terms_note: str,
    day: int,
) -> tuple[bool, str]:
    if not can_forge_cat_pact(user, pack):
        return False, "Only the **Alpha** or a **Diplomat** can negotiate with forest cats."

    clan, err = validate_clan_name(clan_name)
    if err:
        return False, err

    if pact_type not in PACT_SPECS:
        return False, "Pick **truce**, **alliance**, or **hunting_rights**."

    if db.count_active_cat_pacts(pack["id"]) >= CAT_PACT_MAX_ACTIVE:
        return False, (
            f"This den already holds **{CAT_PACT_MAX_ACTIVE}** active cat treaties. "
            "Break or let one expire before forging another."
        )

    existing = db.get_cat_pact(pack["id"], clan)
    if existing and existing["status"] == "active":
        return False, f"An active pact with **{clan}** already stands. Renew or break it first."

    if existing and existing["status"] == "broken":
        cooled = int(existing["broken_day"] or 0) + CAT_PACT_FORGE_FAIL_COOLDOWN_DAYS
        if day < cooled:
            return False, (
                f"**{clan}** still remembers the broken oath; wait **{cooled - day}** more sunrise(s)."
            )

    last_fail = db.get_pack_cat_pact_fail_day(pack["id"], clan)
    if last_fail and day < last_fail + CAT_PACT_FORGE_FAIL_COOLDOWN_DAYS:
        return False, "The cats won't parley again so soon after a refused offer."

    spec = PACT_SPECS[pact_type]
    treasury_cost = spec["treasury"]
    personal_cost = spec["personal"]

    if treasury_cost and not db.deduct_pack_treasury(pack["id"], treasury_cost):
        return False, (
            f"Treasury needs **{treasury_cost}** bones for the tribute gift "
            f"({PACT_TYPE_LABELS[pact_type]})."
        )

    if personal_cost:
        if int(user["bones"]) < personal_cost:
            if treasury_cost:
                db.add_pack_treasury(pack["id"], treasury_cost)
            return False, f"You need **{personal_cost}** bones for the personal scent-gift."
        db.add_bones(user["discord_id"], -personal_cost)

    dc = spec["dc"]
    if int(pack["pack_unity"]) < 0:
        dc += 2

    result = _negotiate_check(user, dc, game_day=day)
    if not result["success"]:
        db.set_pack_cat_pact_fail_day(pack["id"], clan, day)
        tribute_note = (
            f"The cats keep the **{treasury_cost + personal_cost}** bone tribute and leave.\n\n"
            if (treasury_cost or personal_cost)
            else ""
        )
        return False, tribute_note + format_roll_result(result)

    trust = spec["trust_start"]
    if result["outcome"] == "critical_success":
        trust = min(100, trust + 15)
    expires = day + spec["days"]
    db.upsert_cat_pact(
        guild_id,
        pack["id"],
        clan,
        pact_type=pact_type,
        trust=trust,
        tribute_paid=treasury_cost + personal_cost,
        terms_note=(terms_note or "")[:120],
        forged_day=day,
        expires_day=expires,
        forged_by_discord_id=user["discord_id"],
    )
    if spec["unity"]:
        db.adjust_pack_unity(pack["id"], spec["unity"])

    body = (
        f"**{pack['name']}** and **{clan}** mark a **{PACT_TYPE_LABELS[pact_type]}** "
        f"on the border stones.\n"
        f"Tribute accepted · trust **{trust}** · holds until sunrise **{expires}**.\n\n"
        f"{format_roll_result(result)}"
    )
    if terms_note:
        body += f"\n\n_Terms: {terms_note.strip()}_"
    return True, body


def renew_cat_pact(user, pack, *, guild_id: int, clan_name: str, day: int) -> tuple[bool, str]:
    if not can_forge_cat_pact(user, pack):
        return False, "Only the **Alpha** or **Diplomat** can renew a cat treaty."

    clan, err = validate_clan_name(clan_name)
    if err:
        return False, err

    pact = db.get_cat_pact(pack["id"], clan)
    if not pact or pact["status"] != "active":
        return False, f"No active pact with **{clan}**."

    spec = PACT_SPECS.get(pact["pact_type"], PACT_SPECS["truce"])
    if int(pact["trust"]) < CAT_PACT_TRUST_LOW:
        return False, "Trust is too low; the cats won't extend the treaty. Forge anew after it expires."

    half_tribute = max(10, spec["treasury"] // 2)
    if not db.deduct_pack_treasury(pack["id"], half_tribute):
        return False, f"Renewal tribute: **{half_tribute}** bones from treasury."

    dc = spec["dc"] - 2
    result = _negotiate_check(user, dc, game_day=day)
    if not result["success"]:
        db.add_pack_treasury(pack["id"], half_tribute)
        return False, f"The delegation is turned away.\n\n{format_roll_result(result)}"

    new_expires = day + spec["days"]
    new_trust = min(100, int(pact["trust"]) + 10)
    db.renew_cat_pact(pack["id"], clan, expires_day=new_expires, trust=new_trust, day=day)
    return True, (
        f"**{clan}** agrees to extend the **{PACT_TYPE_LABELS[pact['pact_type']]}**.\n"
        f"Trust **{new_trust}** · new expiry sunrise **{new_expires}**.\n\n"
        f"{format_roll_result(result)}"
    )


def break_cat_pact(
    user,
    pack,
    *,
    clan_name: str,
    day: int,
    reason: str = "Den withdrew from the treaty.",
) -> tuple[bool, str]:
    if not can_forge_cat_pact(user, pack):
        return False, "Only the **Alpha** or **Diplomat** can break a cat treaty."

    clan, err = validate_clan_name(clan_name)
    if err:
        return False, err

    pact = db.get_cat_pact(pack["id"], clan)
    if not pact or pact["status"] != "active":
        return False, f"No active pact with **{clan}**."

    db.break_cat_pact(pack["id"], clan, day=day, reason=reason)
    db.adjust_pack_unity(pack["id"], -2)
    return True, (
        f"**{pack['name']}** breaks the treaty with **{clan}**.\n"
        f"_{reason}_\nDen unity **−2**. Border patrols will remember."
    )


def gift_cat_pact(user, pack, *, clan_name: str, day: int) -> tuple[bool, str]:
    if not can_forge_cat_pact(user, pack):
        return False, "Only the **Alpha** or **Diplomat** can send tribute."

    clan, err = validate_clan_name(clan_name)
    if err:
        return False, err

    pact = db.get_cat_pact(pack["id"], clan)
    if not pact or pact["status"] != "active":
        return False, f"No active pact with **{clan}**."

    if db.cat_pact_gift_used_today(pack["id"], day):
        return False, "Tribute was already sent this sunrise."

    if not db.deduct_pack_treasury(pack["id"], CAT_PACT_GIFT_TRIBUTE):
        return False, f"Treasury needs **{CAT_PACT_GIFT_TRIBUTE}** bones for the gift."

    new_trust = min(100, int(pact["trust"]) + CAT_PACT_GIFT_TRUST)
    db.adjust_cat_pact_trust(pack["id"], clan, CAT_PACT_GIFT_TRUST)
    db.mark_cat_pact_gift_day(pack["id"], day)
    return True, (
        f"Prey bones and herbs left at the border for **{clan}**.\n"
        f"Trust **{int(pact['trust'])} → {new_trust}**."
    )


def handle_border_pact_violation(
    user,
    *,
    guild_id: int,
    enc,
    cat_template: str | None,
) -> str | None:
    """Apply consequences when an allied patrol is downed. Returns embed addendum."""
    if not user or not user["pack_id"]:
        return None
    if not enc or not enc["is_border_fight"]:
        return None

    clan = enc["border_cat_clan"] if "border_cat_clan" in enc.keys() else ""
    if not clan:
        return None

    violation = bool(enc["border_pact_violation"] if "border_pact_violation" in enc.keys() else False)
    if not violation and cat_template not in CAT_PACT_PATROL_TEMPLATES:
        return None

    pact = db.get_cat_pact(user["pack_id"], clan)
    if not pact or pact["status"] != "active":
        return None

    if violation or cat_template in CAT_PACT_PATROL_TEMPLATES:
        if cat_template in CAT_PACT_PATROL_TEMPLATES and pact["clan_name"].casefold() == clan.casefold():
            new_trust = max(0, int(pact["trust"]) + CAT_PACT_VIOLATION_TRUST)
            db.adjust_cat_pact_trust(user["pack_id"], clan, CAT_PACT_VIOLATION_TRUST)
            db.adjust_pack_unity(user["pack_id"], CAT_PACT_VIOLATION_UNITY)
            db.adjust_wolf_standing(user["discord_id"], CAT_PACT_VIOLATION_STANDING)
            if new_trust <= 0:
                db.break_cat_pact(
                    user["pack_id"],
                    clan,
                    day=db.get_world(guild_id)["day_number"],
                    reason="Patrol blood on the border; the treaty is ash.",
                )
                return (
                    f"\n\n**Treaty shattered**; **{clan}** will not forgive this patrol kill. "
                    f"Trust collapsed · den unity **{CAT_PACT_VIOLATION_UNITY}** · "
                    f"standing **{CAT_PACT_VIOLATION_STANDING}**."
                )
            return (
                f"\n\n**Trust broken** with **{clan}** (**{new_trust}** trust). "
                f"Another incident ends the pact."
            )
    return None
