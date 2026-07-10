"""Pack-level treaties with other Great Wolf packs."""

from __future__ import annotations

import random

import database as db
from config import (
    CAT_PACT_ALLIANCE_DAYS,
    CAT_PACT_ALLIANCE_DC,
    CAT_PACT_ALLIANCE_TRIBUTE,
    CAT_PACT_ALLIANCE_UNITY,
    CAT_PACT_FORGE_FAIL_COOLDOWN_DAYS,
    CAT_PACT_HUNTING_DAYS,
    CAT_PACT_HUNTING_DC,
    CAT_PACT_HUNTING_PERSONAL,
    CAT_PACT_HUNTING_TRIBUTE,
    CAT_PACT_MAX_ACTIVE,
    CAT_PACT_TRUCE_DAYS,
    CAT_PACT_TRUCE_DC,
    CAT_PACT_TRUCE_TRIBUTE,
    CAT_PACT_TRUCE_UNITY,
    GREAT_PACKS,
)
from engine.cat_pacts import PACT_TYPE_LABELS, _negotiate_check
from engine.dice import format_roll_result
from engine.pack_leadership import can_forge_cat_pact
from engine.pack_relations import FRIENDLY_STANDING_THRESHOLD, relation_effect_text

WOLF_PACT_SPECS = {
    "truce": {
        "days": CAT_PACT_TRUCE_DAYS,
        "treasury": CAT_PACT_TRUCE_TRIBUTE,
        "personal": 0,
        "dc": CAT_PACT_TRUCE_DC,
        "unity": CAT_PACT_TRUCE_UNITY,
        "standing_floor": 6,
        "standing_gain": 2,
    },
    "alliance": {
        "days": CAT_PACT_ALLIANCE_DAYS,
        "treasury": CAT_PACT_ALLIANCE_TRIBUTE,
        "personal": 0,
        "dc": CAT_PACT_ALLIANCE_DC,
        "unity": CAT_PACT_ALLIANCE_UNITY,
        "standing_floor": FRIENDLY_STANDING_THRESHOLD,
        "standing_gain": 3,
    },
    "hunting_rights": {
        "days": CAT_PACT_HUNTING_DAYS,
        "treasury": CAT_PACT_HUNTING_TRIBUTE,
        "personal": CAT_PACT_HUNTING_PERSONAL,
        "dc": CAT_PACT_HUNTING_DC,
        "unity": 0,
        "standing_floor": 5,
        "standing_gain": 1,
    },
}

WOLF_PACT_MARRIAGE_STANDING_BONUS = 1
WOLF_PACT_MARRIAGE_DAYS_BONUS = 6

WOLF_FORGE_SUCCESS = (
    "**{pack}** answers with lowered hackles; the treaty is carved in scent and law.",
    "parley holds. **{pack}**'s scouts read peace on the border wind.",
    "A measured howl; **{pack}** accepts the terms and marks shared ground.",
)


def resolve_wolf_pack_target(target: str):
    key = (target or "").strip().lower()
    for gp_key, info in GREAT_PACKS.items():
        if key in (gp_key, info["name"].lower()):
            row = db.get_pack_by_key(gp_key)
            if not row:
                return None, "that great pack isn't seeded in this server yet."
            return row, None
    return None, (
        f"unknown den; pick a great pack (**{', '.join(GREAT_PACKS[k]['name'] for k in GREAT_PACKS)}**) "
        "or a forest cat Clan."
    )


def is_wolf_pack_target(target: str) -> bool:
    row, err = resolve_wolf_pack_target(target)
    return row is not None and err is None


def format_wolf_treaty_line(treaty, *, current_day: int) -> str:
    label = PACT_TYPE_LABELS.get(treaty["pact_type"], treaty["pact_type"].title())
    name = treaty["other_pack_name"]
    days_left = max(0, int(treaty["expires_day"]) - int(current_day))
    note = f"; _{treaty['terms_note']}_" if treaty["terms_note"] else ""
    standing = db.get_pack_relation(
        int(treaty["guild_id"]), int(treaty["pack_id"]), int(treaty["other_pack_id"])
    )
    return (
        f"**{name}** (wolf pack); {label} · standing **{standing}/10** · "
        f"**{days_left}** sunrises left{note}"
    )


