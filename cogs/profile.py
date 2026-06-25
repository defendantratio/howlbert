import discord

from discord import app_commands

from discord.ext import commands



import database as db

from config import CURRENCY_LABEL, GREAT_PACKS, LONER_DESCRIPTION, LONER_KEY, LONER_LABEL, MAX_WOLVES_PER_PLAYER, ROGUE_DESCRIPTION, ROGUE_KEY, ROGUE_LABEL, SETFACTION_CHANGE_COST, UNAFFILIATED_KEYS
from herbs import HERBS

from rpg_rules import ROLE_LABELS, ROLE_FEATURES

from engine.attraction import BIRTH_SEX_LABELS, SEXUALITY_LABELS, SEXUALITY_OPTIONS, get_birth_sex, get_sexuality

from engine.aging import (
    format_wolf_age,
    stage_for_age,
    stage_label,
)

from engine.maw_belief import MAW_BELIEF_OPTIONS, format_maw_belief
from engine.character_lore import (
    has_character_lore,
    lore_embed_fields,
)

from engine.character import attr_modifier

from engine.pack_unity import standing_effect_text
from engine.prestige import get_tier_info

from utils.currency import format_bones

from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, trim_embed_fields

from utils.names import validate_display_name

from utils.permissions import is_howlbert_admin


class _EmbedPaginator(discord.ui.View):
    def __init__(self, *, pages: list[discord.Embed], owner_id: int, timeout: float = 180):
        super().__init__(timeout=timeout)
        self._pages = pages
        self._owner_id = owner_id
        self._idx = 0
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        self.prev_btn.disabled = self._idx <= 0
        self.next_btn.disabled = self._idx >= len(self._pages) - 1
        self.page_btn.label = f"{self._idx + 1}/{len(self._pages)}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user is not None and interaction.user.id == self._owner_id

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._idx = max(0, self._idx - 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self._pages[self._idx], view=self)

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.gray, disabled=True)
    async def page_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._idx = min(len(self._pages) - 1, self._idx + 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self._pages[self._idx], view=self)


def _paginate_embed_fields(embed: discord.Embed, *, max_fields: int = 25) -> list[discord.Embed]:
    """Split an embed into multiple embeds if it exceeds Discord's 25-field limit."""
    if len(embed.fields) <= max_fields:
        return [embed]

    thumb_url = getattr(getattr(embed, "thumbnail", None), "url", None)
    footer_text = getattr(getattr(embed, "footer", None), "text", None)

    fields = list(embed.fields)
    pages: list[discord.Embed] = []
    for start in range(0, len(fields), max_fields):
        chunk = fields[start : start + max_fields]
        e = discord.Embed(title=embed.title, description=embed.description, color=embed.color)
        if thumb_url:
            e.set_thumbnail(url=thumb_url)
        if footer_text:
            e.set_footer(text=footer_text)
        for f in chunk:
            e.add_field(name=f.name, value=f.value, inline=f.inline)
        pages.append(e)
    return pages


PACK_CHOICES = [

    app_commands.Choice(

        name=f"{info['name']}; {info['path']}",

        value=key,

    )

    for key, info in GREAT_PACKS.items()

] + [

    app_commands.Choice(

        name=f"{LONER_LABEL}; walk apart from any pack",

        value=LONER_KEY,

    ),

    app_commands.Choice(

        name=f"{ROGUE_LABEL}; hostile, border-raiding loner",

        value=ROGUE_KEY,

    ),

]





def _pack_display(affiliation: str) -> str:

    if affiliation == LONER_KEY:

        return f"**{LONER_LABEL}**; {LONER_DESCRIPTION}"

    if affiliation == ROGUE_KEY:

        return f"**{ROGUE_LABEL}**; {ROGUE_DESCRIPTION}"

    if affiliation in GREAT_PACKS:

        info = GREAT_PACKS[affiliation]

        return f"**{info['name']}** ({info['terrain']})"

    return "Unknown"





