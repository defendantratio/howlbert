"""`/rpprompt`; curated and community-suggested scene prompts."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from cogs.profile import PACK_CHOICES
from engine.rp_prompts import (
    MOOD_TAGS,
    add_prompt_direct,
    approve_prompt,
    list_pending,
    random_prompt,
    reject_prompt,
    submit_prompt,
)
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message
from utils.permissions import is_howlbert_admin
from utils.replies import reply_ephemeral

_MOOD_CHOICES = [app_commands.Choice(name=m, value=m) for m in MOOD_TAGS]


class RpPrompts(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _require_admin(self, interaction: discord.Interaction) -> bool:
        if is_howlbert_admin(interaction):
            return True
        embed = howlbert_embed('Denied', 'Admins only.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return False

    @app_commands.command(name='rpprompt', description='get a scene prompt, suggest one, or (admin) manage the prompt library.')
    @app_commands.describe(
        action='get, suggest, add (admin), pending (admin), approve (admin), or reject (admin)',
        pack='filter/tag by great pack, loner, or rogue',
        mood='filter/tag by tone',
        plot='pull from the book one: the blinking prompts for the current plot phase',
        text='the prompt text (suggest / add)',
        prompt_id='pending prompt id (approve / reject)',
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name='get a prompt', value='get'),
            app_commands.Choice(name='suggest a prompt', value='suggest'),
            app_commands.Choice(name='add a prompt (admin)', value='add'),
            app_commands.Choice(name='list pending suggestions (admin)', value='pending'),
            app_commands.Choice(name='approve a suggestion (admin)', value='approve'),
            app_commands.Choice(name='reject a suggestion (admin)', value='reject'),
        ],
        pack=PACK_CHOICES,
        mood=_MOOD_CHOICES,
    )
    async def rpprompt(
        self,
        interaction: discord.Interaction,
        action: str,
        pack: str | None = None,
        mood: str | None = None,
        plot: bool = False,
        text: str | None = None,
        prompt_id: int | None = None,
    ):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        if action == 'get':
            await self._get(interaction, pack, mood, plot)
        elif action == 'suggest':
            await self._suggest(interaction, text, pack, mood)
        elif action == 'add':
            await self._add(interaction, text, pack, mood)
        elif action == 'pending':
            await self._pending(interaction)
        elif action == 'approve':
            await self._approve(interaction, prompt_id)
        elif action == 'reject':
            await self._reject(interaction, prompt_id)
        else:
            await interaction.response.send_message(player_message('Pick a valid **action**.'), ephemeral=reply_ephemeral())

    async def _get(self, interaction: discord.Interaction, pack: str | None, mood: str | None, plot: bool):
        guild_id = interaction.guild.id
        plot_phase = None
        if plot:
            from engine.plot_blinking import plot_phase as current_plot_phase

            phase = current_plot_phase(guild_id)
            plot_phase = phase if phase > 0 else None
            if plot_phase is None:
                await interaction.response.send_message(
                    embed=howlbert_embed('No Active Plot', 'Book One: The Blinking isn\'t active on this server right now.', color=ERROR_COLOR),
                    ephemeral=reply_ephemeral(),
                )
                return
        prompt = random_prompt(guild_id, pack=pack, mood=mood, plot_phase=plot_phase)
        if not prompt:
            await interaction.response.send_message(
                embed=howlbert_embed('No Prompts', 'Nothing matches those filters yet; try fewer, or `/rpprompt action:suggest` one.', color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        footer_bits = []
        if pack:
            footer_bits.append(f'pack: {pack}')
        if mood or prompt.get('mood'):
            footer_bits.append(f"mood: {mood or prompt.get('mood')}")
        if plot_phase:
            footer_bits.append(f'book one: the blinking · phase {plot_phase}')
        if is_howlbert_admin(interaction):
            pending_count = len(list_pending(guild_id, limit=10_000))
            if pending_count:
                footer_bits.append(f'{pending_count} suggestion(s) pending review')
        embed = howlbert_embed('Scene Prompt', prompt['text'], color=SUCCESS_COLOR)
        if footer_bits:
            embed.set_footer(text=' · '.join(footer_bits))
        await interaction.response.send_message(embed=embed)

    async def _suggest(self, interaction: discord.Interaction, text: str | None, pack: str | None, mood: str | None):
        if not text:
            await interaction.response.send_message(player_message('Give the prompt **text** to suggest.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        ok, msg = submit_prompt(interaction.guild.id, interaction.user.id, text, pack=pack, mood=mood, day=world['day_number'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Prompt Suggestion', msg, color=color), ephemeral=reply_ephemeral())

    async def _add(self, interaction: discord.Interaction, text: str | None, pack: str | None, mood: str | None):
        if not await self._require_admin(interaction):
            return
        if not text:
            await interaction.response.send_message(player_message('Give the prompt **text** to add.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        ok, msg = add_prompt_direct(interaction.guild.id, interaction.user.id, text, pack=pack, mood=mood, day=world['day_number'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Prompt Added', msg, color=color), ephemeral=reply_ephemeral())

    async def _pending(self, interaction: discord.Interaction):
        if not await self._require_admin(interaction):
            return
        total = len(list_pending(interaction.guild.id, limit=10_000))
        rows = list_pending(interaction.guild.id)
        if not rows:
            await interaction.response.send_message(embed=howlbert_embed('Pending Prompts', 'No prompts awaiting review.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
            return
        lines = []
        for r in rows:
            tags = ' · '.join(t for t in (r['pack'], r['mood']) if t)
            tag_note = f" _({tags})_" if tags else ''
            lines.append(f"`#{r['id']}`{tag_note}: {r['text']}")
        embed = howlbert_embed('Pending Prompts', '\n'.join(lines), color=SUCCESS_COLOR)
        shown_note = f'showing {len(rows)} of {total} · ' if total > len(rows) else ''
        embed.set_footer(text=f"{shown_note}`/rpprompt action:approve prompt_id:#` · `action:reject prompt_id:#`")
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _approve(self, interaction: discord.Interaction, prompt_id: int | None):
        if not await self._require_admin(interaction):
            return
        if prompt_id is None:
            await interaction.response.send_message(player_message('Give the **prompt_id** to approve.'), ephemeral=reply_ephemeral())
            return
        ok, msg = approve_prompt(prompt_id, interaction.user.id)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Approve Prompt', msg, color=color), ephemeral=reply_ephemeral())

    async def _reject(self, interaction: discord.Interaction, prompt_id: int | None):
        if not await self._require_admin(interaction):
            return
        if prompt_id is None:
            await interaction.response.send_message(player_message('Give the **prompt_id** to reject.'), ephemeral=reply_ephemeral())
            return
        ok, msg = reject_prompt(prompt_id, interaction.user.id)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Reject Prompt', msg, color=color), ephemeral=reply_ephemeral())


async def setup(bot: commands.Bot):
    await bot.add_cog(RpPrompts(bot))
