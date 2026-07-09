"""Pack collaborative scout patrols; survey borders or follow cold trails together."""

from __future__ import annotations

import random

import discord

import database as db
from config import (
    COLLAB_PATROL_ALL_SCOUTS_BONUS,
    COLLAB_PATROL_AMBUSH_CHANCE,
    COLLAB_PATROL_BONUS_PCT_PER_SCOUT,
    COLLAB_PATROL_MAX_WOLVES,
    COLLAB_PATROL_MIN_WOLVES,
    COLLAB_PATROL_MOOD_BONUS,
    SCOUT_SURVEY_BONES,
    SCOUT_TRAIL_BONES,
)
from engine.character import parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from engine.injury_effects import strenuous_activity_blocked_by_injury
from engine.prey_storage import grant_prey_carcass
from engine.role_features import scout_hide_after_check
from engine.role_privileges import is_scout
from engine.scout_field import (
    SURVEY_FLAVOR,
    SURVEY_INTEL,
    TRAIL_FLAVOR,
    TRAIL_INTEL,
    TRAIL_PREY,
)
from engine.vitals import full_activity_block
from engine.wild_encounters import ambush_embed, maybe_start_activity_ambush
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed

PATROL_FLAVOR = [
    "scouts ghost along the ridge in loose formation; no silhouette, no wasted breath.",
    "you split the border into beats and sweep them twice before the den wakes.",
    "Wind-check, paw-sign, and a tail signal; the patrol moves as one quiet line.",
]

TRAIL_PARTY_FLAVOR = [
    "scouts split the spoor line; one reads, one flanks, one holds the wind.",
    "you leapfrog along the cold trail, never two silhouettes on the same ridge.",
    "Paw-sign and breath held; the party follows sign deeper than lone wolves dare.",
]


def _patrol_kind(patrol) -> str:
    if not patrol:
        return "survey"
    kind = patrol["patrol_kind"] if "patrol_kind" in patrol.keys() else "survey"
    return kind or "survey"


def _is_trail(patrol) -> bool:
    return _patrol_kind(patrol) == "trail"


def _is_war_patrol(patrol) -> bool:
    return _patrol_kind(patrol) == "war_patrol"


def _party_users(patrol_id: int) -> list:
    members = db.get_collab_patrol_members(patrol_id)
    users = [db.get_user_by_id(m["wolf_id"]) for m in members]
    return [u for u in users if u]


def _party_names(patrol_id: int) -> str:
    return ", ".join(m["wolf_name"] for m in db.get_collab_patrol_members(patrol_id))


def _war_patrol_block_reason(user, day: int, *, guild_id: int, pack_id: int) -> str | None:
    war = db.get_active_war_for_pack(guild_id, pack_id)
    if not war:
        return "your pack isn't fighting for territory; no collab war patrol."
    if db.wolf_in_open_collab_patrol(user["id"]):
        return "this wolf is already on an open pack patrol or trail."
    return None


def _scout_block_reason(user, day: int, *, kind: str = "survey") -> str | None:
    if not is_scout(user):
        label = "trail" if kind == "trail" else "patrol"
        return f"only **scout** wolves can join a pack {label}."
    inj = strenuous_activity_blocked_by_injury(user)
    if inj:
        return inj
    vitals = full_activity_block(user, day, action=kind if kind in ("survey", "trail") else "patrol")
    if vitals:
        return vitals
    if db.wolf_in_open_collab_patrol(user["id"]):
        return "this wolf is already on an open pack patrol or trail."
    return None


def validate_start_collab_patrol(
    user, *, guild_id: int, day: int, kind: str = "survey"
) -> str | None:
    if not db.row_val(user, "pack_id"):
        label = "war patrols" if kind == "war_patrol" else "trails" if kind == "trail" else "patrols"
        return f"join a great pack first; pack {label} are den business."
    if kind == "war_patrol":
        reason = _war_patrol_block_reason(
            user, day, guild_id=guild_id, pack_id=user["pack_id"]
        )
    else:
        reason = _scout_block_reason(user, day, kind=kind)
    if reason:
        return reason
    if db.get_open_collab_patrol_by_leader(user["id"]):
        label = "war patrol" if kind == "war_patrol" else "trail" if kind == "trail" else "patrol"
        return f"you already called a pack {label}. set out or cancel it first."
    return None