class Profile(commands.Cog):

    def __init__(self, bot: commands.Bot):

        self.bot = bot



    @app_commands.command(name="register", description="Create a wolf (up to 3 per player; admins unlimited).")

    @app_commands.describe(

        name="Your wolf's name",

        pack="Join a Great Pack or walk as a lone wolf / rogue",

        birth_sex="Birth sex (female, male, or intersex; affects conception)",

        sexuality="Who your wolf is attracted to (pups: Too young / none)",

        role="Your wolf's role (sets starting attributes and skills)",

        starting_age="Starting age in moons, 0-120 (optional; defaults from role)",

        genetic="Optional RP genetics; comma-separated: blind, half_blind, deaf, brachycephaly, albinism, melanism, missing_leg, no_tail",

        maw_belief="Faith in the Maw (defaults to Orthodox for Great Pack wolves)",

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

        maw_belief=[
            app_commands.Choice(name=label, value=value)
            for label, value in MAW_BELIEF_OPTIONS
        ],

    )

    async def register(

        self,

        interaction: discord.Interaction,

        name: str,

        pack: str,

        birth_sex: str,

        sexuality: str,

        role: str = "hunter",

        starting_age: app_commands.Range[int, 0, 120] | None = None,

        genetic: str | None = None,

        maw_belief: str | None = None,

    ):

        wolf_count = db.count_slot_wolves(interaction.user.id)
        is_admin = is_howlbert_admin(interaction)
        if not is_admin and wolf_count >= MAX_WOLVES_PER_PLAYER:
            embed = howlbert_embed(
                "Wolf Limit Reached",
                f"You already have **{MAX_WOLVES_PER_PLAYER}** wolves. "
                "Use `/switchwolf` to change active character, or `/rpg action:delete confirm:DELETE` to remove one.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        wolf_name, name_err = db.validate_wolf_name_available(name, label="Wolf names")
        if name_err:
            title = "Name Taken" if "already taken" in name_err else "Invalid Name"
            embed = howlbert_embed(title, name_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        age_months = starting_age

        from engine.genetics import encode_genetic_conditions, parse_genetic_register_input

        genetic_keys, genetic_err = parse_genetic_register_input(genetic)
        if genetic_err:
            embed = howlbert_embed("Invalid Genetics", genetic_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            db.register_user(

                interaction.user.id,

                wolf_name,

                pack,

                wolf_role=role,

                birth_sex=birth_sex,

                sexuality=sexuality,

                age_months=age_months,

                genetic_conditions=encode_genetic_conditions(genetic_keys),

                maw_belief=maw_belief,

            )
        except ValueError as exc:
            msg = str(exc)
            title = (
                "Name Taken"
                if "already taken" in msg or "reserved" in msg
                else "Invalid Name"
            )
            embed = howlbert_embed(title, msg, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from engine.patron import on_wolf_registered

        invite_note = None
        if interaction.guild:
            invite_note = on_wolf_registered(
                interaction.user.id,
                interaction.guild.id,
                first_wolf=(wolf_count == 0),
            )



        user = db.get_user(interaction.user.id)

        embed = howlbert_embed("Welcome to the Den", color=SUCCESS_COLOR)

        embed.add_field(name="Wolf", value=wolf_name, inline=True)

        embed.add_field(name="Birth Sex", value=BIRTH_SEX_LABELS.get(birth_sex, birth_sex.title()), inline=True)

        embed.add_field(name="Sexuality", value=SEXUALITY_LABELS.get(sexuality, sexuality.title()), inline=True)

        embed.add_field(name="Role", value=ROLE_LABELS.get(user["wolf_role"], user["wolf_role"].title()), inline=True)

        age_mo = user["age_months"] if "age_months" in user.keys() else 24
        embed.add_field(
            name="Age",
            value=f"{format_wolf_age(age_mo)} ({stage_label(stage_for_age(age_mo))})",
            inline=True,
        )

        if age_months is not None and user["wolf_role"] != role:
            embed.add_field(
                name="Age & Role",
                value=(
                    f"At **{format_wolf_age(age_mo)}** your wolf starts as "
                    f"**{ROLE_LABELS.get(user['wolf_role'], user['wolf_role'])}** "
                    f"(you picked **{ROLE_LABELS.get(role, role)}**)."
                ),
                inline=False,
            )

        embed.add_field(name="Pack", value=_pack_display(pack), inline=False)

        belief_text = format_maw_belief(user)
        if belief_text:
            embed.add_field(name="Maw Belief", value=belief_text, inline=False)

        if user["wolf_role"] == "drown_sick":
            oracle_blurb = (
                "Drown-Sick wolves are **Mistmoor oracles**; frail, prophetic, changed by the Belly-Rip. "
                "Use `/role action:event`, `/role action:prophecy`, and `/role action:quests`."
            )
            if stage_for_age(age_mo) == "pup":
                oracle_blurb += (
                    " You are still **under 6 moons**; mothers nurse via `/pupcare action:feed`; pack caretakers mash-feed; forbidden to hunt, fight, or mate."
                )
            embed.add_field(name="Oracle's Path", value=oracle_blurb, inline=False)
        elif user["wolf_role"] == "pup":
            embed.add_field(
                name="Pup's Path",
                value=(
                    "You are under **6 moons**; mothers nurse via `/pupcare action:feed`; pack caretakers mash-feed; forbidden to hunt, fight, or mate. "
                    "Survive the first moon to be named. Use `/role action:event` and `/role action:quests`."
                ),
                inline=False,
            )
        elif user["wolf_role"] == "juvenile":
            embed.add_field(
                name="Juvenile's Path",
                value=(
                    "You are **6-24 moons**; practice hunting; your **blooding** comes on your first kill. "
                    "Forbidden to mate. "
                    "Complete role quests and `/role action:event` to grow toward an adult role."
                ),
                inline=False,
            )

        if pack in GREAT_PACKS:

            faction = GREAT_PACKS[pack]

            embed.add_field(name="Motto", value=f"_{faction['motto']}_", inline=False)

            embed.add_field(name="Pack Trait", value=faction["pack_trait"], inline=False)

            herbs = ", ".join(
                HERBS[k]["name"] if k in HERBS else k.replace("_", " ").title()
                for k in faction["starting_herbs"]
            )
            embed.add_field(name="Starting Herbs", value=f"{herbs}\n_Added to `/inventory`._", inline=False)

        else:

            embed.add_field(

                name="The Rogue Path",

                value="No pack treasury, tax, or trait; free to roam. Use `/setfaction` to join a Great Pack later.",

                inline=False,

            )



        embed.add_field(

            name="Next Steps",

            value=(
                "Try `/profile` for your sheet, `/rpg action:roll` for skill checks, `/bones action:hunt` or `action:work` for bones.\n"
                "New here? **`/help topic:getting-started`** walks through courtship, pups, and the den."
            ),

            inline=False,

        )

        if invite_note:
            embed.add_field(name="Invite Reward", value=invite_note, inline=False)

        total = db.count_user_wolves(interaction.user.id)
        slots = db.count_slot_wolves(interaction.user.id)
        born = db.count_born_pups(interaction.user.id)
        if total > 1:
            footer = f"Active wolf · {slots} of {MAX_WOLVES_PER_PLAYER} slots"
            if born:
                footer += f" (+ {born} born pup{'s' if born != 1 else ''})"
            footer += " · use /switchwolf to change"
            embed.set_footer(text=footer)
        elif not is_admin:
            footer = f"Wolf {slots} of {MAX_WOLVES_PER_PLAYER}"
            if born:
                footer += f" (+ {born} born pup{'s' if born != 1 else ''})"
            footer += " · /register again for another"
            embed.set_footer(text=footer)

        await interaction.response.send_message(embed=embed)



    @app_commands.command(name="wolves", description="List all wolves on your account.")
    async def wolves(self, interaction: discord.Interaction):
        rows = db.list_user_wolves(interaction.user.id)
        if not rows:
            embed = howlbert_embed(
                "No Wolves",
                "Use `/register` to create your first wolf.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        active_id = db.get_active_wolf_id(interaction.user.id)
        lines = []
        for w in rows:
            marker = " ◀ active" if w["id"] == active_id else ""
            pack = db.get_user_affiliation(w)
            if pack == LONER_KEY:
                pack_label = LONER_LABEL
            elif pack == ROGUE_KEY:
                pack_label = ROGUE_LABEL
            else:
                pack_label = _pack_display(pack)
            lines.append(f"**{w['wolf_name']}**; {pack_label}{marker}")

        limit_note = "unlimited" if is_howlbert_admin(interaction) else str(MAX_WOLVES_PER_PLAYER)
        footer = (
            f"{len(rows)} wolf(s) · limit {limit_note} · /switchwolf to play as another"
            + (" · type a name if yours is not in the list" if len(rows) > 25 else "")
        )
        page_size = 20
        if len(lines) <= page_size:
            embed = howlbert_embed("Your Wolves", "\n".join(lines))
            embed.set_footer(text=footer)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        pages: list[discord.Embed] = []
        for start in range(0, len(lines), page_size):
            chunk = lines[start : start + page_size]
            page_num = start // page_size + 1
            page_total = (len(lines) + page_size - 1) // page_size
            embed = howlbert_embed(
                f"Your Wolves ({page_num}/{page_total})",
                "\n".join(chunk),
            )
            embed.set_footer(text=footer)
            pages.append(embed)
        view = _EmbedPaginator(pages=pages, owner_id=interaction.user.id)
        await interaction.response.send_message(embed=pages[0], view=view, ephemeral=True)

    async def _own_wolf_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        return await self._switchwolf_autocomplete(interaction, current)

    async def _switchwolf_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        rows = sorted(
            db.list_user_wolves(interaction.user.id),
            key=lambda w: w["wolf_name"].lower(),
        )
        needle = current.lower()
        choices = []
        for w in rows:
            if needle and needle not in w["wolf_name"].lower():
                continue
            choices.append(app_commands.Choice(name=w["wolf_name"], value=w["wolf_name"]))
        return choices[:25]

    @app_commands.command(name="switchwolf", description="Switch which wolf you're playing as.")
    @app_commands.describe(name="Wolf name to activate")
    @app_commands.autocomplete(name=_switchwolf_autocomplete)
    async def switchwolf(self, interaction: discord.Interaction, name: str):
        rows = db.list_user_wolves(interaction.user.id)
        if not rows:
            embed = howlbert_embed("No Wolves", "Use `/register` first.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        match = next(
            (w for w in rows if w["wolf_name"].lower() == name.strip().lower()),
            None,
        )
        if not match:
            embed = howlbert_embed(
                "Not Found",
                "No wolf with that name on your account. Check `/wolves`.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if match["id"] == db.get_active_wolf_id(interaction.user.id):
            embed = howlbert_embed(
                "Already Active",
                f"You're already playing as **{match['wolf_name']}**.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        db.set_active_wolf(interaction.user.id, match["id"])
        embed = howlbert_embed(
            "Wolf Switched",
            f"You're now playing as **{match['wolf_name']}**.\n"
            "Bones, inventory, quests, and cooldowns follow this wolf.",
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed)



    @app_commands.command(

        name="setfaction",

        description="Join a Great Pack, switch packs, or leave to walk as a lone wolf.",

    )

    @app_commands.describe(pack="Great Pack to join, or Lone Wolf to leave pack life")

    @app_commands.choices(pack=PACK_CHOICES)

    async def setfaction(self, interaction: discord.Interaction, pack: str):

        user = db.get_user(interaction.user.id)

        if not user:

            embed = howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)

            await interaction.response.send_message(embed=embed, ephemeral=True)

            return



        current = db.get_user_affiliation(user)

        if current == pack:

            embed = howlbert_embed(

                "No Change",

                f"You already walk as **{_pack_display(pack)}**.",

                color=ERROR_COLOR,

            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

            return



        if current not in UNAFFILIATED_KEYS and pack not in UNAFFILIATED_KEYS:

            if user["bones"] < SETFACTION_CHANGE_COST:

                embed = howlbert_embed(

                    "Not Enough Bones",

                    f"Switching Great Packs costs {format_bones(SETFACTION_CHANGE_COST)}.",

                    color=ERROR_COLOR,

                )

                await interaction.response.send_message(embed=embed, ephemeral=True)

                return

            db.deduct_bones(interaction.user.id, SETFACTION_CHANGE_COST)



        err = db.assign_pack_affiliation(interaction.user.id, pack)

        if err:

            embed = howlbert_embed("Cannot Change Pack", err, color=ERROR_COLOR)

            await interaction.response.send_message(embed=embed, ephemeral=True)

            return



        embed = howlbert_embed("Pack Updated", color=SUCCESS_COLOR)

        embed.add_field(name="Now", value=_pack_display(pack), inline=False)

        if pack in GREAT_PACKS:

            faction = GREAT_PACKS[pack]

            embed.add_field(name="Path", value=faction["path"], inline=True)

            embed.add_field(name="Motto", value=f"_{faction['motto']}_", inline=False)

        if current not in UNAFFILIATED_KEYS and pack not in UNAFFILIATED_KEYS:

            embed.set_footer(text=f"Paid {format_bones(SETFACTION_CHANGE_COST)} to change Great Packs.")

        await interaction.response.send_message(embed=embed)



    @app_commands.command(name="rename", description="Change your wolf's name.")

    @app_commands.describe(name="Your wolf's new name")

    async def rename(self, interaction: discord.Interaction, name: str):

        user = db.get_user(interaction.user.id)

        if not user:

            embed = howlbert_embed(

                "Not Registered",

                "Use `/register` before renaming your wolf.",

                color=ERROR_COLOR,

            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

            return



        new_name, error = validate_display_name(name, label="Wolf names")

        if error:

            embed = howlbert_embed("Invalid Name", error, color=ERROR_COLOR)

            await interaction.response.send_message(embed=embed, ephemeral=True)

            return



        if new_name.lower() == user["wolf_name"].lower():

            embed = howlbert_embed(

                "Same Name",

                f"You're already known as **{user['wolf_name']}**.",

                color=ERROR_COLOR,

            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

            return



        err = db.rename_wolf(interaction.user.id, new_name)
        if err and err.startswith("name:"):
            body = err[5:]
            title = "Name Taken" if "already taken" in body else "Invalid Name"
            embed = howlbert_embed(title, body, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        old_name = user["wolf_name"]



        embed = howlbert_embed("Name Changed", color=SUCCESS_COLOR)

        embed.add_field(name="Was", value=old_name, inline=True)

        embed.add_field(name="Now", value=new_name, inline=True)

        await interaction.response.send_message(embed=embed)



    @app_commands.command(name="profile", description="View a wolf's profile or character sheet.")
    @app_commands.describe(
        member="The wolf to look up (defaults to you)",
        sheet="Show lore sheet (appearance, backstory)",
        own_wolf="One of your other wolves (sheet only; defaults to active wolf)",
    )
    @app_commands.autocomplete(own_wolf=_own_wolf_autocomplete)
    async def profile(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
        sheet: bool = False,
        own_wolf: str | None = None,
    ):
        if sheet:
            await self._bio(interaction, member, own_wolf=own_wolf)
            return

        target = member or interaction.user

        user = db.get_user(target.id)



        if not user:

            message = (

                "You haven't registered yet. Use `/register` to create your wolf."

                if target == interaction.user

                else f"{target.display_name} hasn't registered a wolf yet."

            )

            embed = howlbert_embed("No Profile Found", message, color=ERROR_COLOR)

            await interaction.response.send_message(embed=embed, ephemeral=True)

            return



        affiliation = db.get_user_affiliation(user)



        embed = howlbert_embed(user["wolf_name"])
        possess = db.get_possess_session(interaction.user.id)
        if possess and target == interaction.user:
            embed.description = (
                f"_Admin steering **{user['wolf_name']}** "
                f"(owner <@{possess['owner_discord_id']}>) · `/wolfadmin release` to stop._"
            )

        embed.set_thumbnail(url=target.display_avatar.url)

        wolf_role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"

        embed.add_field(name="Role", value=ROLE_LABELS.get(wolf_role, wolf_role.title()), inline=True)

        from engine.combat_size import format_size_class_profile

        embed.add_field(name="Build", value=format_size_class_profile(user), inline=True)

        age_mo = user["age_months"] if "age_months" in user.keys() else 24
        embed.add_field(
            name="Age",
            value=f"{format_wolf_age(age_mo)} ({stage_label(stage_for_age(age_mo))})",
            inline=True,
        )
        birth_moon = user["birth_lunar_phase"] if "birth_lunar_phase" in user.keys() else ""
        if birth_moon:
            from engine.lunar import BIRTH_LUNAR_LABELS

            embed.add_field(
                name="Birth Moon",
                value=BIRTH_LUNAR_LABELS.get(birth_moon, birth_moon.replace("_", " ").title()),
                inline=True,
            )

        embed.add_field(name="Pack", value=_pack_display(affiliation), inline=True)

        bs = get_birth_sex(user)

        if bs:

            embed.add_field(name="Birth Sex", value=BIRTH_SEX_LABELS.get(bs, bs.title()), inline=True)

        orient = get_sexuality(user)

        embed.add_field(name="Sexuality", value=SEXUALITY_LABELS.get(orient, orient.title()), inline=True)

        belief_text = format_maw_belief(user)
        if belief_text:
            embed.add_field(name="Maw Belief", value=belief_text, inline=False)

        if has_character_lore(user):
            embed.add_field(
                name="Character Sheet",
                value="Appearance, backstory, and RP sample on file; use `/profile sheet:true`.",
                inline=False,
            )

        if "bonded_mate_id" in user.keys() and user["bonded_mate_id"]:

            bonded = db.get_bonded_mate(user)

            if bonded:

                embed.add_field(name="Bonded Mate", value=bonded["wolf_name"], inline=True)

        lineage = db.format_lineage_for_profile(user)
        if lineage:
            embed.add_field(name="Family", value=lineage, inline=False)

        from engine.bonds import format_bonds_embed_body

        bonds_preview = format_bonds_embed_body(user)
        if bonds_preview and "No bonds recorded yet" not in bonds_preview:
            if len(bonds_preview) > 1024:
                bonds_preview = bonds_preview[:1021] + "…"
            embed.add_field(name="Bonds", value=bonds_preview, inline=False)

        embed.add_field(name="Condition", value=user["condition"].title(), inline=True)

        def fmt_attr(key: str) -> str:
            score = user[key] if key in user.keys() else 5
            return f"{score} ({attr_modifier(score):+d})"

        embed.add_field(
            name="Attributes",
            value=(
                f"STR {fmt_attr('attr_str')} · DEX {fmt_attr('attr_dex')} · CON {fmt_attr('attr_con')}\n"
                f"INT {fmt_attr('attr_int')} · CHA {fmt_attr('attr_cha')} · WIS {fmt_attr('attr_wis')}"
            ),
            inline=False,
        )

        if "hp" in user.keys():
            from engine.character import format_max_hp_breakdown
            from engine.exhaustion_effects import effective_max_hp, user_exhaustion

            cap = effective_max_hp(user)
            str_val = int(user["attr_str"]) if "attr_str" in user.keys() else 5
            con_val = int(user["attr_con"]) if "attr_con" in user.keys() else 5
            hp_line = f"{user['hp']} / {cap}\n{format_max_hp_breakdown(str_val, con_val, max_hp=int(user['max_hp']))}"
            if user_exhaustion(user) >= 4:
                hp_line += f"\n_(exhaustion cap {cap}; base {user['max_hp']})_"
            embed.add_field(name="HP", value=hp_line, inline=True)

        from engine.character_traits import format_traits_for_profile, format_skill_strain_line

        strain_line = format_skill_strain_line(user)
        if strain_line:
            embed.add_field(name="Practice Strain", value=strain_line, inline=False)

        traits_text = format_traits_for_profile(user)

        if wolf_role in ROLE_FEATURES:
            from engine.role_features import bonus_feature_label

            role_text = ROLE_FEATURES[wolf_role]
            bonus = bonus_feature_label(user)
            if bonus:
                role_text += f"\n**Bonus feature:** {bonus}"
            embed.add_field(name="Role Feature", value=role_text, inline=False)

        if traits_text:
            if len(traits_text) > 1024:
                traits_text = traits_text[:1021] + "…"
            embed.add_field(name="Skills & Weaknesses", value=traits_text, inline=False)

        from engine.conditions import format_conditions

        day = None
        if interaction.guild_id:
            world = db.get_world(interaction.guild_id)
            if world:
                day = world["day_number"]
        cond_text = format_conditions(user, day=day)

        from engine.role_features import is_full_medic

        if cond_text != "Healthy: no active conditions." or (is_full_medic(user) and day is not None):
            embed.add_field(name="Conditions", value=cond_text, inline=False)

        if affiliation in GREAT_PACKS:

            embed.add_field(

                name="Pack Trait",

                value=GREAT_PACKS[affiliation]["pack_trait"],

                inline=False,

            )



        standing = int(user["standing"])
        embed.add_field(
            name="Standing",
            value=f"**{standing}**\n{standing_effect_text(standing)}",
            inline=False,
        )
        mood = int(user["mood"]) if "mood" in user.keys() else 75
        from config import MOOD_LOW_THRESHOLD
        from engine.hunger import format_hunger_line
        from engine.thirst import format_thirst_line

        mood_note = "; play and socialize to lift it." if mood < MOOD_LOW_THRESHOLD else ""
        embed.add_field(
            name="Vitals",
            value=(
                f"**Mood** {mood}/100{mood_note}\n"
                f"**Hunger** {format_hunger_line(user)}\n"
                f"**Thirst** {format_thirst_line(user)}"
            ),
            inline=False,
        )

        embed.add_field(name=CURRENCY_LABEL, value=format_bones(user["bones"]), inline=True)



        account = db.get_account(target.id)

        tier = get_tier_info(account["prestige_tier"])

        embed.add_field(name="Prestige", value=f"Tier {tier['tier']}; {tier['name']}", inline=False)

        if target == interaction.user:
            slots = db.count_slot_wolves(target.id)
            born = db.count_born_pups(target.id)
            if slots > 1 or born:
                footer = f"Active wolf · {slots} of {MAX_WOLVES_PER_PLAYER} slots"
                if born:
                    footer += f" (+ {born} born pup{'s' if born != 1 else ''})"
                footer += " · /switchwolf to change"
                from engine.kickstarter import profile_footer_suffix

                badge = profile_footer_suffix(target.id)
                if badge:
                    footer = f"{badge} · {footer}"
                embed.set_footer(text=footer)
            else:
                from engine.kickstarter import profile_footer_suffix

                badge = profile_footer_suffix(target.id)
                if badge:
                    embed.set_footer(text=badge)
        else:
            from engine.kickstarter import profile_footer_suffix

            badge = profile_footer_suffix(target.id)
            if badge:
                embed.set_footer(text=badge)

        trim_embed_fields(embed)
        pages = _paginate_embed_fields(embed, max_fields=25)
        if len(pages) == 1:
            await interaction.response.send_message(embed=embed)
            return

        view = _EmbedPaginator(pages=pages, owner_id=interaction.user.id)
        await interaction.response.send_message(embed=pages[0], view=view)

    async def _bio(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
        *,
        own_wolf: str | None = None,
    ):
        if member and own_wolf:
            embed = howlbert_embed(
                "Pick One",
                "Use **member** for another player's active wolf, or **own_wolf** for one of yours — not both.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if own_wolf:
            match = db.find_user_wolf(interaction.user.id, own_wolf)
            if not match:
                embed = howlbert_embed(
                    "Not Found",
                    f"No wolf named **{own_wolf}** on your account. Check `/wolves`.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            user = db.get_user_by_id(match["id"])
            title_name = user["wolf_name"]
            avatar = interaction.user.display_avatar.url
        else:
            target = member or interaction.user
            user = db.get_user(target.id)
            title_name = user["wolf_name"] if user else ""
            avatar = target.display_avatar.url

        if not user:
            message = (
                "You haven't registered yet. Use `/register` to create your wolf."
                if not member and not own_wolf
                else f"{(member or interaction.user).display_name} hasn't registered a wolf yet."
            )
            embed = howlbert_embed("No Profile Found", message, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        fields = lore_embed_fields(user)
        if not fields:
            embed = howlbert_embed(
                "No Lore Saved",
                f"**{title_name}** has no character sheet on file yet.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = howlbert_embed(f"{title_name}; Character Sheet")
        embed.set_thumbnail(url=avatar)
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):

    await bot.add_cog(Profile(bot))

