"""Persistent combat panel components (DynamicItem; survives bot restarts)."""

from __future__ import annotations

import discord
from discord import ui
from discord.ext import commands

import database as db
from utils.replies import reply_ephemeral
from utils.embeds import player_message
from engine.combat_display import current_fighter_for_enc, fighter_name, is_npc_fighter


def _attack_target_options(enc_id: int, bot: commands.Bot) -> list[discord.SelectOption]:
    """Living enemies for the wolf whose turn it is (never includes your own fighter)."""
    current = current_fighter_for_enc(enc_id)
    actor_id = current["id"] if current and not is_npc_fighter(current) else None
    actor_discord = current["discord_id"] if current and not is_npc_fighter(current) else None
    options: list[discord.SelectOption] = []
    for fighter in db.get_combat_fighters(enc_id):
        if fighter["hp"] <= 0:
            continue
        if actor_id and fighter["id"] == actor_id:
            continue
        if (
            actor_discord
            and fighter["discord_id"] == actor_discord
            and not is_npc_fighter(fighter)
        ):
            continue
        name = fighter_name(fighter, bot)
        options.append(
            discord.SelectOption(
                label=name[:100],
                value=str(fighter["id"]),
                description=f"{fighter['hp']}/{fighter['max_hp']} HP",
            )
        )
    return options[:25]


def _player_target_options(enc_id: int, bot: commands.Bot) -> list[discord.SelectOption]:
    options: list[discord.SelectOption] = []
    for fighter in db.get_combat_fighters(enc_id):
        if fighter["hp"] <= 0 or is_npc_fighter(fighter):
            continue
        name = fighter_name(fighter, bot)
        options.append(
            discord.SelectOption(
                label=name[:100],
                value=str(fighter["id"]),
                description=f"{fighter['hp']}/{fighter['max_hp']} HP",
            )
        )
    return options[:25]


class CombatTargetSelect(ui.DynamicItem, template=r"^fable_combat:(?P<enc_id>\d+):target$"):
    def __init__(self, enc_id: int, bot: commands.Bot):
        options = _attack_target_options(enc_id, bot)
        placeholder = "pick a target…"
        if len(options) == 1:
            placeholder = f"target: {options[0].label[:40]} (optional)"
        super().__init__(
            ui.Select(
                placeholder=placeholder,
                options=options or [discord.SelectOption(label="no targets", value="0")],
                min_values=1,
                max_values=1,
                custom_id=f"fable_combat:{enc_id}:target",
                disabled=not options,
            )
        )
        self.enc_id = enc_id
        self.bot = bot

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: ui.Item, match, /):
        return cls(int(match["enc_id"]), interaction.client)

    async def callback(self, interaction: discord.Interaction):
        tid = int(interaction.data["values"][0])
        if tid == 0:
            await interaction.response.send_message(
                player_message("no valid targets in this fight."), ephemeral=reply_ephemeral()
            )
            return
        attacker = db.resolve_player_fighter(self.enc_id, interaction.user.id)
        if attacker and tid == attacker["id"]:
            await interaction.response.send_message(
                player_message("you can't target yourself — pick an **enemy** from the menu."),
                ephemeral=reply_ephemeral(),
            )
            return
        db.set_combat_target(interaction.user.id, self.enc_id, tid)
        defender = db.get_combat_fighter(self.enc_id, tid)
        label = fighter_name(defender, self.bot) if defender else "target"
        await interaction.response.send_message(
            player_message(f"**{label}** locked. choose **bite**, **claw**, or a **maneuver**."),
            ephemeral=reply_ephemeral(),
        )


class CombatNpcAttackSelect(ui.DynamicItem, template=r"^fable_combat:(?P<enc_id>\d+):npcattack$"):
    """NPC turn; pick a wolf; the active NPC uses its natural attack immediately."""

    def __init__(self, enc_id: int, bot: commands.Bot, *, npc_name: str):
        options = _player_target_options(enc_id, bot)
        super().__init__(
            ui.Select(
                placeholder=f"{npc_name[:40]} attacks…",
                options=options or [discord.SelectOption(label="no wolves", value="0")],
                min_values=1,
                max_values=1,
                custom_id=f"fable_combat:{enc_id}:npcattack",
                disabled=not options,
            )
        )
        self.enc_id = enc_id
        self.bot = bot

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: ui.Item, match, /):
        enc_id = int(match["enc_id"])
        current = current_fighter_for_enc(enc_id)
        npc_name = current["npc_name"] if current and is_npc_fighter(current) else "NPC"
        return cls(enc_id, interaction.client, npc_name=npc_name)

    async def callback(self, interaction: discord.Interaction):
        tid = int(interaction.data["values"][0])
        if tid == 0:
            await interaction.response.send_message(
                player_message("no player wolves left to target."), ephemeral=reply_ephemeral()
            )
            return
        from cogs.combat import execute_npc_attack

        await execute_npc_attack(interaction, self.bot, self.enc_id, tid)


