import json

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from engine.character import attr_modifier
from engine.combat import format_attack, overlay_fighter_hp, resolve_attack, resolve_maneuver, roll_initiative
from engine.bestiary import (
    BESTIARY_NPCS,
    HAZARD_TOPICS,
    format_npc_summary,
    npc_hp,
    stats_for_fighter,
)
from engine.combat_guide import COMBAT_GUIDE_TOPICS, COMBAT_MANEUVERS, MANEUVER_DETAIL
from engine.combat_status import (
    apply_crit_status_effects,
    apply_fumble_status_effects,
    apply_maneuver_pin_effects,
    attack_target_block,
    clear_attack_disadvantage,
    format_combat_flags,
    parse_combat_flags,
    release_pin_states,
)
from engine.conditions import add_injury, injury_roll_label, parse_injuries
from engine.combat_injuries import apply_injury_to_list, injury_label, resolve_player_injury_key
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from utils.combat_views import make_combat_view, COMBAT_DYNAMIC_ITEMS
from engine.role_restrictions import young_wolf_block
from engine.combat_display import fighter_name, is_npc_fighter as _is_npc, current_fighter_for_enc, assign_npc_display_name
from engine.hunt_combat import try_complete_hunt_prey_victory
from engine.combat_prey import try_grant_combat_kill_carcass
from engine.ambush_activity import ambush_victory_embed
from engine.border_combat import try_complete_border_victory
from engine.infractions import apply_yield_caught, yield_caught_standing


async def _combat_reply(interaction: discord.Interaction, **kwargs) -> None:
    """Send combat UI response; works whether or not the interaction was deferred."""
    if interaction.response.is_done():
        await interaction.followup.send(**kwargs)
    else:
        await interaction.response.send_message(**kwargs)


def _yield_embed_parts(user, name: str, hp_line: str, outcome: str) -> tuple[str, str, int]:
    """Build title, body, and embed color for a yield outcome."""
    if outcome == "ended":
        title = "Combat Over"
        body = (
            f"**{name}** yields ({hp_line}).\n"
            "With no opponents left, the encounter ends."
        )
        color = SUCCESS_COLOR
    else:
        title = "Yielded"
        body = f"**{name}** yields and backs out ({hp_line} saved to profile)."
        color = SUCCESS_COLOR

    expulsion, caught_flavor = apply_yield_caught(user)
    if caught_flavor:
        body += (
            f"\n\n**Caught yielding**; {caught_flavor}\n"
            f"Standing **{yield_caught_standing()}**."
        )
        color = ERROR_COLOR
    if expulsion:
        body += f"\n\n{expulsion}"

    return title, body, color


async def finish_attack_turn(
    interaction: discord.Interaction,
    bot: commands.Bot,
    enc_id: int,
    body: str,
    hit: bool,
    defender_f,
    new_hp: int,
    *,
    title: str = "Attack",
) -> None:
    db.advance_combat_turn(enc_id)
    db.clear_combat_target(interaction.user.id, enc_id)
    enc = db.get_active_encounter(interaction.channel_id)
    embed = howlbert_embed(title, body, color=SUCCESS_COLOR if hit else ERROR_COLOR)
    embed.add_field(name="Target HP", value=f"{new_hp}/{defender_f['max_hp']}", inline=True)
    embed.set_footer(text=_turn_footer_static(enc, bot) if enc else "Combat ended")

    if new_hp == 0:
        kill_note = try_grant_combat_kill_carcass(enc_id, interaction.user.id, defender_f)
        if kill_note:
            embed.add_field(name="Fresh-kill", value=kill_note, inline=False)

    victory_embed = None
    if new_hp == 0 and _is_npc(defender_f) and interaction.channel:
        victory_embed = await try_complete_hunt_prey_victory(bot, interaction.channel, enc_id)
        if not victory_embed:
            victory_embed = ambush_victory_embed(enc_id)
        if not victory_embed:
            victory_embed = await try_complete_border_victory(bot, interaction.channel, enc_id)

    if victory_embed and interaction.channel:
        enc_row = db.get_encounter(enc_id)
        if enc_row:
            hunt_id = (
                int(enc_row["collab_hunt_id"])
                if "collab_hunt_id" in enc_row.keys() and enc_row["collab_hunt_id"]
                else 0
            )
            patrol_id = (
                int(enc_row["collab_patrol_id"])
                if "collab_patrol_id" in enc_row.keys() and enc_row["collab_patrol_id"]
                else 0
            )
            if hunt_id:
                from engine.collab_ui import post_collab_hunt_prey_pile, refresh_collab_hunt_post

                await post_collab_hunt_prey_pile(bot, interaction.channel, hunt_id)
                await refresh_collab_hunt_post(bot, hunt_id)
            elif patrol_id:
                from engine.collab_ui import refresh_collab_patrol_post

                await refresh_collab_patrol_post(bot, patrol_id)

    view = make_combat_view(enc_id, bot) if enc and enc["status"] == "active" else None
    if victory_embed:
        await _combat_reply(interaction, embed=victory_embed)
        if view:
            await interaction.followup.send(embed=embed, view=view)
    else:
        await _combat_reply(interaction, embed=embed, view=view)