def format_wolf_treaties_section(guild_id: int, pack_id: int, *, day: int) -> str:
    treaties = db.list_active_wolf_treaties(guild_id, pack_id)
    if not treaties:
        return ""
    lines = ["**wolf pack treaties**"]
    for treaty in treaties:
        row = dict(treaty)
        row["guild_id"] = guild_id
        lines.append(format_wolf_treaty_line(row, current_day=day))
    return "\n".join(lines)


def forge_wolf_pack_pact(
    user,
    pack,
    *,
    guild_id: int,
    target_pack: str,
    pact_type: str,
    terms_note: str,
    day: int,
) -> tuple[bool, str]:
    if not can_forge_cat_pact(user, pack):
        return False, "only the **alpha** or a **diplomat** can negotiate wolf-pack treaties."

    other, err = resolve_wolf_pack_target(target_pack)
    if err:
        return False, err
    if int(other["id"]) == int(pack["id"]):
        return False, "you can't treaty with your own den; pick another great pack."

    if pact_type not in WOLF_PACT_SPECS:
        return False, "pick **truce**, **alliance**, or **hunting_rights**."

    total_active = db.count_active_cat_pacts(pack["id"]) + db.count_active_wolf_treaties(pack["id"])
    if total_active >= CAT_PACT_MAX_ACTIVE:
        return False, (
            f"this den already holds **{CAT_PACT_MAX_ACTIVE}** active treaties (cat or wolf). "
            "Break or let one expire before forging another."
        )

    existing = db.get_wolf_treaty(pack["id"], other["id"])
    if existing and existing["status"] == "active":
        other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
        return False, f"an active treaty with **{other_name}** already stands. renew or break it first."

    if existing and existing["status"] == "broken":
        cooled = int(existing["broken_day"] or 0) + CAT_PACT_FORGE_FAIL_COOLDOWN_DAYS
        if day < cooled:
            other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
            return False, (
                f"**{other_name}** still remembers the broken oath; "
                f"wait **{cooled - day}** more sunrise(s)."
            )

    last_fail = db.get_wolf_pact_fail_day(pack["id"], other["id"])
    if last_fail and day < last_fail + CAT_PACT_FORGE_FAIL_COOLDOWN_DAYS:
        return False, "they won't parley again so soon after a refused offer."

    spec = WOLF_PACT_SPECS[pact_type]
    treasury_cost = spec["treasury"]
    personal_cost = spec["personal"]
    other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])

    if treasury_cost and not db.deduct_pack_treasury(pack["id"], treasury_cost):
        return False, (
            f"treasury needs **{treasury_cost}** bones for the tribute gift "
            f"({PACT_TYPE_LABELS[pact_type]})."
        )

    if personal_cost:
        if int(user["bones"]) < personal_cost:
            if treasury_cost:
                db.add_pack_treasury(pack["id"], treasury_cost)
            return False, f"you need **{personal_cost}** bones for the personal scent-gift."
        db.add_bones(user["discord_id"], -personal_cost)

    dc = spec["dc"]
    if int(pack["pack_unity"]) < 0:
        dc += 2
    from engine.plot_blinking import plot_cat_pact_forge_dc_bonus

    dc += plot_cat_pact_forge_dc_bonus(guild_id)

    from config import OATHBREAKER_FORGE_DC_CAP, OATHBREAKER_FORGE_DC_PER_BREAK

    oath_penalty = min(
        OATHBREAKER_FORGE_DC_CAP, db.oathbreaker_count(user) * OATHBREAKER_FORGE_DC_PER_BREAK
    )
    dc += oath_penalty
    oath_note = (
        f"\n_**{user['wolf_name']}**'s broken oaths follow them into this parley; **+{oath_penalty} dc**._"
        if oath_penalty
        else ""
    )

    result = _negotiate_check(user, dc, game_day=day)
    if not result["success"]:
        db.set_wolf_pact_fail_day(pack["id"], other["id"], day)
        tribute_note = (
            f"**{other_name}** keeps the **{treasury_cost + personal_cost}** bone tribute and leaves.\n\n"
            if (treasury_cost or personal_cost)
            else ""
        )
        return False, tribute_note + format_roll_result(result) + oath_note

    expires = day + spec["days"]
    db.upsert_wolf_treaty(
        guild_id,
        pack["id"],
        other["id"],
        pact_type=pact_type,
        terms_note=terms_note or "",
        forged_day=day,
        expires_day=expires,
        forged_by_discord_id=int(user["discord_id"]),
    )

    current = db.get_pack_relation(guild_id, pack["id"], other["id"])
    target_standing = max(spec["standing_floor"], current + spec["standing_gain"])
    if result["outcome"] == "critical_success":
        target_standing = min(10, target_standing + 1)

    marriage_tie = db.has_cross_pack_bonded_mate(int(pack["id"]), int(other["id"]))
    marriage_note = ""
    extra_days = 0
    if marriage_tie:
        target_standing = min(10, target_standing + WOLF_PACT_MARRIAGE_STANDING_BONUS)
        extra_days = WOLF_PACT_MARRIAGE_DAYS_BONUS
        marriage_note = (
            "\n\n_a bonded pair already ties these two dens together; the marriage "
            f"steadies the parley (+{WOLF_PACT_MARRIAGE_STANDING_BONUS} standing, "
            f"+{WOLF_PACT_MARRIAGE_DAYS_BONUS} sunrises)._"
        )

    delta = target_standing - current
    if delta:
        db.adjust_pack_relation(guild_id, pack["id"], other["id"], delta)
    new_standing = db.get_pack_relation(guild_id, pack["id"], other["id"])

    if extra_days:
        expires += extra_days
        db.upsert_wolf_treaty(
            guild_id,
            pack["id"],
            other["id"],
            pact_type=pact_type,
            terms_note=terms_note or "",
            forged_day=day,
            expires_day=expires,
            forged_by_discord_id=int(user["discord_id"]),
        )

    if spec["unity"]:
        db.adjust_pack_unity(pack["id"], spec["unity"])

    flavor = random.choice(WOLF_FORGE_SUCCESS).format(pack=other_name)
    terms = f"\n\n_terms: {terms_note}_" if terms_note else ""
    return True, (
        f"{format_roll_result(result)}{oath_note}\n\n{flavor}\n\n"
        f"**{PACT_TYPE_LABELS[pact_type]}** with **{other_name}** for **{spec['days'] + extra_days}** sunrises."
        f"{terms}{marriage_note}\n\n{relation_effect_text(new_standing)}"
    )


