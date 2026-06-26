import discord
from discord import app_commands
from discord.ext import commands
import sqlite3

import database as db
from cogs.profile import PACK_CHOICES, _pack_display
from engine.attraction import BIRTH_SEX_LABELS, SEXUALITY_LABELS, SEXUALITY_OPTIONS, is_pup_age
from engine.aging import format_wolf_age, stage_for_age, stage_label
from engine.family import XP_PER_ROLE_FEATURE
from rpg_rules import ROLE_FEATURES, ROLE_LABELS
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from utils.notifications import try_dm_user
from utils.permissions import is_howlbert_admin


async def _wolfadmin_wolf_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    from_player = getattr(interaction.namespace, "from_player", None)
    player = from_player or getattr(interaction.namespace, "player", None)
    if not player:
        return []
    wolves = db.list_user_wolves(player.id)
    needle = current.lower()
    choices = []
    for row in wolves:
        name = row["wolf_name"]
        if needle and needle not in name.lower():
            continue
        choices.append(app_commands.Choice(name=name, value=name))
    return choices[:25]


def _wolf_not_found_embed(player: discord.User, wolf_name: str) -> discord.Embed:
    body = db.explain_wolf_not_found(
        player.id,
        wolf_name,
        player_label=player.display_name,
    )
    return howlbert_embed("Wolf Not Found", body, color=ERROR_COLOR)