async def execute_npc_attack(
    interaction: discord.Interaction,
    bot: commands.Bot,
    enc_id: int,
    target_id: int,
) -> bool:
    """
    Resolve the active NPC's attack against a player wolf.
    Returns True if the interaction was answered, False if caller should respond.
    """
    if not interaction.response.is_done():
        await interaction.response.defer()

    enc = db.get_encounter(enc_id)
    if not enc or enc["status"] != "active":
        await _combat_reply(
            interaction,
            embed=howlbert_embed("No Active Combat", color=ERROR_COLOR),
            ephemeral=True,
        )
        return True

    if not db.player_in_encounter(enc_id, interaction.user.id):
        await _combat_reply(
            interaction,
            embed=howlbert_embed(
                "Not In Combat",
                "You must be in this encounter to run NPC turns.",
                color=ERROR_COLOR,
            ),
            ephemeral=True,
        )
        return True

    current = current_fighter_for_enc(enc_id)
    if not current or not _is_npc(current):
        name = fighter_name(current, bot) if current else "Unknown"
        await _combat_reply(
            interaction,
            embed=howlbert_embed(
                "Not NPC Turn",
                f"It's **{name}**'s turn; use the combat panel or `/combat attack`.",
                color=ERROR_COLOR,
            ),
            ephemeral=True,
        )
        return True
    if current["hp"] <= 0:
        await _combat_reply(
            interaction,
            embed=howlbert_embed("NPC Down", "That NPC is already defeated.", color=ERROR_COLOR),
            ephemeral=True,
        )
        return True

    defender_f = db.get_combat_fighter(enc_id, target_id)
    if not defender_f or _is_npc(defender_f):
        await _combat_reply(
            interaction,
            embed=howlbert_embed(
                "Invalid Target",
                "NPCs attack player wolves; pick a wolf from the list.",
                color=ERROR_COLOR,
            ),
            ephemeral=True,
        )
        return True
    if defender_f["id"] == current["id"]:
        await _combat_reply(
            interaction,
            embed=howlbert_embed("Invalid Target", "An NPC cannot attack itself.", color=ERROR_COLOR),
            ephemeral=True,
        )
        return True

    att_name = current["npc_name"]
    npc_stats = stats_for_fighter(current)
    atk_profile = npc_stats.get("npc_attack_profile")
    npc_action = atk_profile["type"] if atk_profile else "bite"
    try:
        body, new_hp, hit = _apply_attack_result(
            defender_f, npc_action, npc_stats, att_name, attacker_f=current
        )
    except ValueError:
        await _combat_reply(
            interaction,
            embed=howlbert_embed("Invalid Target", color=ERROR_COLOR),
            ephemeral=True,
        )
        return True

    await finish_attack_turn(interaction, bot, enc_id, body, hit, defender_f, new_hp)
    return True