def renew_wolf_pack_pact(
    user, pack, *, guild_id: int, target_pack: str, day: int
) -> tuple[bool, str]:
    if not can_forge_cat_pact(user, pack):
        return False, "only the **alpha** or a **diplomat** can renew a wolf-pack treaty."

    other, err = resolve_wolf_pack_target(target_pack)
    if err:
        return False, err

    treaty = db.get_wolf_treaty(pack["id"], other["id"])
    if not treaty or treaty["status"] != "active":
        other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
        return False, f"no active treaty with **{other_name}** to renew."

    spec = WOLF_PACT_SPECS.get(treaty["pact_type"], WOLF_PACT_SPECS["truce"])
    new_expires = day + spec["days"]
    db.renew_wolf_treaty(pack["id"], other["id"], expires_day=new_expires, day=day)
    db.adjust_pack_relation(guild_id, pack["id"], other["id"], 1)
    standing = db.get_pack_relation(guild_id, pack["id"], other["id"])
    other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
    return True, (
        f"treaty with **{other_name}** renewed for **{spec['days']}** more sunrises "
        f"(standing **{standing}/10**)."
    )


def break_wolf_pack_pact(
    user,
    pack,
    *,
    guild_id: int,
    target_pack: str,
    day: int,
    reason: str = "Den withdrew from the treaty.",
) -> tuple[bool, str]:
    if not can_forge_cat_pact(user, pack):
        return False, "only the **alpha** or a **diplomat** can break a wolf-pack treaty."

    other, err = resolve_wolf_pack_target(target_pack)
    if err:
        return False, err

    treaty = db.get_wolf_treaty(pack["id"], other["id"])
    if not treaty or treaty["status"] != "active":
        other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
        return False, f"no active treaty with **{other_name}**."

    db.break_wolf_treaty(pack["id"], other["id"], day=day, reason=reason)
    db.adjust_pack_relation(guild_id, pack["id"], other["id"], -2)

    hostage_note = ""
    hostages = db.get_hostages_at_pack_from(int(other["id"]), int(pack["id"]))
    if hostages:
        from config import HOSTAGE_BETRAYAL_STANDING_PENALTY
        new_rel = db.adjust_pack_relation(guild_id, pack["id"], other["id"], HOSTAGE_BETRAYAL_STANDING_PENALTY)
        names = ", ".join(f"**{h['wolf_name']}**" for h in hostages)
        hostage_note = (
            f"\n\n_{names} still live in {GREAT_PACKS.get(other['key'], {}).get('name', other['name'])}'s den as "
            f"hostages; breaking faith with them standing there costs extra: standing "
            f"**{HOSTAGE_BETRAYAL_STANDING_PENALTY}** more (now **{new_rel}/10**)._"
        )

    standing = db.get_pack_relation(guild_id, pack["id"], other["id"])
    other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
    personal_count = db.mark_oathbreaker(int(user["id"]))
    return True, (
        f"**{pack['name']}** breaks the treaty with **{other_name}**.\n"
        f"_{reason}_\n\nstanding **−2** (now **{standing}/10**).{hostage_note}\n"
        f"_**{user['wolf_name']}** carries this oath broken now too "
        f"(**{personal_count}** personally); future negotiations they lead start with a wary den._"
    )