class WolfAdmin(commands.Cog):
    wolfadmin = app_commands.Group(
        name="wolfadmin",
        description="Admin; create or reassign wolf profiles for players.",
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _require_admin(self, interaction: discord.Interaction) -> bool:
        if is_howlbert_admin(interaction):
            return True
        embed = howlbert_embed("Denied", "Admins only.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return False

    @wolfadmin.command(
        name="assign",
        description="Create a wolf and assign it to a player.",
    )
    @app_commands.describe(
        player="Discord member who will own this wolf",
        name="Wolf name",
        pack="Great Pack or loner",
        birth_sex="Birth sex",
        sexuality="Attraction",
        role="Wolf role (stats and skills)",
        starting_age="Starting age in moons, 0-120 (optional)",
        set_active="Make this their active wolf immediately",
    )
    @app_commands.choices(
        pack=PACK_CHOICES,
        birth_sex=[
            app_commands.Choice(name="Female", value="female"),
            app_commands.Choice(name="Male", value="male"),
            app_commands.Choice(name="Intersex", value="intersex"),
            app_commands.Choice(name="Nonbinary", value="nonbinary"),
        ],
        sexuality=[
            app_commands.Choice(name=name, value=value)
            for name, value in SEXUALITY_OPTIONS
        ],
        role=[
            app_commands.Choice(name=ROLE_LABELS[key], value=key)
            for key in ROLE_LABELS
        ],
    )
    async def wolfadmin_assign(
        self,
        interaction: discord.Interaction,
        player: discord.User,
        name: str,
        pack: str,
        birth_sex: str,
        sexuality: str,
        role: str = "hunter",
        starting_age: app_commands.Range[int, 0, 120] | None = None,
        set_active: bool = True,
    ):
        if not await self._require_admin(interaction):
            return

        if player.bot:
            embed = howlbert_embed(
                "Invalid Player",
                "Bots cannot own wolves.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        wolf_name, name_err = db.validate_wolf_name_available(name, label="Wolf names")
        if name_err:
            title = "Name Taken" if "already taken" in name_err else "Invalid Name"
            embed = howlbert_embed(title, name_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        try:
            wolf_id = db.register_user(
                player.id,
                wolf_name,
                pack,
                wolf_role=role,
                birth_sex=birth_sex,
                sexuality=sexuality,
                age_months=starting_age,
                set_active=set_active,
            )
        except ValueError as exc:
            msg = str(exc)
            title = (
                "Name Taken"
                if "already taken" in msg or "reserved" in msg
                else "Invalid Name"
            )
            embed = howlbert_embed(title, msg, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        user = db.get_user_by_id(wolf_id)
        embed = howlbert_embed("Wolf Assigned", color=SUCCESS_COLOR)
        embed.add_field(name="Player", value=player.mention, inline=True)
        embed.add_field(name="Wolf", value=wolf_name, inline=True)
        embed.add_field(
            name="Active",
            value="Yes" if set_active else "No (use `/switchwolf`)",
            inline=True,
        )
        embed.add_field(
            name="Birth Sex",
            value=BIRTH_SEX_LABELS.get(birth_sex, birth_sex.title()),
            inline=True,
        )
        embed.add_field(
            name="Sexuality",
            value=SEXUALITY_LABELS.get(sexuality, sexuality.title()),
            inline=True,
        )
        embed.add_field(name="Role", value=ROLE_LABELS.get(user["wolf_role"], user["wolf_role"].title()), inline=True)
        age_mo = user["age_months"] if "age_months" in user.keys() else 24
        embed.add_field(
            name="Age",
            value=f"{format_wolf_age(age_mo)} ({stage_label(stage_for_age(age_mo))})",
            inline=True,
        )
        embed.add_field(name="Pack", value=_pack_display(pack), inline=False)
        await interaction.response.send_message(embed=embed)

    @wolfadmin.command(
        name="transfer",
        description="Move an existing wolf from one player to another.",
    )
    @app_commands.describe(
        from_player="Current owner",
        wolf_name="Which wolf to move",
        to_player="New owner",
        set_active="Make this their active wolf immediately",
    )
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_transfer(
        self,
        interaction: discord.Interaction,
        from_player: discord.User,
        wolf_name: str,
        to_player: discord.User,
        set_active: bool = True,
    ):
        if not await self._require_admin(interaction):
            return

        if to_player.bot:
            embed = howlbert_embed(
                "Invalid Player",
                "Bots cannot own wolves.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        wolf = db.find_user_wolf(from_player.id, wolf_name)
        if not wolf:
            await interaction.response.send_message(
                embed=_wolf_not_found_embed(from_player, wolf_name),
                ephemeral=reply_ephemeral(),
            )
            return

        if from_player.id == to_player.id:
            embed = howlbert_embed(
                "Same Player",
                "Pick a different owner to transfer to.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        result = db.reassign_wolf_owner(
            wolf["id"],
            to_player.id,
            set_active=set_active,
        )
        if result == "same_owner":
            embed = howlbert_embed(
                "Same Player",
                "That wolf already belongs to the target player.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        embed = howlbert_embed("Wolf Transferred", color=SUCCESS_COLOR)
        embed.add_field(name="Wolf", value=wolf["wolf_name"], inline=True)
        embed.add_field(name="From", value=from_player.mention, inline=True)
        embed.add_field(name="To", value=to_player.mention, inline=True)
        embed.add_field(
            name="Active for new owner",
            value="Yes" if set_active else "No",
            inline=True,
        )
        await interaction.response.send_message(embed=embed)

    @wolfadmin.command(
        name="list",
        description="List all wolves registered to a player.",
    )
    @app_commands.describe(player="Discord member to inspect")
    async def wolfadmin_list(
        self,
        interaction: discord.Interaction,
        player: discord.User,
    ):
        if not await self._require_admin(interaction):
            return

        await interaction.response.defer()

        wolves = db.list_user_wolves(player.id)
        if not wolves:
            embed = howlbert_embed(
                "No Wolves",
                f"**{player.display_name}** has no registered wolves.",
                color=ERROR_COLOR,
            )
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())
            return

        active_id = db.get_active_wolf_id(player.id)
        lines = []
        for row in wolves:
            marker = " *(active)*" if row["id"] == active_id else ""
            role_key = row["wolf_role"] if row["wolf_role"] else "hunter"
            role = ROLE_LABELS.get(role_key, str(role_key).title())
            lines.append(f"**{row['wolf_name']}**; {role} (id `{row['id']}`){marker}")

        embed = howlbert_embed(
            f"Wolves: {player.display_name}",
            "\n".join(lines),
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text=f"{len(wolves)} wolf(s) · Discord ID {player.id}")
        await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

    @wolfadmin.command(
        name="possess",
        description="Steer another player's wolf (all commands act as that character).",
    )
    @app_commands.describe(
        player="Wolf owner",
        wolf_name="Which wolf (defaults to their active wolf)",
    )
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_possess(
        self,
        interaction: discord.Interaction,
        player: discord.User,
        wolf_name: str | None = None,
    ):
        if not await self._require_admin(interaction):
            return
        if player.bot:
            embed = howlbert_embed("Invalid Player", "Bots cannot own wolves.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        wolf, err = db.resolve_possessed_wolf(interaction.user.id, player.id, wolf_name)
        if err:
            embed = howlbert_embed("Wolf Not Found", err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        ok, msg = db.set_admin_possess(interaction.user.id, wolf["id"])
        if not ok:
            embed = howlbert_embed("Cannot Possess", msg, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        embed = howlbert_embed("Possessing Wolf", msg, color=SUCCESS_COLOR)
        embed.set_footer(text="Use /wolfadmin release when done · /profile shows their sheet")
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @wolfadmin.command(
        name="release",
        description="Stop steering another player's wolf and return to your own.",
    )
    async def wolfadmin_release(self, interaction: discord.Interaction):
        if not await self._require_admin(interaction):
            return
        ok, msg = db.clear_admin_possess(interaction.user.id)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = "Released" if ok else "Not Possessing"
        embed = howlbert_embed(title, msg, color=color)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @wolfadmin.command(
        name="setage",
        description="Set a wolf's age in moons (0-120).",
    )
    @app_commands.describe(
        player="Wolf owner",
        moons="New age in moons",
        wolf_name="Which wolf (defaults to their active wolf)",
    )
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_setage(
        self,
        interaction: discord.Interaction,
        player: discord.User,
        moons: app_commands.Range[int, 0, 120],
        wolf_name: str | None = None,
    ):
        if not await self._require_admin(interaction):
            return

        if wolf_name:
            wolf = db.find_user_wolf(player.id, wolf_name)
            if not wolf:
                await interaction.response.send_message(
                    embed=_wolf_not_found_embed(player, wolf_name),
                    ephemeral=reply_ephemeral(),
                )
                return
        else:
            wolf = db.get_user(player.id)
            if not wolf:
                embed = howlbert_embed(
                    "No Wolf",
                    f"**{player.display_name}** has no active wolf.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return

        result = db.set_wolf_age_moons(wolf["id"], moons)
        if not result:
            embed = howlbert_embed("Error", "Could not update age.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        embed = howlbert_embed("Age Updated", color=SUCCESS_COLOR)
        embed.description = (
            f"**{wolf['wolf_name']}** ({player.mention}); "
            f"**{format_wolf_age(result['old_age'])}** → **{format_wolf_age(result['new_age'])}** "
            f"({stage_label(stage_for_age(result['new_age']))})."
        )
        if result["new_role"] != result["old_role"]:
            embed.add_field(
                name="Role",
                value=(
                    f"{ROLE_LABELS.get(result['old_role'], result['old_role'])} → "
                    f"**{ROLE_LABELS.get(result['new_role'], result['new_role'])}**"
                ),
                inline=False,
            )
        for note in result["notes"]:
            embed.add_field(name="Milestone", value=note, inline=False)
        if is_pup_age(result["new_age"]):
            embed.set_footer(text="Pup age; sexuality set to Too young / none.")
        else:
            embed.set_footer(text="Each `/rollover` still ages every wolf by 1 moon.")
        await interaction.response.send_message(embed=embed)

    async def _resolve_pending_role_feature(
        self,
        interaction: discord.Interaction,
        *,
        request_id: int | None,
        player: discord.User | None,
        wolf_name: str | None,
    ) -> sqlite3.Row | None:
        if request_id is not None:
            row = db.get_pending_role_feature(request_id)
            if not row:
                embed = howlbert_embed(
                    "Not Found",
                    f"No request with id `{request_id}`.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return None
            return row

        if player and wolf_name:
            wolf = db.find_user_wolf(player.id, wolf_name)
            if not wolf:
                await interaction.response.send_message(
                    embed=_wolf_not_found_embed(player, wolf_name),
                    ephemeral=reply_ephemeral(),
                )
                return None
            row = db.get_open_pending_for_wolf(wolf["id"])
            if not row:
                embed = howlbert_embed(
                    "No Pending Request",
                    f"No open role-feature request for **{wolf['wolf_name']}**.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return None
            return row

        embed = howlbert_embed(
            "Missing Parameters",
            "Provide **request_id** or both **player** and **wolf_name**.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return None

    @wolfadmin.command(
        name="featurepending",
        description="List open bonus role-feature requests awaiting approval.",
    )
    async def wolfadmin_featurepending(self, interaction: discord.Interaction):
        if not await self._require_admin(interaction):
            return

        guild_id = interaction.guild.id if interaction.guild else 0
        rows = db.list_open_pending_role_features(guild_id)
        if not rows:
            embed = howlbert_embed(
                "No Pending Requests",
                "No role-feature requests are waiting for approval.",
                color=SUCCESS_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        lines = []
        for row in rows:
            role_key = row["role_feature"]
            role_label = ROLE_LABELS.get(role_key, role_key.title())
            lines.append(
                f"`{row['id']}`; **{row['wolf_name']}** "
                f"(<@{row['discord_id']}>); **{role_label}**"
            )

        embed = howlbert_embed(
            "Pending Role Features",
            "\n".join(lines),
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="Approve with /wolfadmin approvefeature")
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @wolfadmin.command(
        name="approvefeature",
        description="Approve a pending bonus role-feature request (spends 10 XP).",
    )
    @app_commands.describe(
        request_id="Pending request id (from featurepending)",
        player="Player who submitted the request",
        wolf_name="Wolf that requested the feature",
    )
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_approvefeature(
        self,
        interaction: discord.Interaction,
        request_id: int | None = None,
        player: discord.User | None = None,
        wolf_name: str | None = None,
    ):
        if not await self._require_admin(interaction):
            return

        row = await self._resolve_pending_role_feature(
            interaction,
            request_id=request_id,
            player=player,
            wolf_name=wolf_name,
        )
        if not row:
            return

        if row["status"] != "pending":
            embed = howlbert_embed(
                "Not Pending",
                f"Request `{row['id']}` is already **{row['status']}**.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        role_key = row["role_feature"]
        if role_key not in ROLE_FEATURES:
            embed = howlbert_embed(
                "Invalid Role",
                f"Request `{row['id']}` references unknown role **{role_key}**.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        wolf = db.get_user_by_id(row["wolf_id"])
        if not wolf:
            embed = howlbert_embed(
                "Wolf Missing",
                f"Wolf id `{row['wolf_id']}` no longer exists.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        existing_bonus = (
            wolf["bonus_role_feature"]
            if "bonus_role_feature" in wolf.keys() and wolf["bonus_role_feature"]
            else None
        )
        if existing_bonus == role_key:
            db.set_pending_role_feature_status(
                row["id"],
                "denied",
                resolved_by_discord_id=interaction.user.id,
            )
            embed = howlbert_embed(
                "Already Granted",
                f"**{wolf['wolf_name']}** already has this feature; request denied.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        account = db.get_account(row["discord_id"])
        xp_val = account["xp"] if "xp" in account.keys() else 0
        if xp_val < XP_PER_ROLE_FEATURE:
            embed = howlbert_embed(
                "Not Enough XP",
                f"<@{row['discord_id']}> only has **{xp_val}** XP (need {XP_PER_ROLE_FEATURE}).",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        if not db.spend_xp(row["discord_id"], XP_PER_ROLE_FEATURE):
            embed = howlbert_embed(
                "Spend Failed",
                "Could not deduct XP; request left pending.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        db.update_user(row["discord_id"], wolf_id=row["wolf_id"], bonus_role_feature=role_key)
        db.set_pending_role_feature_status(
            row["id"],
            "approved",
            resolved_by_discord_id=interaction.user.id,
        )

        role_label = ROLE_LABELS.get(role_key, role_key.title())
        embed = howlbert_embed(
            "Feature Approved",
            f"**{wolf['wolf_name']}** gained **{role_label}** bonus feature "
            f"({XP_PER_ROLE_FEATURE} XP spent from <@{row['discord_id']}>).",
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

        await try_dm_user(
            self.bot,
            row["discord_id"],
            embed=howlbert_embed(
                "Bonus Role Feature Approved",
                f"**{wolf['wolf_name']}** gained **{role_label}**:\n{ROLE_FEATURES[role_key]}",
                color=SUCCESS_COLOR,
            ),
        )

    @wolfadmin.command(
        name="denyfeature",
        description="Deny a pending bonus role-feature request (no XP spent).",
    )
    @app_commands.describe(
        request_id="Pending request id (from featurepending)",
        player="Player who submitted the request",
        wolf_name="Wolf that requested the feature",
    )
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_denyfeature(
        self,
        interaction: discord.Interaction,
        request_id: int | None = None,
        player: discord.User | None = None,
        wolf_name: str | None = None,
    ):
        if not await self._require_admin(interaction):
            return

        row = await self._resolve_pending_role_feature(
            interaction,
            request_id=request_id,
            player=player,
            wolf_name=wolf_name,
        )
        if not row:
            return

        if row["status"] != "pending":
            embed = howlbert_embed(
                "Not Pending",
                f"Request `{row['id']}` is already **{row['status']}**.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        db.set_pending_role_feature_status(
            row["id"],
            "denied",
            resolved_by_discord_id=interaction.user.id,
        )

        role_label = ROLE_LABELS.get(row["role_feature"], row["role_feature"].title())
        embed = howlbert_embed(
            "Feature Denied",
            f"Denied **{role_label}** for **{row['wolf_name']}** "
            f"(<@{row['discord_id']}>, id `{row['id']}`). No XP spent.",
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())


async def setup(bot: commands.Bot):
    await bot.add_cog(WolfAdmin(bot))