def _apply_attack_result(
    defender_f,
    action: str,
    attacker_stats,
    att_name: str,
    *,
    maneuver_key: str | None = None,
    attacker_f=None,
    allow_free_counter: bool = True,
) -> tuple[str, int, bool]:
    """Resolve one attack and update DB. Returns (body text, new_hp, hit)."""
    if _is_npc(defender_f):
        defender_stats = stats_for_fighter(defender_f)
        def_name = defender_f["npc_name"]
    else:
        defender_stats = db.get_user(defender_f["discord_id"])
        if not defender_stats:
            raise ValueError("invalid_target")
        def_name = defender_stats["wolf_name"]

    defender_stats = overlay_fighter_hp(defender_stats, defender_f)

    if attacker_f and defender_f:
        reach_block = attack_target_block(
            attacker_f,
            defender_f,
            maneuver_key=maneuver_key,
        )
        if reach_block:
            label = COMBAT_MANEUVERS[maneuver_key]["name"] if maneuver_key else action.title()
            blocked = {
                "attack_name": label,
                "hit": False,
                "crit": False,
                "fumble": False,
                "blocked": True,
                "block_reason": reach_block,
                "attacker_roll": 0,
                "attacker_mod": 0,
                "attacker_total": 0,
                "defender_roll": 0,
                "defender_mod": 0,
                "defender_total": 0,
                "damage": 0,
                "extra": "",
            }
            body = format_attack(blocked, att_name, def_name)
            return body, defender_f["hp"], False

    result = (
        resolve_maneuver(
            attacker_stats,
            defender_stats,
            maneuver_key,
            attacker_f=attacker_f,
            defender_f=defender_f,
        )
        if maneuver_key
        else resolve_attack(
            attacker_stats,
            defender_stats,
            action,
            attacker_f=attacker_f,
            defender_f=defender_f,
        )
    )
    if result.get("blocked"):
        body = format_attack(result, att_name, def_name)
        return body, defender_f["hp"], False

    new_hp = max(0, defender_f["hp"] - result["damage"])
    db.update_fighter_hp(defender_f["id"], new_hp)

    injury_note = ""
    status_note = ""
    if defender_f["id"]:
        crit_msg = apply_crit_status_effects(defender_f["id"], result.get("crit_effect"))
        if crit_msg:
            status_note += f"\n{crit_msg}"
    if attacker_f and attacker_f["id"]:
        clear_attack_disadvantage(attacker_f["id"])
        fumble_msg = apply_fumble_status_effects(
            attacker_f["id"], result.get("fumble_effect")
        )
        if fumble_msg:
            status_note += f"\n{fumble_msg}"

    if maneuver_key and attacker_f and defender_f:
        pin_msg = apply_maneuver_pin_effects(
            attacker_f,
            defender_f,
            maneuver_key,
            hit=result["hit"],
            defender_name=def_name,
        )
        if pin_msg:
            status_note += f"\n{pin_msg}"

    if not _is_npc(defender_f):
        db.sync_fighter_hp_to_user(defender_f["discord_id"], new_hp)
        if new_hp == 0:
            db.enter_dying_state(defender_f["discord_id"])
        if result.get("crit") or new_hp == 0:
            max_hp = int(defender_stats.get("max_hp") or defender_f["max_hp"] or 1)
            inj_key = resolve_player_injury_key(
                maneuver_key=maneuver_key,
                crit=bool(result.get("crit")),
                hit=bool(result.get("hit")),
                new_hp=new_hp,
                max_hp=max_hp,
            )
            if inj_key:
                injuries_raw = (
                    defender_stats["active_injuries"]
                    if "active_injuries" in defender_stats
                    else None
                )
                injuries = parse_injuries(injuries_raw)
                injuries = apply_injury_to_list(injuries, inj_key)
                db.set_user_conditions(
                    defender_f["discord_id"],
                    active_injuries=json.dumps(injuries),
                )
                wolf_id = (
                    defender_f["wolf_id"]
                    if defender_f and "wolf_id" in defender_f.keys() and defender_f["wolf_id"]
                    else defender_stats["id"]
                )
                enc = db.get_encounter(defender_f["encounter_id"])
                if enc and wolf_id:
                    world = db.get_world(enc["guild_id"])
                    db.record_injury_since(wolf_id, inj_key, world["day_number"])
                injury_note = f"\n**Injury:** {injury_label(inj_key)}"
        if new_hp == 0:
            from engine.chronic_conditions import try_near_death_mental_trauma

            trauma = try_near_death_mental_trauma(defender_stats)
            if trauma:
                injury_note += f"\n**Mind fracture:** {trauma}"
            injury_note += f"\n**{def_name}** is **dying**; use `/deathsaves`."
            release_pin_states(defender_f["id"], defender_f["encounter_id"])
        elif result.get("hit") and attacker_f:
            from engine.chronic_conditions import try_combat_bite_disease

            bite_note = try_combat_bite_disease(
                defender_stats,
                attacker_f,
                action=action,
                maneuver_key=maneuver_key,
                hit=True,
            )
            if bite_note:
                injury_note += f"\n**Exposure:** {bite_note}"
    elif new_hp == 0:
        injury_note = f"\n**{def_name}** is defeated."
        release_pin_states(defender_f["id"], defender_f["encounter_id"])

    if (
        attacker_f
        and not _is_npc(attacker_f)
        and result.get("fumble_self_damage", 0) > 0
    ):
        self_dmg = result["fumble_self_damage"]
        att_hp = max(0, attacker_f["hp"] - self_dmg)
        db.update_fighter_hp(attacker_f["id"], att_hp)
        db.sync_fighter_hp_to_user(attacker_f["discord_id"], att_hp)
        injury_note += f"\n**{att_name}** bites their tongue; **{self_dmg}** damage."

    if (
        allow_free_counter
        and result.get("fumble_effect") == 1
        and attacker_f
        and defender_f["hp"] > 0
        and attacker_f["hp"] > 0
    ):
        if _is_npc(defender_f):
            counter_stats = stats_for_fighter(defender_f)
            counter_att_name = defender_f["npc_name"]
        else:
            counter_stats = db.get_user(defender_f["discord_id"])
            counter_att_name = counter_stats["wolf_name"] if counter_stats else def_name
        counter_body, counter_hp, _ = _apply_attack_result(
            attacker_f,
            "claw",
            counter_stats,
            counter_att_name,
            attacker_f=defender_f,
            allow_free_counter=False,
        )
        injury_note += f"\n\n**Free counterattack!** {counter_body}"

    body = format_attack(result, att_name, def_name) + status_note + injury_note
    return body, new_hp, result["hit"]