def send_hostage(
    user, pack, *, guild_id: int, target_pack: str, hostage, day: int
) -> tuple[bool, str]:
    """Send `hostage` (one of pack's own wolves) to live with target_pack as a good-faith guarantee."""
    if not can_forge_cat_pact(user, pack):
        return False, "only the **alpha** or a **diplomat** can offer a hostage."

    other, err = resolve_wolf_pack_target(target_pack)
    if err:
        return False, err
    if int(other["id"]) == int(pack["id"]):
        return False, "your own den doesn't need a hostage in itself."

    treaty = db.get_wolf_treaty(pack["id"], other["id"])
    if not treaty or treaty["status"] != "active":
        other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
        return False, f"no active treaty with **{other_name}**; forge one first."

    if hostage["hostage_at_pack_id"] if "hostage_at_pack_id" in hostage.keys() else None:
        return False, f"**{hostage['wolf_name']}** is already hosted elsewhere; recall them first."
    if int(hostage["pack_id"] or 0) != int(pack["id"]):
        return False, f"**{hostage['wolf_name']}** isn't a member of **{pack['name']}**."

    db.set_hostage(int(hostage["id"]), int(other["id"]))
    from config import HOSTAGE_TREATY_STANDING_BONUS

    new_rel = db.adjust_pack_relation(guild_id, pack["id"], other["id"], HOSTAGE_TREATY_STANDING_BONUS)
    other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
    return True, (
        f"**{hostage['wolf_name']}** goes to live in **{other_name}**'s den as a good-faith hostage.\n"
        f"standing **+{HOSTAGE_TREATY_STANDING_BONUS}** (now **{new_rel}/10**). "
        f"if **{pack['name']}** breaks faith with **{other_name}** while {hostage['wolf_name']} is there, it costs extra."
    )


def recall_hostage(user, pack, *, hostage) -> tuple[bool, str]:
    if not can_forge_cat_pact(user, pack):
        return False, "only the **alpha** or a **diplomat** can recall a hostage."
    host_pack_id = hostage["hostage_at_pack_id"] if "hostage_at_pack_id" in hostage.keys() else None
    if not host_pack_id:
        return False, f"**{hostage['wolf_name']}** isn't hosted anywhere."
    db.clear_hostage(int(hostage["id"]))
    host = db.get_pack(int(host_pack_id))
    host_name = host["name"] if host else "their host"
    return True, f"**{hostage['wolf_name']}** comes home from **{host_name}**'s den."


