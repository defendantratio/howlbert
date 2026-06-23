"""Wolf bonds; friendships, rivalries, kin, mentors, and found families."""

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from engine.bonds import BOND_LABELS, FAMILY_ROLE_LABELS, format_bonds_embed_body
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed


async def _other_wolf_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    active = db.get_user(interaction.user.id)
    if not active:
        return []
    choices = []
    for wolf in db.list_user_wolves(interaction.user.id):
        if wolf["id"] == active["id"]:
            continue
        name = wolf["wolf_name"]
        if current and current.lower() not in name.lower():
            continue
        choices.append(app_commands.Choice(name=name[:100], value=name))
    return choices[:25]


def _resolve_own_wolf(discord_id: int, name: str):
    rows = db.list_user_wolves(discord_id)
    return next((w for w in rows if w["wolf_name"].lower() == name.strip().lower()), None)


def _resolve_subject(interaction: discord.Interaction, own_wolf: str | None):
    if own_wolf:
        subject = _resolve_own_wolf(interaction.user.id, own_wolf)
        if not subject:
            return None, "No wolf with that name on your account. Check `/wolves`."
        return subject, None
    subject = db.get_user(interaction.user.id)
    if not subject:
        return None, "__not_registered__"
    return subject, None


def _resolve_bond_target(
    subject,
    interaction: discord.Interaction,
    *,
    wolf: discord.Member | None,
    target_own_wolf: str | None,
) -> tuple[object | None, str | None]:
    if wolf and target_own_wolf:
        return None, "Pick either another **player** (`wolf`) or `target_own_wolf`, not both."
    if target_own_wolf:
        target = _resolve_own_wolf(interaction.user.id, target_own_wolf)
        if not target:
            return None, "No wolf with that name on your account. Check `/wolves`."
        if target["id"] == subject["id"]:
            return None, "Pick a different wolf than the one you're setting bonds for."
        return target, None
    if wolf:
        if wolf.id == interaction.user.id:
            return None, "Use `target_own_wolf` for another character you own."
        target = db.get_user(wolf.id)
        if not target:
            return None, "__not_registered__"
        return target, None
    return None, "Specify `wolf` (another player) or `target_own_wolf` (your other wolf)."


class BondsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="bonds",
        description="View or manage friendships, rivalries, kin, mentors, and found families.",
    )
    @app_commands.describe(
        action="What to do",
        own_wolf="Your other wolf; whose bonds to view or edit (default: active wolf)",
        wolf="Another player's wolf (set/clear target)",
        target_own_wolf="Your other wolf as set/clear target",
        bond_type="Bond to set or clear",
        strength="Bond strength 0-100 (set only; default 40)",
        note="Short label; e.g. litter-mate, old feud (set only)",
        family_name="Found family name (create or join)",
        family_role="Your role in the family (join only)",
        leave="Leave your current found family",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="View bonds", value="view"),
            app_commands.Choice(name="Set bond", value="set"),
            app_commands.Choice(name="Clear bond", value="clear"),
            app_commands.Choice(name="Found family", value="family"),
        ],
        bond_type=[
            app_commands.Choice(name="Friendship", value="friendship"),
            app_commands.Choice(name="Rivalry", value="rivalry"),
            app_commands.Choice(name="Kin", value="kin"),
            app_commands.Choice(name="Mentor", value="mentor"),
        ],
        family_role=[
            app_commands.Choice(name="Parent", value="parent"),
            app_commands.Choice(name="Sibling", value="sibling"),
            app_commands.Choice(name="Cub", value="cub"),
            app_commands.Choice(name="Member", value="member"),
        ],
    )
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, target_own_wolf=_other_wolf_autocomplete)
    async def bonds(
        self,
        interaction: discord.Interaction,
        action: str = "view",
        own_wolf: str | None = None,
        wolf: discord.Member | None = None,
        target_own_wolf: str | None = None,
        bond_type: str | None = None,
        strength: app_commands.Range[int, 0, 100] | None = None,
        note: str | None = None,
        family_name: str | None = None,
        family_role: str | None = None,
        leave: bool = False,
    ):
        subject, err = _resolve_subject(interaction, own_wolf)
        if err == "__not_registered__":
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        if err:
            await interaction.response.send_message(
                embed=howlbert_embed("Unknown Wolf", err, color=ERROR_COLOR),
                ephemeral=True,
            )
            return

        if action == "view":
            body = format_bonds_embed_body(subject)
            await interaction.response.send_message(
                embed=howlbert_embed(f"{subject['wolf_name']}; Bonds", body),
            )
            return

        if action == "family":
            if not interaction.guild:
                await interaction.response.send_message("Use this in a server.", ephemeral=True)
                return
            world = db.get_world(interaction.guild.id)
            day = world["day_number"]

            if leave:
                ok, msg = db.leave_wolf_family(subject["id"])
                if not ok:
                    await interaction.response.send_message(
                        embed=howlbert_embed("Found Family", msg or "Could not leave.", color=ERROR_COLOR),
                        ephemeral=True,
                    )
                    return
                await interaction.response.send_message(
                    embed=howlbert_embed(
                        "Found Family",
                        f"**{subject['wolf_name']}** leaves the found family.",
                        color=SUCCESS_COLOR,
                    ),
                )
                return

            name = (family_name or "").strip()
            if not name:
                await interaction.response.send_message(
                    embed=howlbert_embed(
                        "Found Family",
                        "Give a **family_name** to create or join, or set **leave:true** to depart.\n\n"
                        "• **Create**; `/bonds action:Found family family_name:The Howlers`\n"
                        "• **Join**; `/bonds action:Found family family_name:The Howlers family_role:Sibling`\n"
                        "• **Leave**; `/bonds action:Found family leave:true`",
                        color=ERROR_COLOR,
                    ),
                    ephemeral=True,
                )
                return

            if db.get_family_by_name(name):
                family, msg = db.join_wolf_family(
                    subject["id"],
                    name,
                    role=family_role or "member",
                    day=day,
                )
                if not family:
                    await interaction.response.send_message(
                        embed=howlbert_embed("Found Family", msg or "Could not join.", color=ERROR_COLOR),
                        ephemeral=True,
                    )
                    return
                role_label = FAMILY_ROLE_LABELS.get(family_role or "member", "Member")
                await interaction.response.send_message(
                    embed=howlbert_embed(
                        "Found Family",
                        f"**{subject['wolf_name']}** joins **{family['name']}** as **{role_label}**.",
                        color=SUCCESS_COLOR,
                    ),
                )
                return

            family, msg = db.create_wolf_family(subject["id"], name, day=day)
            if not family:
                await interaction.response.send_message(
                    embed=howlbert_embed("Found Family", msg or "Could not create family.", color=ERROR_COLOR),
                    ephemeral=True,
                )
                return
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Found Family",
                    f"**{subject['wolf_name']}** founds **{family['name']}**; invite packmates to join with the same name.",
                    color=SUCCESS_COLOR,
                ),
            )
            return

        target, terr = _resolve_bond_target(
            subject, interaction, wolf=wolf, target_own_wolf=target_own_wolf
        )
        if terr == "__not_registered__":
            await interaction.response.send_message("They haven't registered a wolf.", ephemeral=True)
            return
        if terr:
            await interaction.response.send_message(
                embed=howlbert_embed("Pick a Wolf", terr, color=ERROR_COLOR),
                ephemeral=True,
            )
            return

        if not bond_type:
            await interaction.response.send_message(
                embed=howlbert_embed("Bond Type", "Pick a **bond_type**.", color=ERROR_COLOR),
                ephemeral=True,
            )
            return

        label = BOND_LABELS.get(bond_type, bond_type.title())

        if action == "clear":
            cleared = db.clear_bond(subject["id"], target["id"], bond_type)
            if not cleared:
                await interaction.response.send_message(
                    embed=howlbert_embed(
                        "Clear Bond",
                        f"No **{label.lower()}** between **{subject['wolf_name']}** and **{target['wolf_name']}**.",
                        color=ERROR_COLOR,
                    ),
                    ephemeral=True,
                )
                return
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Clear Bond",
                    f"Cleared **{label.lower()}** between **{subject['wolf_name']}** and **{target['wolf_name']}**.",
                    color=SUCCESS_COLOR,
                ),
            )
            return

        if action == "set":
            if not interaction.guild:
                await interaction.response.send_message("Use this in a server.", ephemeral=True)
                return
            world = db.get_world(interaction.guild.id)
            row = db.set_bond(
                subject["id"],
                target["id"],
                bond_type,
                strength=strength if strength is not None else 40,
                note=note or "",
                day=world["day_number"],
            )
            if not row:
                await interaction.response.send_message(
                    embed=howlbert_embed("Set Bond", "Could not save bond.", color=ERROR_COLOR),
                    ephemeral=True,
                )
                return
            note_line = f"\n_{row['note']}_" if row["note"] else ""
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Set Bond",
                    f"**{subject['wolf_name']}** ↔ **{target['wolf_name']}**; **{label}** "
                    f"**{row['strength']}/100**{note_line}",
                    color=SUCCESS_COLOR,
                ),
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(BondsCog(bot))