def validate_join_collab_patrol(user, patrol, day: int) -> str | None:
    if patrol["status"] != "open":
        label = "war patrol" if _is_war_patrol(patrol) else "trail" if _is_trail(patrol) else "patrol"
        return f"this pack {label} is no longer open."
    if user["pack_id"] != patrol["pack_id"]:
        return "only wolves in the same great pack can join."
    members = db.get_collab_patrol_members(patrol["id"])
    if any(m["wolf_id"] == user["id"] for m in members):
        return "this wolf is already on the party."
    if len(members) >= COLLAB_PATROL_MAX_WOLVES:
        return f"the party is full ({COLLAB_PATROL_MAX_WOLVES} wolves max)."
    if _is_war_patrol(patrol):
        return _war_patrol_block_reason(
            user, day, guild_id=patrol["guild_id"], pack_id=patrol["pack_id"]
        )
    return _scout_block_reason(user, day, kind=_patrol_kind(patrol))


def wolves_eligible_to_join_patrol(discord_id: int, patrol_id: int, day: int) -> list:
    patrol = db.get_collab_patrol(patrol_id)
    if not patrol:
        return []
    member_ids = {m["wolf_id"] for m in db.get_collab_patrol_members(patrol_id)}
    eligible = []
    for wolf in db.list_user_wolves(discord_id):
        if wolf["pack_id"] != patrol["pack_id"]:
            continue
        if wolf["id"] in member_ids:
            continue
        if validate_join_collab_patrol(wolf, patrol, day):
            continue
        eligible.append(wolf)
    return eligible


def build_collab_patrol_embed(patrol_id: int) -> discord.Embed:
    patrol = db.get_collab_patrol(patrol_id)
    if not patrol:
        return howlbert_embed("pack scout party", "party not found.", color=ERROR_COLOR)
    trail = _is_trail(patrol)
    war = _is_war_patrol(patrol)
    members = db.get_collab_patrol_members(patrol_id)
    leader = db.get_user_by_id(patrol["leader_wolf_id"])
    leader_name = leader["wolf_name"] if leader else "Unknown"
    pack = db.get_pack(patrol["pack_id"])
    pack_name = pack["name"] if pack else "the den"

    if patrol["status"] == "open":
        if war:
            title = "war patrol called"
            flavor = random.choice(PATROL_FLAVOR)
            spend = "war patrol"
            role_note = "any packmate"
        elif trail:
            title = "pack trail called"
            flavor = random.choice(TRAIL_PARTY_FLAVOR)
            spend = "trail"
            role_note = "scouts"
        else:
            title = "pack patrol called"
            flavor = random.choice(PATROL_FLAVOR)
            spend = "survey"
            role_note = "scouts"
        desc = (
            f"**{leader_name}** calls {role_note.lower()} to "
            f"{'hold the war line' if war else 'follow a cold trail' if trail else 'patrol'} for **{pack_name}**.\n"
            f"{flavor}\n\n"
            f"**party** ({len(members)}/{COLLAB_PATROL_MAX_WOLVES}); need at least "
            f"**{COLLAB_PATROL_MIN_WOLVES}** to set out.\n"
            f"each wolf spends their **{spend}** this sunrise. "
            f"+**{COLLAB_PATROL_BONUS_PCT_PER_SCOUT}%** {'war points' if war else 'bones'} per extra wolf.\n"
            + (
                "Ambushes can still strike; party fights together (+1 attack per ally, max +3)."
                if not war
                else "Hold the contested line together."
            )
        )
        color = SUCCESS_COLOR
    elif patrol["status"] == "encounter":
        title = "pack party; fight!"
        desc = (
            f"the party (**{_party_names(patrol_id)}**) was ambushed.\n"
            "Combat is live below; win to finish. Packmates fight on their own turns (+1 attack per ally)."
        )
        color = SUCCESS_COLOR
    elif patrol["status"] == "done":
        title = "war patrol complete" if war else "pack trail complete" if trail else "pack patrol complete"
        desc = patrol["result_text"] or "The scouts returned to the den."
        color = SUCCESS_COLOR
    else:
        title = "war patrol closed" if war else "pack trail closed" if trail else "pack patrol closed"
        desc = "this party was cancelled or the den rolled over."
        color = ERROR_COLOR

    embed = howlbert_embed(title, desc, color=color)
    if members:
        field_name = "party" if war else "scouts"
        lines = [
            f"• **{m['wolf_name']}**" + (" (caller)" if m["wolf_id"] == patrol["leader_wolf_id"] else "")
            for m in members
        ]
        embed.add_field(name=field_name, value="\n".join(lines), inline=False)
    if patrol["status"] == "open":
        chemistry = ""
        if len(members) >= 2 and not war:
            from engine.hunt_party import collab_hunt_bond_modifiers

            users = _party_users(patrol_id)
            world = db.get_world(patrol["guild_id"])
            season = world["season"] if world else None
            bond_bonus, bond_note = collab_hunt_bond_modifiers(users, season=season)
            if bond_note:
                chemistry = f" · {bond_note.strip('_')}"
            elif bond_bonus:
                chemistry = f" · chemistry **+{bond_bonus}%**"
        footer_role = "Packmates" if war else "Scouts"
        embed.set_footer(
            text=(
                f"{footer_role} join below · caller sets out when ready · "
                f"max {COLLAB_PATROL_MAX_WOLVES} wolves{chemistry}"
            )
        )
    return embed