def infiltrate_pack(user, pack, *, target_pack: str, spy, day: int) -> tuple[bool, str]:
    """Embed one of pack's own wolves in a rival den under a false claim of defection."""
    if not can_forge_cat_pact(user, pack):
        return False, "only the **alpha** or a **diplomat** can plant a spy."

    other, err = resolve_wolf_pack_target(target_pack)
    if err:
        return False, err
    if int(other["id"]) == int(pack["id"]):
        return False, "you can't spy on your own den."
    if int(spy["pack_id"] or 0) != int(pack["id"]):
        return False, f"**{spy['wolf_name']}** isn't a member of **{pack['name']}**."
    if spy["spy_for_pack_id"] if "spy_for_pack_id" in spy.keys() else None:
        return False, f"**{spy['wolf_name']}** is already embedded elsewhere."
    if spy["hostage_at_pack_id"] if "hostage_at_pack_id" in spy.keys() else None:
        return False, f"**{spy['wolf_name']}** is currently a hostage elsewhere; recall them first."

    other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
    db.plant_spy(int(spy["id"]), host_pack_id=int(other["id"]), host_great_pack=other["key"], home_pack_id=int(pack["id"]))
    return True, (
        f"**{spy['wolf_name']}** slips into **{other_name}**'s den, posing as a defector. "
        f"use `/pact action:report` (as {spy['wolf_name']}) to send word home; every report risks exposure."
    )


def spy_report(spy, *, guild_id: int, day: int) -> tuple[bool, str]:
    home_pack_id = spy["spy_for_pack_id"] if "spy_for_pack_id" in spy.keys() else None
    if not home_pack_id:
        return False, "you aren't embedded in a rival den."
    host_pack_id = int(spy["pack_id"])
    host = db.get_pack(host_pack_id)
    home = db.get_pack(int(home_pack_id))
    if not host or not home:
        return False, "den record missing; the spy thread is broken."

    db.update_user_by_id(int(spy["id"]), last_spy_report_day=day)

    from engine.dice import roll_d20
    from engine.character import attr_modifier, parse_proficiencies
    from config import SPY_CAUGHT_RELATION_PENALTY, SPY_CAUGHT_STANDING, SPY_REPORT_DISCOVERY_DC

    profs = parse_proficiencies(spy["skill_proficiencies"])
    die = roll_d20()
    mod = attr_modifier(int(spy["attr_dex"]))
    bonus = 2 if "stealth" in profs else 0
    total = die + mod + bonus

    if total < SPY_REPORT_DISCOVERY_DC:
        db.unmask_spy(int(spy["id"]))
        db.adjust_wolf_standing_by_id(int(spy["id"]), SPY_CAUGHT_STANDING)
        new_rel = db.adjust_pack_relation(guild_id, int(home_pack_id), host_pack_id, SPY_CAUGHT_RELATION_PENALTY)
        return False, (
            f"**1d20** ({die}) {mod:+d} {f'+{bonus} stealth' if bonus else ''} = **{total}** vs dc **{SPY_REPORT_DISCOVERY_DC}**\n\n"
            f"**{spy['wolf_name']}** is caught feeding word back to **{home['name']}**; exposed and cast out of "
            f"**{host['name']}**'s den. standing **{SPY_CAUGHT_STANDING}**; pack relation **{SPY_CAUGHT_RELATION_PENALTY}** "
            f"(now **{new_rel}/10**)."
        )

    return True, (
        f"**1d20** ({die}) {mod:+d} {f'+{bonus} stealth' if bonus else ''} = **{total}** vs dc **{SPY_REPORT_DISCOVERY_DC}**\n\n"
        f"**{spy['wolf_name']}** slips word home from inside **{host['name']}**'s den:\n"
        f"treasury **{int(host['treasury'])}** bones · tax **{host['tax_rate']}%** · unity **{host['pack_unity']}**."
    )