async def handle_combat_button(
    interaction: discord.Interaction,
    enc_id: int,
    bot: commands.Bot,
    action: str,
) -> None:
    if not interaction.response.is_done():
        await interaction.response.defer()

    enc = db.get_encounter(enc_id)
    if not enc or enc["status"] != "active":
        await _combat_reply(
            interaction,
            embed=howlbert_embed("No Active Combat", color=ERROR_COLOR),
            ephemeral=True,
        )
        return

    user = db.get_user(interaction.user.id)
    if not user:
        await _combat_reply(
            interaction,
            embed=howlbert_embed("Not Registered", color=ERROR_COLOR),
            ephemeral=True,
        )
        return

    if action == "yield":
        fighter = db.resolve_player_fighter(enc_id, interaction.user.id)
        if not fighter:
            await _combat_reply(
                interaction,
                embed=howlbert_embed("Not In Combat", color=ERROR_COLOR),
                ephemeral=True,
            )
            return
        name = db.get_user_by_id(fighter["wolf_id"])["wolf_name"] if fighter["wolf_id"] else user["wolf_name"]
        hp_line = f"{fighter['hp']}/{fighter['max_hp']} HP"
        outcome = db.yield_fighter(enc_id, fighter["id"])
        title, body, color = _yield_embed_parts(user, name, hp_line, outcome)
        if outcome == "ended":
            await _combat_reply(interaction, embed=howlbert_embed(title, body, color=color))
            return
        enc = db.get_encounter(enc_id)
        if enc and enc["status"] == "active":
            body += f"\n\n{_turn_footer_static(enc, bot)}"
        view = make_combat_view(enc_id, bot) if enc and enc["status"] == "active" else None
        await _combat_reply(
            interaction,
            embed=howlbert_embed(title, body, color=color),
            view=view,
        )
        return

    target_id = db.get_combat_target(interaction.user.id, enc_id)
    if not target_id:
        await _combat_reply(interaction, content="Pick a target from the menu first.", ephemeral=True)
        return

    attacker_f = db.resolve_player_fighter(enc_id, interaction.user.id)
    defender_f = db.get_combat_fighter(enc_id, target_id)
    if not attacker_f or not defender_f:
        await _combat_reply(
            interaction,
            embed=howlbert_embed("Not In Combat", color=ERROR_COLOR),
            ephemeral=True,
        )
        return
    if attacker_f["id"] == defender_f["id"]:
        await _combat_reply(
            interaction,
            embed=howlbert_embed("Invalid Target", "You cannot attack yourself.", color=ERROR_COLOR),
            ephemeral=True,
        )
        return
    if attacker_f["hp"] <= 0:
        await _combat_reply(
            interaction,
            embed=howlbert_embed("Cannot Act", "You are down.", color=ERROR_COLOR),
            ephemeral=True,
        )
        return

    current = _current_fighter_static(enc)
    if not current or current["id"] != attacker_f["id"]:
        if current and _is_npc(current):
            msg = (
                f"It's **{fighter_name(current, bot)}**'s turn. "
                "Use the **NPC attack** menu on the combat panel or `/combat npcattack`."
            )
        else:
            msg = "Not your turn; wait for initiative."
        await _combat_reply(
            interaction,
            embed=howlbert_embed("Not Your Turn", msg, color=ERROR_COLOR),
            ephemeral=True,
        )
        return

    try:
        body, new_hp, hit = _apply_attack_result(
            defender_f,
            action if not action.startswith("maneuver:") else "claw",
            user,
            user["wolf_name"],
            maneuver_key=action.split(":", 1)[1] if action.startswith("maneuver:") else None,
            attacker_f=attacker_f,
        )
    except ValueError:
        await _combat_reply(
            interaction,
            embed=howlbert_embed("Invalid Target", color=ERROR_COLOR),
            ephemeral=True,
        )
        return

    title = "Maneuver" if action.startswith("maneuver:") else "Attack"
    await finish_attack_turn(
        interaction, bot, enc_id, body, hit, defender_f, new_hp, title=title
    )


def _current_fighter_static(enc):
    return current_fighter_for_enc(enc["id"])


def _turn_footer_static(enc, bot: commands.Bot) -> str:
    current = _current_fighter_static(enc)
    if not current:
        return f"Round {enc['round']}"
    name = fighter_name(current, bot)
    if _is_npc(current):
        return f"Round {enc['round']}; {name}'s turn · pick a wolf from the NPC attack menu"
    return f"Round {enc['round']}; {name}'s turn"


def _recruitment_block(enc) -> tuple[str, str] | None:
    """Return (title, body) when join/npc cannot proceed; None if recruiting is open."""
    if not enc:
        return (
            "No Recruitment",
            "No open encounter here. Start one with `/combat start`.",
        )
    if enc["status"] == "active":
        return (
            "Combat Underway",
            "This fight has already begun; new wolves can't join mid-encounter.\n"
            "Use `/combat status` for turn order, or `/combat end` to close it.",
        )
    if enc["status"] != "recruiting":
        return (
            "No Recruitment",
            f"Encounter status is **{enc['status']}**; can't join.",
        )
    return None


def _existing_encounter_message(enc) -> tuple[str, str]:
    if enc["status"] == "recruiting":
        return (
            "Recruitment Open",
            "An encounter is recruiting here. Others can `/combat join` or `/combat npc`.\n"
            "When ready: `/combat begin`.",
        )
    return (
        "Combat Active",
        "A fight is already **active** in this channel.\n"
        "Use `/combat status` for turn order, or `/combat end` to close it.",
    )