def _compute_party_base(
    users: list, *, kind: str, fixed_base: int | None = None, season: str | None = None
) -> tuple[int, int, str]:
    if fixed_base is not None:
        base = fixed_base
    else:
        base = random.randint(*(SCOUT_TRAIL_BONES if kind == "trail" else SCOUT_SURVEY_BONES))
    bonus_pct = (len(users) - 1) * COLLAB_PATROL_BONUS_PCT_PER_SCOUT if users else 0
    if users and all(is_scout(u) for u in users):
        bonus_pct += COLLAB_PATROL_ALL_SCOUTS_BONUS
    chemistry_note = ""
    if len(users) >= 2:
        from engine.hunt_party import collab_hunt_bond_modifiers

        bond_bonus, bond_note = collab_hunt_bond_modifiers(users, season=season)
        if bond_bonus == -100:
            base = 0
            bonus_pct = 0
            chemistry_note = bond_note.strip("_")
        elif bond_bonus > 0:
            bonus_pct += bond_bonus
            chemistry_note = bond_note.strip("_") if bond_note else f"pack chemistry **+{bond_bonus}%**"
        elif bond_bonus < 0:
            base = max(0, int(base * (100 + bond_bonus) / 100))
            chemistry_note = bond_note.strip("_")
    if base > 0 and bonus_pct:
        base = max(0, int(base * (100 + bonus_pct) / 100))
    return base, bonus_pct, chemistry_note


def _mark_survey_done(users: list, day: int, *, guild_id: int) -> None:
    for user in users:
        db.update_user(user["discord_id"], wolf_id=user["id"], last_survey_day=day)
        db.increment_quest_progress(user["discord_id"], "survey", guild_id=guild_id)
        db.increment_quest_progress(user["discord_id"], "patrol", guild_id=guild_id)


def _mark_trail_done(users: list, day: int) -> None:
    for user in users:
        db.update_user(user["discord_id"], wolf_id=user["id"], last_trail_day=day)
        db.increment_quest_progress(user["discord_id"], "trail")


