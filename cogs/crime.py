"""Top-level /crime — individual theft, wolf-pack den raids, and cat-clan camp raids."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, choice_label
from utils.replies import reply_ephemeral
from utils.wolf_autocomplete import make_member_wolf_autocomplete


_wolf_name_autocomplete = make_member_wolf_autocomplete("target_wolf")

async def _other_wolf_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    from utils.embeds import choice_label
    active = db.get_user(interaction.user.id)
    if not active:
        return []
    choices = []
    for wolf in db.list_user_wolves(interaction.user.id):
        if wolf['id'] == active['id']:
            continue
        name = wolf['wolf_name']
        if current and current.lower() not in name.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(name), value=name))
    return choices[:25]

def _resolve_own_wolf(discord_id: int, name: str):
    rows = db.list_user_wolves(discord_id)
    return next((w for w in rows if w['wolf_name'].lower() == name.strip().lower()), None)

async def _crime_target_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    from config import GREAT_PACKS
    from engine.cat_clans import KNOWN_CAT_CLANS

    choices: list[app_commands.Choice[str]] = []
    for name in KNOWN_CAT_CLANS:
        if current and current.lower() not in name.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(f'{name} (cat clan)'), value=name))
    for _key, info in GREAT_PACKS.items():
        label = f"{info['name']} (wolf pack)"
        if current and current.lower() not in label.lower() and current.lower() not in _key:
            continue
        choices.append(app_commands.Choice(name=choice_label(label), value=info['name']))
    return choices[:25]


class Crime(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='crime', description='petty theft or pocket-picking; or raid a rival wolf-pack den / cat-clan camp.')
    @app_commands.describe(
        target_wolf='wolf to pick a pocket from (individual crime; omit for a generic petty score)',
        wolf_name="specific wolf from that player's roster",
        own_wolf='your other wolf to pick from (multi-wolf players)',
        target='wolf pack or cat clan to raid (raid only; pick from autocomplete)',
        raid_type='what to steal from a den or camp (raid only; treasury = bones, wolf packs only)',
        scene='optional rp scene note',
        staff='flag for staff to weave your rp scene',
    )
    @app_commands.choices(raid_type=[
        app_commands.Choice(name='treasury / bones (packs) or camp scraps (clans)', value='bones'),
        app_commands.Choice(name='food reserve', value='food'),
        app_commands.Choice(name='herb store', value='herbs'),
        app_commands.Choice(name='toy store / amusement', value='amusement'),
    ])
    @app_commands.autocomplete(target=_crime_target_autocomplete, own_wolf=_other_wolf_autocomplete, wolf_name=_wolf_name_autocomplete)
    async def crime(
        self,
        interaction: discord.Interaction,
        target_wolf: discord.Member | None = None,
        wolf_name: str | None = None,
        own_wolf: str | None = None,
        target: str | None = None,
        raid_type: str = 'food',
        scene: str | None = None,
        staff: bool = False,
    ) -> None:
        if (target_wolf or own_wolf) and target:
            await interaction.response.send_message(
                embed=howlbert_embed('Pick One', 'Use **target_wolf**/**own_wolf** for a pick-pocket or **target** for a den/camp raid — not both.', color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        if target_wolf and own_wolf:
            await interaction.response.send_message(
                embed=howlbert_embed('Pick One', 'Use **target_wolf** or **own_wolf**; not both.', color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return

        if target:
            await self._raid(interaction, target=target, raid_type=raid_type, scene=scene, staff=staff)
            return

        from engine.activities import try_crime
        if own_wolf:
            victim_row = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not victim_row:
                await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', 'No wolf with that name on your account. Check `/wolves`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            active = db.get_user(interaction.user.id)
            if active and victim_row['id'] == active['id']:
                await interaction.response.send_message(embed=howlbert_embed('Same Wolf', 'Switch active wolf with `/switchwolf`, or pick a different `own_wolf`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            embed = try_crime(interaction, victim_row=victim_row, scene=scene, staff=staff)
        elif target_wolf and wolf_name:
            victim_row = db.find_user_wolf(target_wolf.id, wolf_name)
            if not victim_row:
                await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', db.explain_wolf_not_found(target_wolf.id, wolf_name, player_label=target_wolf.display_name), color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            embed = try_crime(interaction, victim_row=victim_row, scene=scene, staff=staff)
        else:
            embed = try_crime(interaction, target_wolf=target_wolf, scene=scene, staff=staff)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _raid(
        self,
        interaction: discord.Interaction,
        *,
        target: str,
        raid_type: str,
        scene: str | None,
        staff: bool,
    ) -> None:
        from engine.wolf_pack_pacts import is_wolf_pack_target

        wolf_target = is_wolf_pack_target(target)

        if wolf_target:
            if raid_type not in ('bones', 'food', 'herbs', 'amusement'):
                raid_type = 'bones'
            from config import GREAT_PACKS
            from engine.activities import try_crime

            gp_key = next(
                (k for k, info in GREAT_PACKS.items() if target.strip().lower() in (k, info['name'].lower())),
                None,
            )
            if not gp_key:
                await interaction.response.send_message(
                    embed=howlbert_embed('unknown pack', 'pick a rival great pack from the autocomplete.', color=ERROR_COLOR),
                    ephemeral=reply_ephemeral(),
                )
                return
            embed = try_crime(interaction, target_pack=gp_key, raid_type=raid_type, scene=scene, staff=staff)
            if embed:
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        user = db.get_user(interaction.user.id)
        if not user or not user['pack_id']:
            await interaction.response.send_message(
                embed=howlbert_embed('no pack', 'join a great pack to raid a clan camp.', color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        pack = db.get_pack(user['pack_id'])
        if not pack:
            await interaction.response.send_message(
                embed=howlbert_embed('pack not found', 'your pack record is missing.', color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        if not interaction.guild:
            await interaction.response.send_message(
                embed=howlbert_embed('server only', 'use this in a server.', color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        from engine.cat_pacts import raid_cat_clan
        world = db.get_world(interaction.guild.id)
        ok, msg = raid_cat_clan(user, pack, guild_id=interaction.guild.id, clan_name=target, raid_type=raid_type, day=world['day_number'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('raid successful' if ok else 'caught at the border', msg, color=color)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Crime(bot))