def sanction_political_match(user, pack, *, guild_id: int, own_wolf, day: int) -> tuple[bool, str]:
    """
    Formally recognize an existing cross-pack bonded pair as a deliberate
    political alliance; the active counterpart to the passive marriage
    bonus baked into forge_wolf_pack_pact. Requires the two wolves already
    chose each other (no third-party-arranged consent flow); the alpha is
    just the one who makes it official den policy.
    """
    if not can_forge_cat_pact(user, pack):
        return False, "only the **alpha** or a **diplomat** can sanction a political match."

    from engine.attraction import are_bonded_mates

    if int(own_wolf["pack_id"] or 0) != int(pack["id"]):
        return False, f"**{own_wolf['wolf_name']}** isn't a member of **{pack['name']}**."
    mate_id = own_wolf["bonded_mate_id"] if "bonded_mate_id" in own_wolf.keys() else None
    if not mate_id:
        return False, f"**{own_wolf['wolf_name']}** has no bonded mate to sanction a match with."
    mate = db.get_user_by_id(int(mate_id))
    if not mate or not are_bonded_mates(own_wolf, mate):
        return False, "that bond isn't mutual on file; both wolves need to be bonded mates."
    mate_pack_id = mate["pack_id"]
    if not mate_pack_id or int(mate_pack_id) == int(pack["id"]):
        return False, f"**{own_wolf['wolf_name']}**'s mate must belong to a **different** great pack to sanction a political match."

    if db.is_match_sanctioned(int(own_wolf["id"]), int(mate["id"])):
        return False, "this match is already sanctioned; the alliance bonus already applied."

    mate_pack = db.get_pack(int(mate_pack_id))
    db.mark_match_sanctioned(int(own_wolf["id"]), int(mate["id"]))

    from config import POLITICAL_MATCH_STANDING_BONUS

    new_rel = db.adjust_pack_relation(guild_id, int(pack["id"]), int(mate_pack_id), POLITICAL_MATCH_STANDING_BONUS)
    return True, (
        f"**{pack['name']}** sanctions the bond between **{own_wolf['wolf_name']}** and **{mate['wolf_name']}** "
        f"of **{mate_pack['name']}** as a deliberate alliance.\n"
        f"pack relation **+{POLITICAL_MATCH_STANDING_BONUS}** (now **{new_rel}/10**); future treaties between these "
        f"two dens carry the existing marriage-alliance bonus."
    )


def _active_wolf_treaty(pack_id: int, other_pack_id: int):
    treaty = db.get_wolf_treaty(pack_id, other_pack_id)
    if treaty and treaty["status"] == "active":
        return treaty
    return None


def gift_wolf_pack_pact(
    user, pack, *, guild_id: int, target_pack: str, day: int, amount: int | None = None
) -> tuple[bool, str]:
    from config import CAT_PACT_GIFT_TRIBUTE

    if not can_forge_cat_pact(user, pack):
        return False, "only the **alpha** or a **diplomat** can send border tribute."

    other, err = resolve_wolf_pack_target(target_pack)
    if err:
        return False, err
    if not _active_wolf_treaty(pack["id"], other["id"]):
        other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
        return False, f"no active treaty with **{other_name}**."

    spend = CAT_PACT_GIFT_TRIBUTE if amount is None else max(0, int(amount))
    if spend > 0 and not db.deduct_pack_treasury(pack["id"], spend):
        return False, f"treasury doesn't have **{spend}** bones to spare."

    from config import WOLF_PACT_GIFT_STANDING

    standing_gain = round(WOLF_PACT_GIFT_STANDING * spend / CAT_PACT_GIFT_TRIBUTE) if spend > 0 else 0
    standing = (
        db.adjust_pack_relation(guild_id, pack["id"], other["id"], standing_gain)
        if standing_gain
        else db.get_pack_relation(guild_id, pack["id"], other["id"])
    )
    db.mark_cat_pact_gift_day(pack["id"], day)
    other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
    flavor = (
        f"prey bones and scent-gifts left at the border for **{other_name}**."
        if spend > 0
        else f"you show up at the border empty-pawed; **{other_name}** notices."
    )
    return True, (
        f"{flavor}\n"
        f"spent **{spend}** bones; standing **{'+' if standing_gain >= 0 else ''}{standing_gain}** (now **{standing}/10**)."
    )