def payout_collab_survey(
    patrol_id: int,
    *,
    fixed_base: int | None = None,
    encounter_note: str = "",
    roll_lines: list[str] | None = None,
    standing_delta: int = 1,
) -> discord.Embed:
    patrol = db.get_collab_patrol(patrol_id)
    if not patrol:
        return howlbert_embed("pack scout party", "party not found.", color=ERROR_COLOR)
    if patrol["status"] == "done":
        return build_collab_patrol_embed(patrol_id)
    users = _party_users(patrol_id)
    world = db.get_world(patrol["guild_id"])
    day = world["day_number"]
    season = world["season"] if world else None

    base, bonus_pct, chemistry_note = _compute_party_base(
        users, kind="survey", fixed_base=fixed_base, season=season
    )
    share = base // len(users) if users else 0
    remainder = base - share * len(users)

    lines: list[str] = []
    from engine.diminishing import diminishing_note, next_use_multiplier
    from engine.plot_blinking import plot_thistlehide_patrol_standing_bonus

    for user in users:
        bones = share + (remainder if user["id"] == patrol["leader_wolf_id"] else 0)
        survey_mult, survey_n = next_use_multiplier(user, "survey", day)
        if bones > 0:
            bones = max(0, int(bones * survey_mult))
            db.add_bones(user["discord_id"], bones, wolf_id=user["id"])
        standing_gain = standing_delta
        if standing_delta:
            gp = user["great_pack"] if "great_pack" in user.keys() else None
            standing_gain += plot_thistlehide_patrol_standing_bonus(
                patrol["guild_id"], gp, user=user
            )
            from engine.injury_effects import injury_patrol_standing_bonus
            standing_gain += injury_patrol_standing_bonus(user)
            db.adjust_wolf_standing(user["discord_id"], standing_gain)
        db.adjust_mood(user["id"], COLLAB_PATROL_MOOD_BONUS)
        dim = ""  # payouts no longer diminish; energy is the throttle
        if standing_delta:
            lines.append(f"**{user['wolf_name']}** +{bones} bones · standing **+{standing_gain}**{dim}")
        else:
            lines.append(f"**{user['wolf_name']}** +{bones} bones{dim}")

    _mark_survey_done(users, day, guild_id=patrol["guild_id"])
    db.adjust_pack_unity(patrol["pack_id"], 1)

    flavor = random.choice(SURVEY_FLAVOR)
    if encounter_note:
        flavor = encounter_note + "\n\n" + flavor

    bonus_note = f"+{bonus_pct}% patrol bonus"
    if users and all(is_scout(u) for u in users):
        bonus_note += " (all scouts)"
    if chemistry_note:
        bonus_note += f" · _{chemistry_note}_"

    roll_block = ""
    if roll_lines:
        roll_block = "\n\n" + "\n".join(roll_lines) + "\n"

    intel = ""
    if standing_delta > 0 and random.random() < 0.4:
        intel = f"\n_{random.choice(SURVEY_INTEL)}_"

    result_text = (
        f"{flavor}{roll_block}\n"
        + "\n".join(lines)
        + f"\n\n**{bonus_note}** · pack unity **+1**{intel}"
    )
    db.set_collab_patrol_status(patrol_id, "done", result_text=result_text)
    return build_collab_patrol_embed(patrol_id)


