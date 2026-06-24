"""Rebuild rpg.py with slim vitals only."""
from pathlib import Path

lines = Path("cogs/rpg.py").read_text(encoding="utf-8").splitlines()

# Find key anchors (0-indexed)
vitals_start = next(i for i, l in enumerate(lines) if 'name="vitals"' in l) - 1
sacred_start = next(i for i, l in enumerate(lines) if "async def _sacred_visit" in l)
condition_start = next(i for i, l in enumerate(lines) if "async def _condition" in l)
swim_end = next(i for i, l in enumerate(lines) if "async def _swim_therapy" in l)
swim_end = next(i for i, l in enumerate(lines[swim_end:], swim_end) if lines[i].strip() == "" or "quarantine" in lines[i]) 
# find line after swim method ends
swim_start = next(i for i, l in enumerate(lines) if "async def _swim_therapy" in l)
setup_start = next(i for i, l in enumerate(lines) if "async def setup" in l)

# swim method ends before quarantine @app_commands
quarantine_start = next(i for i, l in enumerate(lines) if 'name="quarantine"' in l)

header = """import discord
from discord import app_commands
from discord.ext import commands

import database as db
from rpg_rules import DC_TIERS, ROLE_LABELS, SKILLS
from engine.character import attr_modifier, parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from engine.shop_items import consume_item_by_key, has_item
from engine.role_features import can_use_role_reroll, has_any_role
from engine.role_privileges import HERB_HEAL_DAILY_LIMIT, herb_heal_limit_reached
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
"""

vitals_cmd = '''
    @app_commands.command(
        name="vitals",
        description="View conditions, rest, or swim therapy.",
    )
    @app_commands.describe(
        action="condition, rest, or swim",
        rest_type="Short or long rest (rest)",
        use_herb="Use comfrey for short rest healing (rest)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="View conditions", value="condition"),
            app_commands.Choice(name="Rest", value="rest"),
            app_commands.Choice(name="Swim therapy (river)", value="swim"),
        ],
        rest_type=[
            app_commands.Choice(name="Long rest (6-8 hours sleep)", value="long"),
            app_commands.Choice(name="Short rest (10-30 min)", value="short"),
        ],
    )
    async def vitals(
        self,
        interaction: discord.Interaction,
        action: str,
        rest_type: str = "long",
        use_herb: bool = False,
    ):
        if action == "condition":
            await self._condition(interaction)
        elif action == "rest":
            await self._rest(interaction, rest_type, use_herb)
        elif action == "swim":
            await self._swim_therapy(interaction)

'''

# class start through end of setstats (before old vitals)
class_start = next(i for i, l in enumerate(lines) if "class Rpg" in l)
pre_vitals = lines[class_start:vitals_start]

# handlers condition through swim
handlers = lines[condition_start:quarantine_start]

tail = lines[setup_start:]

out = header + "\n" + "\n".join(pre_vitals) + vitals_cmd + "\n".join(handlers) + "\n\n" + "\n".join(tail)
Path("cogs/rpg.py").write_text(out, encoding="utf-8")
print("rebuilt rpg.py", len(out.splitlines()), "lines")