def trade_duplicates_wolf_pack_pact(
    user, pack, *, guild_id: int, target_pack: str, day: int
) -> tuple[bool, str]:
    other, err = resolve_wolf_pack_target(target_pack)
    if err:
        return False, err
    if not _active_wolf_treaty(pack["id"], other["id"]):
        other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
        return False, f"no active treaty with **{other_name}**."

    from engine.duplicate_trade import (
        collect_duplicates,
        format_duplicate_summary,
        surrender_duplicates,
    )

    bundle = collect_duplicates(user["id"])
    if bundle.is_empty():
        return False, f"no duplicates in your hoard.\n\n_{format_duplicate_summary(bundle)}_"

    ok, detail = surrender_duplicates(user["id"], bundle)
    if not ok:
        return False, detail

    from config import WOLF_PACT_DUP_STANDING_MAX
    from engine.energy import spend_energy

    _new_energy, _had_energy, trade_penalty = spend_energy(user, "duplicate_trade")
    standing_gain = min(WOLF_PACT_DUP_STANDING_MAX, max(1, bundle.total_items // 4))
    standing = db.adjust_pack_relation(guild_id, pack["id"], other["id"], standing_gain)
    db.update_user(user["discord_id"], last_duplicate_trade_day=day, wolf_id=user["id"])

    from engine.wolf_pact_goods import barter_loot_count, grant_wolf_pact_loot, roll_wolf_pact_loot

    treaty = _active_wolf_treaty(pack["id"], other["id"])
    loot_count = barter_loot_count(bundle.total_items, standing=standing)
    loot_lines: list[str] = []
    if loot_count > 0 and treaty:
        entries = roll_wolf_pact_loot(
            other["key"], pact_type=treaty["pact_type"], count=loot_count
        )
        loot_lines = grant_wolf_pact_loot(user, guild_id=guild_id, day=day, entries=entries)
    loot_block = "\n".join(f"• {line}" for line in loot_lines) if loot_lines else "_no goods this time._"
    other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
    dim = f"\n\n_{trade_penalty}_" if trade_penalty else ""
    return True, (
        f"**{other_name}** scouts take your duplicate hoard at the neutral stone.\n"
        f"standing **+{standing_gain}** (now **{standing}/10**).\n\n"
        f"**you gave up:**\n{detail}\n\n"
        f"**from the pack:**\n{loot_block}{dim}"
    )


def trade_food_wolf_pack_pact(
    user, pack, *, guild_id: int, target_pack: str, stack_id: int, day: int
) -> tuple[bool, str]:
    from config import (
        WOLF_PACT_FOOD_FORAGE_STANDING_PER_USE,
        WOLF_PACT_FOOD_MEAT_STANDING_PER_BONE,
        WOLF_PACT_FOOD_STANDING_MAX,
    )
    from engine.prey_items import is_forage_food, prey_meta

    other, err = resolve_wolf_pack_target(target_pack)
    if err:
        return False, err
    treaty = _active_wolf_treaty(pack["id"], other["id"])
    if not treaty:
        other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
        return False, f"no active treaty with **{other_name}**."

    stack = db.get_prey_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "you don't carry that stack (`/food` for ids)."
    uses_left = int(stack["uses_left"])
    if uses_left <= 0:
        return False, "there's nothing left of that to trade."

    from engine.energy import spend_energy

    _new_energy, _had_energy, trade_penalty = spend_energy(user, "wolf_pact_food_trade")

    meta = prey_meta(stack["prey_key"])
    if is_forage_food(stack["prey_key"]):
        standing_gain = min(
            WOLF_PACT_FOOD_STANDING_MAX,
            max(1, round(uses_left * WOLF_PACT_FOOD_FORAGE_STANDING_PER_USE)),
        )
        loot_count = 0
        flavor = f"**{other['name']}** takes the **{meta['name']}** for sick denmates."
    else:
        bone_value = int(stack["bone_value"])
        standing_gain = min(
            WOLF_PACT_FOOD_STANDING_MAX,
            max(1, round(bone_value * WOLF_PACT_FOOD_MEAT_STANDING_PER_BONE)),
        )
        loot_count = max(1, min(3, bone_value // 15))
        flavor = f"fresh-kill shared with **{GREAT_PACKS.get(other['key'], {}).get('name', other['name'])}**."

    db.remove_prey_stack(stack_id)
    standing = db.adjust_pack_relation(guild_id, pack["id"], other["id"], standing_gain)
    db.update_user(user["discord_id"], last_cat_food_trade_day=day, wolf_id=user["id"])

    from engine.wolf_pact_goods import grant_wolf_pact_loot, roll_wolf_pact_loot

    loot_lines: list[str] = []
    if loot_count > 0:
        entries = roll_wolf_pact_loot(other["key"], pact_type=treaty["pact_type"], count=loot_count)
        loot_lines = grant_wolf_pact_loot(user, guild_id=guild_id, day=day, entries=entries)
    loot_block = "\n".join(f"• {line}" for line in loot_lines) if loot_lines else "_they send nothing back this time._"
    dim = f"\n\n_{trade_penalty}_" if trade_penalty else ""
    return True, (
        f"{flavor}\nstanding **+{standing_gain}** (now **{standing}/10**).\n\n"
        f"**you gave up:** {meta['name']} ({uses_left} use(s))\n\n"
        f"**from the pack:**\n{loot_block}{dim}"
    )


def receive_wolf_pack_goods(
    user, pack, *, guild_id: int, target_pack: str, day: int
) -> tuple[bool, str]:
    from config import WOLF_PACT_RECEIVE_MIN_STANDING

    other, err = resolve_wolf_pack_target(target_pack)
    if err:
        return False, err
    treaty = _active_wolf_treaty(pack["id"], other["id"])
    if not treaty:
        other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
        return False, f"no active treaty with **{other_name}**."

    standing = db.get_pack_relation(guild_id, pack["id"], other["id"])
    if standing < WOLF_PACT_RECEIVE_MIN_STANDING:
        return False, (
            f"**{other['name']}** won't leave border gifts yet; standing **{standing}** "
            f"(need **{WOLF_PACT_RECEIVE_MIN_STANDING}**). gift, barter, or share territory first."
        )

    from engine.energy import spend_energy
    from engine.wolf_pact_goods import grant_wolf_pact_loot, receive_loot_count, roll_wolf_pact_loot

    _new_energy, _had_energy, receive_penalty = spend_energy(user, "wolf_receive")
    count = receive_loot_count(standing, treaty["pact_type"])
    if count <= 0:
        return False, "standing is too low for border gifts."

    entries = roll_wolf_pact_loot(other["key"], pact_type=treaty["pact_type"], count=count)
    lines = grant_wolf_pact_loot(user, guild_id=guild_id, day=day, entries=entries)
    db.update_user(user["discord_id"], last_wolf_receive_day=day, wolf_id=user["id"])
    other_name = GREAT_PACKS.get(other["key"], {}).get("name", other["name"])
    body = "\n".join(f"• {line}" for line in lines)
    dim = f"\n\n_{receive_penalty}_" if receive_penalty else ""
    return True, (
        f"**{other_name}** left goods at the neutral stone (standing **{standing}**).\n\n"
        f"{body}{dim}\n\n_barter duplicates with `action:trade`_"
    )


def wolf_pact_border_multiplier(guild_id: int, pack_id: int | None) -> float:
    """Friendly wolf treaties calm the border (fewer random cat fights on sniff)."""
    from config import WOLF_PACT_RECEIVE_MIN_STANDING

    if not pack_id:
        return 1.0
    treaties = db.list_active_wolf_treaties(guild_id, pack_id)
    if not treaties:
        return 1.0
    mult = 1.0
    for treaty in treaties:
        standing = db.get_pack_relation(guild_id, pack_id, int(treaty["other_pack_id"]))
        if standing >= WOLF_PACT_RECEIVE_MIN_STANDING:
            mult *= 0.75
        elif standing >= 6:
            mult *= 0.9
    return mult