def payout_collab_trail(
    patrol_id: int,
    *,
    fixed_base: int | None = None,
    encounter_note: str = "",
    roll_lines: list[str] | None = None,
    crit_success: bool = False,
) -> discord.Embed:
    patrol = db.get_collab_patrol(patrol_id)
    if not patrol:
        return howlbert_embed("pack scout party", "party not found.", color=ERROR_COLOR)
    if patrol["status"] == "done":
        return build_collab_patrol_embed(patrol_id)
    users = _party_users(patrol_id)
    world = db.get_world(patrol["guild_id"])
    day = world["day_number"]
    season = world["season"] if world else None
    leader = db.get_user_by_id(patrol["leader_wolf_id"])

    base, bonus_pct, chemistry_note = _compute_party_base(
        users, kind="trail", fixed_base=fixed_base, season=season
    )
    share = base // len(users) if users else 0
    remainder = base - share * len(users)

    lines: list[str] = []
    from engine.diminishing import diminishing_note, next_use_multiplier

    for user in users:
        bones = share + (remainder if user["id"] == patrol["leader_wolf_id"] else 0)
        trail_mult, trail_n = next_use_multiplier(user, "trail", day)
        if bones > 0:
            bones = max(0, int(bones * trail_mult))
            db.add_bones(user["discord_id"], bones, wolf_id=user["id"])
        db.adjust_mood(user["id"], COLLAB_PATROL_MOOD_BONUS)
        dim = ""  # payouts no longer diminish; energy is the throttle
        lines.append(f"**{user['wolf_name']}** +{bones} bones{dim}")

    _mark_trail_done(users, day)
    db.adjust_pack_unity(patrol["pack_id"], 1)

    prey_note = ""
    if leader and random.random() < (0.55 if crit_success else 0.4):
        keys, weights = zip(*TRAIL_PREY)
        loot = random.choices(keys, weights=weights, k=1)[0]
        if loot == "bones":
            extra = random.randint(4, 10)
            db.add_bones(leader["discord_id"], extra, wolf_id=leader["id"])
            prey_note = f"\n**sign cache** to **{leader['wolf_name']}**; +{extra} bones."
        else:
            grant_prey_carcass(
                leader["id"],
                loot,
                guild_id=patrol["guild_id"],
                acquired_day=day,
            )
            from engine.prey_items import prey_meta

            prey_note = (
                f"\n**caught up**; **{prey_meta(loot)['name']}** to caller's hoard (`/food`)."
            )

    flavor = random.choice(TRAIL_FLAVOR)
    if encounter_note:
        flavor = encounter_note + "\n\n" + flavor

    bonus_note = f"+{bonus_pct}% trail bonus"
    if users and all(is_scout(u) for u in users):
        bonus_note += " (all scouts)"
    if chemistry_note:
        bonus_note += f" · _{chemistry_note}_"

    roll_block = ""
    if roll_lines:
        roll_block = "\n\n" + "\n".join(roll_lines) + "\n"

    intel = ""
    if random.random() < (0.45 if crit_success else 0.25):
        intel = f"\n_{random.choice(TRAIL_INTEL)}_"

    crit = " **Perfect read!**" if crit_success else ""
    result_text = (
        f"{flavor}{roll_block}\n"
        + "\n".join(lines)
        + f"\n\n{crit}**{bonus_note}** · pack unity **+1**{prey_note}{intel}"
    )
    db.set_collab_patrol_status(patrol_id, "done", result_text=result_text)
    return build_collab_patrol_embed(patrol_id)