class CombatActionButton(ui.DynamicItem, template=r"^fable_combat:(?P<enc_id>\d+):(?P<action>bite|claw|yield)$"):
    def __init__(self, enc_id: int, action: str):
        labels = {"bite": "bite", "claw": "claw", "yield": "yield"}
        styles = {
            "bite": discord.ButtonStyle.danger,
            "claw": discord.ButtonStyle.primary,
            "yield": discord.ButtonStyle.secondary,
        }
        super().__init__(
            ui.Button(
                label=labels[action],
                style=styles[action],
                custom_id=f"fable_combat:{enc_id}:{action}",
            )
        )
        self.enc_id = enc_id
        self.action = action

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: ui.Item, match, /):
        return cls(int(match["enc_id"]), match["action"])

    async def callback(self, interaction: discord.Interaction):
        from cogs.combat import handle_combat_button

        await handle_combat_button(
            interaction, self.enc_id, interaction.client, self.action
        )


class CombatManeuverSelect(ui.DynamicItem, template=r"^fable_combat:(?P<enc_id>\d+):maneuver$"):
    def __init__(self, enc_id: int):
        from engine.combat_guide import COMBAT_MANEUVER_LIST

        maneuver_options = [
            discord.SelectOption(
                label=m["name"][:100],
                value=m["key"],
                description=m["summary"][:100],
            )
            for m in COMBAT_MANEUVER_LIST[:25]
        ]
        super().__init__(
            ui.Select(
                placeholder="maneuver…",
                options=maneuver_options,
                min_values=1,
                max_values=1,
                custom_id=f"fable_combat:{enc_id}:maneuver",
            )
        )
        self.enc_id = enc_id

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: ui.Item, match, /):
        return cls(int(match["enc_id"]))

    async def callback(self, interaction: discord.Interaction):
        from cogs.combat import handle_combat_button

        from engine.combat_display import pick_combat_target

        attacker = db.resolve_player_fighter(self.enc_id, interaction.user.id)
        if not attacker or not pick_combat_target(
            interaction.user.id, self.enc_id, attacker["id"]
        ):
            await interaction.response.send_message(
                player_message("pick a **target** from the menu above first, then choose a maneuver."),
                ephemeral=reply_ephemeral(),
            )
            return
        key = interaction.data["values"][0]
        await handle_combat_button(
            interaction, self.enc_id, interaction.client, f"maneuver:{key}"
        )


COMBAT_DYNAMIC_ITEMS = (
    CombatTargetSelect,
    CombatNpcAttackSelect,
    CombatActionButton,
    CombatManeuverSelect,
)


def _make_player_turn_view(enc_id: int, bot: commands.Bot) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(CombatTargetSelect(enc_id, bot))
    view.add_item(CombatActionButton(enc_id, "bite"))
    view.add_item(CombatActionButton(enc_id, "claw"))
    view.add_item(CombatActionButton(enc_id, "yield"))
    view.add_item(CombatManeuverSelect(enc_id))
    return view


def _make_npc_turn_view(enc_id: int, bot: commands.Bot, npc_name: str) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(CombatNpcAttackSelect(enc_id, bot, npc_name=npc_name))
    return view


def make_combat_view(enc_id: int, bot: commands.Bot) -> discord.ui.View | None:
    enc = db.get_encounter(enc_id)
    if not enc or enc["status"] != "active":
        return None

    current = current_fighter_for_enc(enc_id)
    if current and is_npc_fighter(current):
        return _make_npc_turn_view(enc_id, bot, current["npc_name"])

    return _make_player_turn_view(enc_id, bot)


async def refresh_combat_panel(
    interaction: discord.Interaction,
    enc_id: int,
    bot: commands.Bot,
) -> None:
    """Sync the message's buttons with whose turn it is (avoids stale bite menus on NPC turns)."""
    if not interaction.message:
        return
    enc = db.get_encounter(enc_id)
    if not enc or enc["status"] != "active":
        try:
            await interaction.message.edit(view=discord.ui.View())
        except discord.HTTPException:
            pass
        return
    view = make_combat_view(enc_id, bot)
    try:
        await interaction.message.edit(view=view or discord.ui.View())
    except discord.HTTPException:
        pass
