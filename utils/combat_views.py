"""Persistent combat panel components (DynamicItem; survives bot restarts)."""

from __future__ import annotations

import discord
from discord import ui
from discord.ext import commands

import database as db
from engine.combat_display import current_fighter_for_enc, fighter_name, is_npc_fighter


def _target_options(enc_id: int, bot: commands.Bot) -> list[discord.SelectOption]:
    options: list[discord.SelectOption] = []
    for fighter in db.get_combat_fighters(enc_id):
        if fighter["hp"] <= 0:
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
        options = _target_options(enc_id, bot)
        super().__init__(
            ui.Select(
                placeholder="Pick a target…",
                options=options or [discord.SelectOption(label="No targets", value="0")],
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
                "No valid targets in this fight.", ephemeral=True
            )
            return
        db.set_combat_target(interaction.user.id, self.enc_id, tid)
        defender = db.get_combat_fighter(self.enc_id, tid)
        label = fighter_name(defender, self.bot) if defender else "target"
        await interaction.response.send_message(
            f"**{label}** locked. Choose **Bite**, **Claw**, or a **Maneuver**.",
            ephemeral=True,
        )


class CombatNpcAttackSelect(ui.DynamicItem, template=r"^fable_combat:(?P<enc_id>\d+):npcattack$"):
    """NPC turn; pick a wolf; the active NPC uses its natural attack immediately."""

    def __init__(self, enc_id: int, bot: commands.Bot, *, npc_name: str):
        options = _player_target_options(enc_id, bot)
        super().__init__(
            ui.Select(
                placeholder=f"{npc_name[:40]} attacks…",
                options=options or [discord.SelectOption(label="No wolves", value="0")],
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
                "No player wolves left to target.", ephemeral=True
            )
            return
        from cogs.combat import execute_npc_attack

        await execute_npc_attack(interaction, self.bot, self.enc_id, tid)


class CombatActionButton(ui.DynamicItem, template=r"^fable_combat:(?P<enc_id>\d+):(?P<action>bite|claw|yield)$"):
    def __init__(self, enc_id: int, action: str):
        labels = {"bite": "Bite", "claw": "Claw", "yield": "Yield"}
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
                placeholder="Maneuver (pick target first)…",
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

        if not db.get_combat_target(interaction.user.id, self.enc_id):
            await interaction.response.send_message(
                "Pick a **target** from the menu above first, then choose a maneuver.",
                ephemeral=True,
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