def resolve_collab_survey(patrol_id: int) -> tuple[discord.Embed | None, str | None]:
    patrol = db.get_collab_patrol(patrol_id)
    users = _party_users(patrol_id)
    world = db.get_world(patrol["guild_id"])
    day = world["day_number"]
    roll_lines: list[str] = []
    successes = 0
    crit_fail = False
    crit_success = False
    hide_notes: list[str] = []

    for user in users:
        profs = parse_proficiencies(user["skill_proficiencies"])
        result = resolve_check(
            user,
            attr_keys=("attr_wis", "attr_dex"),
            skill="Stealth",
            dc=11,
            proficient="stealth" in profs or "tracking" in profs,
            skill_key="stealth",
            game_day=day,
        )
        roll_lines.append(f"**{user['wolf_name']}**; {format_roll_result(result)}")
        if result["success"]:
            successes += 1
            note = scout_hide_after_check(
                user,
                weather_key=world["weather"],
                day=day,
                skill_key="stealth",
                success=True,
            )
            if note:
                hide_notes.append(note)
        if result["outcome"] == "critical_failure":
            crit_fail = True
        if result["outcome"] == "critical_success":
            crit_success = True

    needed = (len(users) + 1) // 2
    if crit_fail and successes < needed:
        from engine.injury_effects import injury_caught_standing_penalty
        extra_penalty_lines = []
        for user in users:
            standing_loss = -1 + injury_caught_standing_penalty(user)
            db.adjust_wolf_standing(user["discord_id"], standing_loss)
            db.update_user(user["discord_id"], wolf_id=user["id"], last_survey_day=day)
            if standing_loss < -1:
                extra_penalty_lines.append(
                    f"**{user['wolf_name']}**'s injury slowed the getaway; standing **{standing_loss}**."
                )
        result_text = (
            random.choice(SURVEY_FLAVOR)
            + "\n\n"
            + "\n".join(roll_lines)
            + "\n\nThe patrol was **spotted** on the ridge; standing **−1** each."
        )
        if extra_penalty_lines:
            result_text += "\n\n" + "\n".join(extra_penalty_lines)
        db.set_collab_patrol_status(patrol_id, "done", result_text=result_text)
        return build_collab_patrol_embed(patrol_id), None

    if successes < needed:
        result_text = (
            random.choice(SURVEY_FLAVOR)
            + "\n\n"
            + "\n".join(roll_lines)
            + "\n\nThe border stays quiet; nothing worth reporting."
        )
        for user in users:
            db.update_user(user["discord_id"], wolf_id=user["id"], last_survey_day=day)
        db.set_collab_patrol_status(patrol_id, "done", result_text=result_text)
        return build_collab_patrol_embed(patrol_id), None

    standing = 2 if crit_success else 1
    fixed = random.randint(*SCOUT_SURVEY_BONES)
    if crit_success:
        fixed += 8
    embed = payout_collab_survey(
        patrol_id,
        fixed_base=fixed,
        roll_lines=roll_lines,
        standing_delta=standing,
    )
    if hide_notes:
        patrol_row = db.get_collab_patrol(patrol_id)
        db.set_collab_patrol_status(
            patrol_id,
            "done",
            result_text=(patrol_row["result_text"] or "") + "".join(hide_notes),
        )
        embed = build_collab_patrol_embed(patrol_id)
    return embed, None


def resolve_collab_trail(patrol_id: int) -> tuple[discord.Embed | None, str | None]:
    patrol = db.get_collab_patrol(patrol_id)
    users = _party_users(patrol_id)
    world = db.get_world(patrol["guild_id"])
    day = world["day_number"]
    roll_lines: list[str] = []
    successes = 0
    crit_fail = False
    crit_success = False

    for user in users:
        profs = parse_proficiencies(user["skill_proficiencies"])
        result = resolve_check(
            user,
            attr_keys=("attr_wis", "attr_int"),
            skill="Tracking",
            dc=12,
            proficient="tracking" in profs,
            skill_key="tracking",
            game_day=day,
        )
        roll_lines.append(f"**{user['wolf_name']}**; {format_roll_result(result)}")
        if result["success"]:
            successes += 1
        if result["outcome"] == "critical_failure":
            crit_fail = True
        if result["outcome"] == "critical_success":
            crit_success = True

    needed = (len(users) + 1) // 2
    if crit_fail and successes < needed:
        for user in users:
            db.adjust_mood(user["id"], -2)
            db.update_user(user["discord_id"], wolf_id=user["id"], last_trail_day=day)
        result_text = (
            random.choice(TRAIL_FLAVOR)
            + "\n\n"
            + "\n".join(roll_lines)
            + "\n\nThe spoor vanishes in bog-water; **−2 mood** each."
        )
        db.set_collab_patrol_status(patrol_id, "done", result_text=result_text)
        return build_collab_patrol_embed(patrol_id), None

    if successes < needed:
        result_text = (
            random.choice(TRAIL_FLAVOR)
            + "\n\n"
            + "\n".join(roll_lines)
            + "\n\nThe trail goes cold."
        )
        for user in users:
            db.update_user(user["discord_id"], wolf_id=user["id"], last_trail_day=day)
        db.set_collab_patrol_status(patrol_id, "done", result_text=result_text)
        return build_collab_patrol_embed(patrol_id), None

    fixed = random.randint(*SCOUT_TRAIL_BONES)
    if crit_success:
        fixed += 10
    embed = payout_collab_trail(
        patrol_id,
        fixed_base=fixed,
        roll_lines=roll_lines,
        crit_success=crit_success,
    )
    return embed, None