class Combat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.add_dynamic_items(*COMBAT_DYNAMIC_ITEMS)

    combat = app_commands.Group(name="combat", description="Basil combat; initiative, bite, claw.")

    async def _require_user(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        return user

    async def _require_combat_participant(self, interaction: discord.Interaction, enc):
        user = await self._require_user(interaction)
        if not user:
            return None, None
        fighter = db.resolve_player_fighter(enc["id"], interaction.user.id)
        if not fighter:
            embed = howlbert_embed(
                "Not In Combat",
                "You must be in this encounter to run NPC turns.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None, None
        return user, fighter

    def _current_fighter(self, enc):
        return _current_fighter_static(enc)

    def _turn_footer(self, enc) -> str:
        return _turn_footer_static(enc, self.bot)

    async def _finish_attack_turn(
        self,
        interaction: discord.Interaction,
        enc,
        body: str,
        hit: bool,
        defender_f,
        new_hp: int,
        *,
        title: str = "Attack",
    ):
        await finish_attack_turn(
            interaction, self.bot, enc["id"], body, hit, defender_f, new_hp, title=title
        )

    @combat.command(name="start", description="Start a combat encounter in this channel.")
    async def combat_start(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return
        block = young_wolf_block(user, action="combat")
        if block:
            await interaction.response.send_message(
                embed=howlbert_embed("Too Young", block, color=ERROR_COLOR),
                ephemeral=True,
            )
            return
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        await interaction.response.defer()

        existing = db.get_active_encounter(interaction.channel_id)
        if existing:
            title, body = _existing_encounter_message(existing)
            embed = howlbert_embed(title, body, color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        enc_id = db.create_encounter(
            interaction.guild.id, interaction.channel_id, interaction.user.id
        )
        db.add_combat_fighter(
            enc_id,
            discord_id=interaction.user.id,
            wolf_id=user["id"],
            hp=user["hp"],
            max_hp=user["max_hp"],
        )
        embed = howlbert_embed(
            "Combat Started",
            f"**{user['wolf_name']}** enters the fray.\n"
            "Others: `/combat join` · Random ambush: `/combat encounter`\n"
            "Story fight: `/combat npc` · When ready: `/combat begin`",
            color=SUCCESS_COLOR,
        )
        await interaction.followup.send(embed=embed)

    @combat.command(
        name="encounter",
        description="Force a random wilderness ambush (90 min cooldown between ambushes).",
    )
    async def combat_encounter(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return
        block = young_wolf_block(user, action="combat")
        if block:
            await interaction.response.send_message(
                embed=howlbert_embed("Too Young", block, color=ERROR_COLOR),
                ephemeral=True,
            )
            return
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        await interaction.response.defer()

        existing = db.get_active_encounter(interaction.channel_id)
        if existing:
            title, body = _existing_encounter_message(existing)
            embed = howlbert_embed(title, body, color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        from engine.wild_encounters import (
            ambush_embed,
            can_trigger_wild_encounter,
            start_wild_encounter,
            wild_encounter_cooldown_minutes,
        )

        if not can_trigger_wild_encounter(user, interaction.channel_id):
            wait = wild_encounter_cooldown_minutes(user)
            if db.get_active_encounter(interaction.channel_id):
                msg = "A fight is already active in this channel."
            elif wait:
                msg = f"Recent ambush; wait **{wait}** min before forcing another encounter."
            else:
                msg = "Cannot start an encounter here right now."
            embed = howlbert_embed("Not Ready", msg, color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        enc_id, template_key, flavor = start_wild_encounter(
            user,
            guild_id=interaction.guild.id,
            channel_id=interaction.channel_id,
        )
        embed = ambush_embed(template_key, flavor)
        enc = db.get_encounter(enc_id)
        embed.set_footer(text=self._turn_footer(enc))
        view = make_combat_view(enc_id, self.bot)
        await interaction.followup.send(embed=embed, view=view)

    @combat.command(name="join", description="Join the active combat in this channel.")
    async def combat_join(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return

        block = young_wolf_block(user, action="combat")
        if block:
            await interaction.response.send_message(
                embed=howlbert_embed("Too Young", block, color=ERROR_COLOR),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        enc = db.get_active_encounter(interaction.channel_id)
        blocked = _recruitment_block(enc)
        if blocked:
            title, body = blocked
            embed = howlbert_embed(title, body, color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if db.player_in_encounter(enc["id"], interaction.user.id):
            embed = howlbert_embed("Already In", "You're already in this fight.", color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        fighter_id = db.add_combat_fighter(
            enc["id"],
            discord_id=interaction.user.id,
            wolf_id=user["id"],
            hp=user["hp"],
            max_hp=user["max_hp"],
        )
        world = db.get_world(interaction.guild.id)
        from engine.role_features import apply_scout_combat_hidden

        if apply_scout_combat_hidden(
            user,
            fighter_id,
            day=world["day_number"],
            weather_key=world["weather"],
        ):
            hidden_note = " **Unseen Paw**; hidden in the obscured air."
        else:
            hidden_note = ""
        embed = howlbert_embed(
            "Joined Combat",
            f"**{user['wolf_name']}** joins (HP {user['hp']}/{user['max_hp']}).{hidden_note}",
            color=SUCCESS_COLOR,
        )
        await interaction.followup.send(embed=embed)

    @combat.command(name="npc", description="Add a predator, hearth-hound, or clan cat from the bestiary (during recruitment).")
    @app_commands.describe(
        category="Threat category",
        threat="Creature to add",
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="Predators & Threats", value="predators"),
            app_commands.Choice(name="Hearth-hounds (Twoleg hounds)", value="dogs"),
            app_commands.Choice(name="Clan Cats & Rivals", value="cats"),
        ],
        threat=[
            app_commands.Choice(name=data["name"], value=key)
            for key, data in BESTIARY_NPCS.items()
        ],
    )
    async def combat_npc(
        self,
        interaction: discord.Interaction,
        threat: str,
        category: str | None = None,
    ):
        await interaction.response.defer(ephemeral=True)

        enc = db.get_active_encounter(interaction.channel_id)
        blocked = _recruitment_block(enc)
        if blocked:
            title, body = blocked
            embed = howlbert_embed(title, body, color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        template = BESTIARY_NPCS.get(threat)
        if not template:
            embed = howlbert_embed("Unknown Threat", color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        if category and template["category"] != category:
            embed = howlbert_embed(
                "Wrong Category",
                f"**{template['name']}** is not in that category.",
                color=ERROR_COLOR,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        hp = npc_hp(template)
        display_name = assign_npc_display_name(enc["id"], threat, template["name"])
        db.add_combat_fighter(
            enc["id"],
            npc_name=display_name,
            npc_template=threat,
            hp=hp,
            max_hp=hp,
        )
        footer = "Cats · hearth-hounds · fox · badger · /combat hazard for Two-Legs and traps."
        user = db.get_user(interaction.user.id)
        if user and user["pack_id"] and template["category"] == "cats":
            pacts = db.list_active_cat_pacts(interaction.guild.id, user["pack_id"])
            if pacts:
                footer = (
                    f"⚠️ Active cat pact(s); RP fights may break trust. "
                    f"See `/pack pact action:View`."
                )
        embed = howlbert_embed(
            f"{display_name} Enters",
            format_npc_summary(threat),
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text=footer)
        await interaction.followup.send(embed=embed)

    @combat.command(
        name="hazard",
        description="Human-world hazards; Two-Legs, Thunderpath, traps, fences.",
    )
    @app_commands.describe(topic="Hazard reference", ally="Packmate to encourage past fire")
    @app_commands.choices(
        topic=[
            app_commands.Choice(name="Humans (Two-Legs)", value="humans"),
            app_commands.Choice(name="Thunderpath (Road)", value="thunderpath"),
            app_commands.Choice(name="Traps", value="traps"),
            app_commands.Choice(name="Two-Leg Nests (Buildings)", value="twoleg_nests"),
            app_commands.Choice(name="Fences", value="fences"),
            app_commands.Choice(name="Fire fear (campfire/torch)", value="fire"),
            app_commands.Choice(name="Wildfire fear + smoke", value="wildfire"),
            app_commands.Choice(name="Stand against fire (Intimidation)", value="fire_stand"),
            app_commands.Choice(name="Encourage ally past fire", value="fire_encourage"),
        ]
    )
    async def combat_hazard(
        self, interaction: discord.Interaction, topic: str, ally: discord.Member | None = None
    ):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        if topic in ("fire", "wildfire", "fire_stand", "fire_encourage"):
            await self._fire_hazard(interaction, user, topic, ally)
            return
        title, body = HAZARD_TOPICS.get(topic, HAZARD_TOPICS["humans"])
        embed = howlbert_embed(title, body)
        embed.set_footer(text="Use /roll for opposed checks · Safe Roll cannot be used in combat.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _fire_hazard(
        self,
        interaction: discord.Interaction,
        user,
        topic: str,
        ally: discord.Member | None,
    ):
        from engine.fire_fear import (
            encourage_through_fire,
            fire_fear_save,
            stand_against_fire,
            wildfire_heat_save,
        )

        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day = world["day_number"] if world else 1

        if topic == "fire_encourage":
            if not ally:
                await interaction.response.send_message(
                    "Pick an **ally** packmate to encourage past the flame.",
                    ephemeral=True,
                )
                return
            target = db.get_user(ally.id)
            if not target:
                await interaction.response.send_message("Ally is not registered.", ephemeral=True)
                return
            ok, body = encourage_through_fire(user, target, day=day)
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            embed = howlbert_embed("Encouragement", body, color=color)
            await interaction.response.send_message(embed=embed)
            return

        if topic == "fire":
            ok, body = fire_fear_save(user, wildfire=False, day=day)
        elif topic == "wildfire":
            ok, body = fire_fear_save(user, wildfire=True, day=day)
            if not ok:
                heat_ok, heat_body, _ = wildfire_heat_save(user, day=day)
                body += "\n\n" + heat_body
                ok = heat_ok
        else:
            ok, body = stand_against_fire(user, day=day)

        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed("Fear of Fire", body, color=color)
        embed.set_footer(text="Guard: one failed save reroll per sunrise · /vitals action:condition")
        await interaction.response.send_message(embed=embed)

    @combat.command(name="begin", description="Roll initiative and begin turns.")
    async def combat_begin(self, interaction: discord.Interaction):
        enc = db.get_active_encounter(interaction.channel_id)
        if not enc or enc["status"] != "recruiting":
            embed = howlbert_embed("Cannot Begin", "No recruiting encounter in this channel.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        fighters = db.get_combat_fighters(enc["id"])
        if len(fighters) < 2:
            embed = howlbert_embed(
                "Need Opponents",
                "At least 2 fighters required (use `/combat join` or `/combat npc`).",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        rolls = []
        for f in fighters:
            if f["discord_id"]:
                user = db.get_user(f["discord_id"])
                die, mod, total = roll_initiative(user)
            else:
                stats = stats_for_fighter(f)
                die = __import__("random").randint(1, 20)
                mod = attr_modifier(stats["attr_dex"])
                total = die + mod
            db.set_fighter_initiative(f["id"], total)
            rolls.append((f["id"], fighter_name(f, self.bot), die, mod, total))

        fighters = db.get_combat_fighters(enc["id"])
        order = [f["id"] for f in fighters]
        db.start_combat_encounter(enc["id"], order)

        lines = [f"**{name}**; {die} + {mod} = **{total}**" for _, name, die, mod, total in rolls]
        enc = db.get_active_encounter(interaction.channel_id)
        embed = howlbert_embed("Initiative", "\n".join(lines), color=SUCCESS_COLOR)
        embed.set_footer(text=self._turn_footer(enc))
        view = make_combat_view(enc["id"], self.bot)
        await interaction.followup.send(embed=embed, view=view)

    @combat.command(name="attack", description="Bite or claw the target on your turn.")
    @app_commands.describe(
        target="Fighter to attack; wolves and NPCs in this encounter",
        action="Attack type",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Bite (STR vs DEX)", value="bite"),
            app_commands.Choice(name="Claw (DEX vs DEX)", value="claw"),
        ]
    )
    async def combat_attack(
        self,
        interaction: discord.Interaction,
        target: str,
        action: str = "bite",
    ):
        user = await self._require_user(interaction)
        if not user:
            return

        enc = db.get_active_encounter(interaction.channel_id)
        if not enc or enc["status"] != "active":
            embed = howlbert_embed("No Active Combat", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            target_id = int(target)
        except ValueError:
            embed = howlbert_embed(
                "Invalid Target",
                "Pick a target from the autocomplete list.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        attacker_f = db.resolve_player_fighter(enc["id"], interaction.user.id)
        defender_f = db.get_combat_fighter(enc["id"], target_id)
        if not attacker_f or not defender_f:
            embed = howlbert_embed("Not In Combat", "Both fighters must be in this encounter.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if attacker_f["id"] == defender_f["id"]:
            embed = howlbert_embed("Invalid Target", "You cannot attack yourself.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if attacker_f["hp"] <= 0:
            embed = howlbert_embed("Cannot Act", "You are down.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        current = self._current_fighter(enc)
        if not current or current["id"] != attacker_f["id"]:
            if current and _is_npc(current):
                embed = howlbert_embed(
                    "NPC Turn",
                    f"It's **{fighter_name(current, self.bot)}**'s turn. Use `/combat npcattack`.",
                    color=ERROR_COLOR,
                )
            else:
                embed = howlbert_embed("Not Your Turn", "Wait for your turn in initiative.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            body, new_hp, hit = _apply_attack_result(
                defender_f, action, user, user["wolf_name"], attacker_f=attacker_f
            )
        except ValueError:
            embed = howlbert_embed("Invalid Target", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await self._finish_attack_turn(interaction, enc, body, hit, defender_f, new_hp)

    @combat.command(
        name="npcattack",
        description="Run the active NPC's natural attack (anyone in the fight can GM this).",
    )
    @app_commands.describe(target="Wolf for the NPC to attack")
    async def combat_npcattack(
        self,
        interaction: discord.Interaction,
        target: str,
    ):
        enc = db.get_active_encounter(interaction.channel_id)
        if not enc or enc["status"] != "active":
            embed = howlbert_embed("No Active Combat", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            target_id = int(target)
        except ValueError:
            embed = howlbert_embed(
                "Invalid Target",
                "Pick a wolf from the autocomplete list.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await execute_npc_attack(interaction, self.bot, enc["id"], target_id)

    @combat.command(
        name="yield",
        description="Surrender and leave the fight; may cost standing if caught (35%).",
    )
    async def combat_yield(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return

        enc = db.get_active_encounter(interaction.channel_id)
        if not enc or enc["status"] not in ("recruiting", "active"):
            embed = howlbert_embed("No Combat", "There is no fight to yield from.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        fighter = db.resolve_player_fighter(enc["id"], interaction.user.id)
        if not fighter:
            embed = howlbert_embed("Not In Combat", "You are not in this encounter.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        name = user["wolf_name"]
        hp_line = f"{fighter['hp']}/{fighter['max_hp']} HP"
        outcome = db.yield_fighter(enc["id"], fighter["id"])
        title, body, color = _yield_embed_parts(user, name, hp_line, outcome)

        if outcome == "ended":
            await interaction.response.send_message(
                embed=howlbert_embed(title, body, color=color),
            )
            return

        enc = db.get_active_encounter(interaction.channel_id)
        if enc and enc["status"] == "active":
            body += f"\n\n{self._turn_footer(enc)}"
        embed = howlbert_embed(title, body, color=color)
        await interaction.response.send_message(embed=embed)

    @combat_attack.autocomplete("target")
    async def combat_attack_target_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        if not interaction.channel_id:
            return []
        enc = db.get_active_encounter(interaction.channel_id)
        if not enc or enc["status"] != "active":
            return []
        attacker = db.resolve_player_fighter(enc["id"], interaction.user.id)
        if not attacker:
            return []
        return self._target_choices(
            enc, exclude_id=attacker["id"], current=current, players_only=False
        )

    @combat_npcattack.autocomplete("target")
    async def combat_npcattack_target_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        enc = db.get_active_encounter(interaction.channel_id)
        if not enc or enc["status"] != "active":
            return []
        if not db.player_in_encounter(enc["id"], interaction.user.id):
            return []
        current_npc = self._current_fighter(enc)
        exclude = current_npc["id"] if current_npc and _is_npc(current_npc) else None
        return self._target_choices(enc, exclude_id=exclude, current=current, players_only=True)

    def _target_choices(
        self, enc, *, exclude_id: int | None, current: str, players_only: bool
    ) -> list[app_commands.Choice[str]]:
        needle = current.lower()
        choices: list[app_commands.Choice[str]] = []
        for fighter in db.get_combat_fighters(enc["id"]):
            if exclude_id and fighter["id"] == exclude_id:
                continue
            if players_only and _is_npc(fighter):
                continue
            if fighter["hp"] <= 0:
                continue
            name = fighter_name(fighter, self.bot)
            if needle and needle not in name.lower():
                continue
            label = f"{name} ({fighter['hp']}/{fighter['max_hp']} HP)"
            choices.append(app_commands.Choice(name=label[:100], value=str(fighter["id"])))
        return choices[:25]

    @combat.command(name="status", description="Show combat HP and turn order.")
    async def combat_status(self, interaction: discord.Interaction):
        await interaction.response.defer()

        enc = db.get_active_encounter(interaction.channel_id)
        if not enc:
            embed = howlbert_embed("No Combat", "No encounter in this channel.", color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        fighters = db.get_combat_fighters(enc["id"])
        lines = []
        for f in fighters:
            line = (
                f"**{fighter_name(f, self.bot)}**; {f['hp']}/{f['max_hp']} HP"
                + (f" (init {f['initiative']})" if f["initiative"] else "")
            )
            flags = format_combat_flags(
                parse_combat_flags(f),
                fighter_id=f["id"],
                encounter_id=enc["id"],
            )
            if flags:
                line += f" · _{flags}_"
            lines.append(line)
        footer = f"Status: {enc['status']}"
        if enc["status"] == "active":
            footer = self._turn_footer(enc)
        embed = howlbert_embed("Combat Status", "\n".join(lines) or "No fighters.")
        embed.set_footer(text=footer)
        view = make_combat_view(enc["id"], self.bot) if enc["status"] == "active" else None
        await interaction.followup.send(embed=embed, view=view)

    @combat.command(name="guide", description="Wolf combat fundamentals, vulnerable areas, and maneuvers.")
    @app_commands.describe(topic="Topic to read")
    @app_commands.choices(
        topic=[
            app_commands.Choice(name="Overview", value="overview"),
            app_commands.Choice(name="Vulnerable Areas", value="vulnerable"),
            app_commands.Choice(name="Stance & Balance", value="stance"),
            app_commands.Choice(name="Awareness", value="awareness"),
            app_commands.Choice(name="Defense", value="defense"),
            app_commands.Choice(name="Energy & Stamina", value="stamina"),
            app_commands.Choice(name="Bestiary (cats, fox, badger)", value="bestiary"),
            app_commands.Choice(name="Maneuvers List", value="maneuvers"),
            app_commands.Choice(name="Injury Table (1d10)", value="injuries"),
            app_commands.Choice(name="Critical Hits & Fumbles", value="crits"),
            app_commands.Choice(name="⚠️ Lethal Techniques", value="killing"),
        ]
    )
    async def combat_guide(self, interaction: discord.Interaction, topic: str = "overview"):
        title, body = COMBAT_GUIDE_TOPICS.get(topic, COMBAT_GUIDE_TOPICS["overview"])
        embed = howlbert_embed(title, body)
        embed.set_footer(text="/combat maneuver · /combat guide topic:maneuvers")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @combat.command(name="maneuver", description="Use a special maneuver on your turn.")
    @app_commands.describe(
        target="Fighter to target",
        maneuver="Combat maneuver",
    )
    @app_commands.choices(
        maneuver=[
            app_commands.Choice(name=m["name"], value=m["key"])
            for m in sorted(COMBAT_MANEUVERS.values(), key=lambda x: x["name"])[:25]
        ]
    )
    async def combat_maneuver(
        self,
        interaction: discord.Interaction,
        target: str,
        maneuver: str,
    ):
        user = await self._require_user(interaction)
        if not user:
            return

        enc = db.get_active_encounter(interaction.channel_id)
        if not enc or enc["status"] != "active":
            embed = howlbert_embed("No Active Combat", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            target_id = int(target)
        except ValueError:
            embed = howlbert_embed("Invalid Target", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        attacker_f = db.resolve_player_fighter(enc["id"], interaction.user.id)
        defender_f = db.get_combat_fighter(enc["id"], target_id)
        if not attacker_f or not defender_f:
            embed = howlbert_embed("Not In Combat", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if attacker_f["id"] == defender_f["id"]:
            embed = howlbert_embed("Invalid Target", "You cannot target yourself.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if attacker_f["hp"] <= 0:
            embed = howlbert_embed("Cannot Act", "You are down.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        current = self._current_fighter(enc)
        if not current or current["id"] != attacker_f["id"]:
            embed = howlbert_embed("Not Your Turn", "Wait for your turn in initiative.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            body, new_hp, hit = _apply_attack_result(
                defender_f,
                "claw",
                user,
                user["wolf_name"],
                maneuver_key=maneuver,
                attacker_f=attacker_f,
            )
        except ValueError:
            embed = howlbert_embed("Unknown Maneuver", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        detail = MANEUVER_DETAIL.get(maneuver, "")
        if detail:
            body = f"{body}\n\n_{detail}_"
        await self._finish_attack_turn(
            interaction, enc, body, hit, defender_f, new_hp, title="Maneuver"
        )

    @combat_maneuver.autocomplete("target")
    async def combat_maneuver_target_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        enc = db.get_active_encounter(interaction.channel_id)
        if not enc or enc["status"] != "active":
            return []
        attacker = db.resolve_player_fighter(enc["id"], interaction.user.id)
        if not attacker:
            return []
        return self._target_choices(enc, exclude_id=attacker["id"], current=current, players_only=False)

    @combat.command(name="end", description="End combat and sync HP to profiles.")
    async def combat_end(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        enc = db.get_active_encounter(interaction.channel_id)
        if not enc:
            embed = howlbert_embed("No Combat", color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        db.end_encounter(enc["id"])
        embed = howlbert_embed(
            "Combat Ended",
            "HP synced to wolf profiles. Wounds and conditions persist.",
            color=SUCCESS_COLOR,
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Combat(bot))