def resolve_collab_war_patrol(patrol_id: int) -> tuple[discord.Embed | None, str | None]:
    from engine.character import attr_modifier, get_attr

    patrol = db.get_collab_patrol(patrol_id)
    users = _party_users(patrol_id)
    world = db.get_world(patrol["guild_id"])
    day = world["day_number"]
    war = db.get_active_war_for_pack(patrol["guild_id"], patrol["pack_id"])
    if not war:
        return None, "the war ended before your patrol set out."

    from engine.diminishing import diminishing_note, next_use_multiplier

    lines: list[str] = []
    raw_points = 0
    for user in users:
        pts = random.randint(2, 5) + max(0, attr_modifier(get_attr(user, "con")))
        patrol_mult, patrol_n = next_use_multiplier(user, "war_patrol", day)
        pts = max(1, int(pts * patrol_mult))
        raw_points += pts
        dim = ""  # payouts no longer diminish; energy is the throttle
        lines.append(f"**{user['wolf_name']}** +{pts} pts{dim}")

    bonus_pct = (len(users) - 1) * COLLAB_PATROL_BONUS_PCT_PER_SCOUT if users else 0
    total = raw_points
    if total > 0 and bonus_pct:
        total = max(0, int(total * (100 + bonus_pct) / 100))

    db.add_war_score(war["id"], patrol["pack_id"], total)
    from engine.strenuous_strain import apply_strenuous_strain

    strain_lines: list[str] = []
    for user in users:
        db.update_user(user["discord_id"], wolf_id=user["id"], last_patrol_day=day)
        db.increment_quest_progress(user["discord_id"], "patrol", guild_id=patrol["guild_id"])
        db.adjust_mood(user["id"], COLLAB_PATROL_MOOD_BONUS)
        # a war patrol is strenuous; pushing a hurt/pregnant body has a price.
        _strain = apply_strenuous_strain(user, day, "patrol")
        if _strain:
            strain_lines.append(f"**{user['wolf_name']}**: {_strain}")

    db.adjust_pack_unity(patrol["pack_id"], 1)
    war = db.get_active_war_for_pack(patrol["guild_id"], patrol["pack_id"])
    war_line = ""
    if war:
        war_line = (
            f"**{war['territory_name']}**; attack **{war['attacker_score']}** · "
            f"defend **{war['defender_score']}**"
        )
    result_text = (
        f"{random.choice(PATROL_FLAVOR)}\n\n"
        + "\n".join(lines)
        + f"\n\n**+{total} war points** to the score (+{bonus_pct}% pack bonus)"
        + (f"\n{war_line}" if war_line else "")
        + ("\n\n" + "\n".join(strain_lines) if strain_lines else "")
    )
    db.set_collab_patrol_status(patrol_id, "done", result_text=result_text)
    return build_collab_patrol_embed(patrol_id), None


def resolve_collab_patrol(patrol_id: int) -> tuple[discord.Embed | None, str | None]:
    patrol = db.get_collab_patrol(patrol_id)
    if not patrol or patrol["status"] != "open":
        return None, "this party is not open."
    members = db.get_collab_patrol_members(patrol_id)
    if len(members) < COLLAB_PATROL_MIN_WOLVES:
        return None, f"need at least **{COLLAB_PATROL_MIN_WOLVES}** scouts to set out."
    users = _party_users(patrol_id)
    if len(users) < COLLAB_PATROL_MIN_WOLVES:
        return None, "not enough valid scouts on the party."

    if _is_trail(patrol):
        return resolve_collab_trail(patrol_id)
    if _is_war_patrol(patrol):
        return resolve_collab_war_patrol(patrol_id)
    return resolve_collab_survey(patrol_id)


def try_set_out_collab_patrol(patrol_id: int) -> tuple[discord.Embed | None, str | None, int | None]:
    patrol = db.get_collab_patrol(patrol_id)
    if not patrol or patrol["status"] != "open":
        return None, "this party is not open.", None
    members = db.get_collab_patrol_members(patrol_id)
    if len(members) < COLLAB_PATROL_MIN_WOLVES:
        return None, f"need at least **{COLLAB_PATROL_MIN_WOLVES}** scouts to set out.", None

    users = _party_users(patrol_id)
    leader = db.get_user_by_id(patrol["leader_wolf_id"])
    if not leader or len(users) < COLLAB_PATROL_MIN_WOLVES:
        return None, "not enough valid scouts on the party.", None

    trail = _is_trail(patrol)
    war = _is_war_patrol(patrol)
    guild_id = patrol["guild_id"]
    channel_id = patrol["channel_id"]
    party_note = f"pack {'war patrol' if war else 'trail' if trail else 'patrol'}: {_party_names(patrol_id)}"
    slot = "war patrols" if war else "trails" if trail else "surveys"

    if war:
        embed, err = resolve_collab_patrol(patrol_id)
        return embed, err, None

    ambush = maybe_start_activity_ambush(
        leader,
        guild_id=guild_id,
        channel_id=channel_id,
        activity="collab_patrol",
    )
    if ambush:
        enc_id, template_key, flavor = ambush
        db.set_encounter_collab_patrol(enc_id, patrol_id)
        db.set_collab_patrol_status(patrol_id, "encounter")
        embed = ambush_embed(template_key, flavor, leader, activity="collab_patrol")
        embed.set_footer(
            text=f"{party_note} · ~{COLLAB_PATROL_AMBUSH_CHANCE}% ambush · win to finish · flee keeps {slot}"
        )
        from engine.collab_combat import enroll_collab_party_in_encounter

        enroll_collab_party_in_encounter(enc_id, users, leader_wolf_id=patrol["leader_wolf_id"])
        return embed, None, enc_id

    embed, err = resolve_collab_patrol(patrol_id)
    return embed, err, None


def complete_collab_patrol_ambush(patrol_id: int, enc_id: int) -> discord.Embed | None:
    enc = db.get_encounter(enc_id)
    if not enc or int(enc["collab_patrol_id"] or 0) != patrol_id:
        return None
    if enc["ambush_finalized"] if "ambush_finalized" in enc.keys() else False:
        return None
    patrol = db.get_collab_patrol(patrol_id)
    if not patrol or patrol["status"] != "encounter":
        return None

    from engine.ambush_activity import AMBUSH_WIN_BONES, _ambush_won

    if not _ambush_won(enc_id):
        return None

    patrol = db.get_collab_patrol(patrol_id)
    trail = _is_trail(patrol)
    users = _party_users(patrol_id)
    if not users:
        return None

    gross = random.randint(*AMBUSH_WIN_BONES) + (len(users) - 1) * 2

    with db.get_db() as conn:
        conn.execute(
            "UPDATE combat_encounters SET ambush_finalized = 1 WHERE id = ?",
            (enc_id,),
        )

    note = (
        "the trail party drove off the ambush and finished the cold read."
        if trail
        else "the patrol drove off the ambush and finished the border sweep."
    )
    if trail:
        embed = payout_collab_trail(patrol_id, fixed_base=gross, encounter_note=note)
    else:
        embed = payout_collab_survey(patrol_id, fixed_base=gross, encounter_note=note, standing_delta=1)
    db.end_encounter(enc_id)
    return embed
