import discord
from discord import app_commands
from discord.ext import commands
import database as db
from config import CURRENCY_LABEL, GREAT_PACKS, LONER_DESCRIPTION, LONER_KEY, LONER_LABEL, MAX_WOLVES_PER_PLAYER, ROGUE_DESCRIPTION, ROGUE_KEY, ROGUE_LABEL, SETFACTION_CHANGE_COST, UNAFFILIATED_KEYS
from herbs import HERBS
from rpg_rules import ROLE_LABELS, ROLE_FEATURES, SKILLS
from engine.attraction import BIRTH_SEX_LABELS, SEXUALITY_LABELS, SEXUALITY_OPTIONS, get_birth_sex, get_sexuality
from engine.aging import format_wolf_age, stage_for_age, stage_label
from engine.maw_belief import MAW_BELIEF_OPTIONS, format_maw_belief
from engine.character_lore import has_character_lore, lore_embed_fields
from engine.character import attr_modifier
from engine.character_art import canonical_art_path
from engine.pack_unity import standing_effect_text
from engine.prestige import get_tier_info
from utils.currency import format_bones
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, trim_embed_fields, PlayerEmbed, choice_label
from utils.names import validate_display_name
from utils.permissions import is_howlbert_admin
from utils.wolf_autocomplete import make_member_wolf_autocomplete

_member_wolf_autocomplete = make_member_wolf_autocomplete("member")

class _EmbedPaginator(discord.ui.View):

    def __init__(self, *, pages: list[discord.Embed], owner_id: int, timeout: float=180):
        super().__init__(timeout=timeout)
        self._pages = pages
        self._owner_id = owner_id
        self._idx = 0
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        self.prev_btn.disabled = self._idx <= 0
        self.next_btn.disabled = self._idx >= len(self._pages) - 1
        self.page_btn.label = f'{self._idx + 1}/{len(self._pages)}'

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user is not None and interaction.user.id == self._owner_id

    @discord.ui.button(label='prev', style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._idx = max(0, self._idx - 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self._pages[self._idx], view=self)

    @discord.ui.button(label='1/1', style=discord.ButtonStyle.gray, disabled=True)
    async def page_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer_update()

    @discord.ui.button(label='next', style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._idx = min(len(self._pages) - 1, self._idx + 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self._pages[self._idx], view=self)

def _paginate_embed_fields(embed: discord.Embed, *, max_fields: int=25) -> list[discord.Embed]:
    """Split an embed into multiple embeds if it exceeds Discord's 25-field limit."""
    if len(embed.fields) <= max_fields:
        return [embed]
    thumb_url = getattr(getattr(embed, 'thumbnail', None), 'url', None)
    footer_text = getattr(getattr(embed, 'footer', None), 'text', None)
    fields = list(embed.fields)
    pages: list[discord.Embed] = []
    for start in range(0, len(fields), max_fields):
        chunk = fields[start:start + max_fields]
        e = PlayerEmbed(title=embed.title, description=embed.description, color=embed.color)
        if thumb_url:
            e.set_thumbnail(url=thumb_url)
        if footer_text:
            e.set_footer(text=footer_text)
        for f in chunk:
            e.add_field(name=f.name, value=f.value, inline=f.inline)
        pages.append(e)
    return pages
PACK_CHOICES = [app_commands.Choice(name=choice_label(f"{info['name']}; {info['path']}"), value=key) for key, info in GREAT_PACKS.items()] + [app_commands.Choice(name=choice_label(f'{LONER_LABEL}; walk apart from any pack'), value=LONER_KEY), app_commands.Choice(name=choice_label(f'{ROGUE_LABEL}; hostile, border-raiding loner'), value=ROGUE_KEY)]

# friendly attribute names -> attr key, for the comma-separated trait_weakness field.
_WEAKNESS_ATTRS = {
    'strength': 'attr_str', 'str': 'attr_str',
    'dexterity': 'attr_dex', 'dex': 'attr_dex',
    'constitution': 'attr_con', 'con': 'attr_con', 'survival': 'attr_con',
    'intelligence': 'attr_int', 'int': 'attr_int',
    'charisma': 'attr_cha', 'cha': 'attr_cha',
    'wisdom': 'attr_wis', 'wis': 'attr_wis',
}


def _parse_register_traits(trait_skill: str | None, trait_weakness: str | None,
                           default_bonus: int = 1, default_penalty: int = -1):
    """Parse comma-separated starting skills and weak attributes from /register.
    Each item may carry its own value inline (e.g. `hunting:2, stealth`); a bare
    item uses the default bonus/penalty. Returns (skill_pairs, weakness_pairs,
    error), each pair a (key, value); duplicates are dropped, and an unknown token
    or out-of-range value returns a helpful error instead of vanishing."""
    from rpg_rules import SKILLS

    def split_val(part, default):
        if ':' in part:
            name, _, raw = part.rpartition(':')
            raw = raw.strip()
            try:
                return name.strip(), int(raw), None
            except ValueError:
                return None, None, f"**{raw}** isn't a number (use e.g. `hunting:2`)."
        return part.strip(), default, None

    skills: list[tuple[str, int]] = []
    seen_s: set[str] = set()
    if trait_skill:
        for part in trait_skill.replace(';', ',').split(','):
            part = part.strip()
            if not part:
                continue
            name, val, err = split_val(part, default_bonus)
            if err:
                return [], [], err
            if not 0 <= val <= 5:
                return [], [], f"skill bonus **{val}** is out of range (0 to 5)."
            tok = name.lower().replace(' ', '_')
            if tok not in SKILLS:
                return [], [], f"unknown skill **{name}**; pick from: {', '.join(SKILLS)}."
            if tok not in seen_s:
                seen_s.add(tok)
                skills.append((tok, val))
    weaknesses: list[tuple[str, int]] = []
    seen_w: set[str] = set()
    if trait_weakness:
        for part in trait_weakness.replace(';', ',').split(','):
            part = part.strip()
            if not part:
                continue
            name, val, err = split_val(part, default_penalty)
            if err:
                return [], [], err
            if val > 0:
                val = -val
            if not -5 <= val <= 0:
                return [], [], f"weakness penalty **{val}** is out of range (-5 to 0)."
            tok = name.lower().replace('attr_', '').replace(' (constitution)', '')
            key = _WEAKNESS_ATTRS.get(tok)
            if not key:
                return [], [], f"unknown attribute **{name}**; pick from: strength, dexterity, constitution, intelligence, charisma, wisdom."
            if key not in seen_w:
                seen_w.add(key)
                weaknesses.append((key, val))
    return skills, weaknesses, None


async def _pack_register_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Great packs + loner/rogue + any live founded pack (dynamic; can't be a static Choice list)."""
    from engine.factions import founded_key_for
    cur = current.lower()
    choices: list[app_commands.Choice[str]] = []
    for choice in PACK_CHOICES:
        if not cur or cur in choice.name.lower():
            choices.append(choice)
    for pack in db.list_founded_packs():
        label = choice_label(f"{pack['name']}; a founded pack")
        if not cur or cur in label.lower():
            choices.append(app_commands.Choice(name=label, value=founded_key_for(pack['id'])))
    return choices[:25]

def _profile_badges(discord_id: int) -> str | None:
    from engine.kickstarter import profile_footer_suffix
    from engine.patron import referral_badge_text

    badges = [b for b in (profile_footer_suffix(discord_id), referral_badge_text(discord_id)) if b]
    return ' · '.join(badges) if badges else None


def _pack_display(affiliation: str) -> str:
    if affiliation == LONER_KEY:
        return f'**{LONER_LABEL}**; {LONER_DESCRIPTION}'
    if affiliation == ROGUE_KEY:
        return f'**{ROGUE_LABEL}**; {ROGUE_DESCRIPTION}'
    from engine.factions import resolve_faction
    info = resolve_faction(affiliation)
    if info:
        terrain = info.get('terrain')
        return f"**{info['name']}** ({terrain})" if terrain else f"**{info['name']}** (founded pack)"
    return 'Unknown'

class _RegisterLoreModal(discord.ui.Modal, title='wolf lore (optional)'):
    """The prose half of /register. Modal text inputs cap at 4000 characters each
    with real multi-line paste, so this replaces the old personality/personality2
    and backstory/backstory2 split-field workaround that existed only to dodge
    Discord's ~6000-character combined limit on a slash command's composer."""

    personality = discord.ui.TextInput(label='personality', style=discord.TextStyle.paragraph, required=False, max_length=4000)
    backstory = discord.ui.TextInput(label='backstory', style=discord.TextStyle.paragraph, required=False, max_length=4000)
    rp_sample = discord.ui.TextInput(label='rp sample', style=discord.TextStyle.paragraph, required=False, max_length=4000)
    family_ties = discord.ui.TextInput(label='family ties', style=discord.TextStyle.paragraph, required=False, max_length=1000)
    open_plots = discord.ui.TextInput(label='open plots', style=discord.TextStyle.paragraph, required=False, max_length=1000)

    def __init__(self, *, params: dict):
        super().__init__()
        self._p = params

    async def on_submit(self, interaction: discord.Interaction):
        p = self._p
        wolf_name, pack, role, birth_sex, sexuality, age_months, genetic_keys, maw_belief = (
            p['wolf_name'], p['pack'], p['role'], p['birth_sex'], p['sexuality'],
            p['age_months'], p['genetic_keys'], p['maw_belief'],
        )
        fur_color, eye_color, markings, scars = p['fur_color'], p['eye_color'], p['markings'], p['scars']
        skill_keys, weakness_keys = p['skill_keys'], p['weakness_keys']
        is_admin, wolf_count = p['is_admin'], p['wolf_count']
        from engine.genetics import encode_genetic_conditions

        try:
            new_wolf_id = db.register_user(interaction.user.id, wolf_name, pack, wolf_role=role, birth_sex=birth_sex, sexuality=sexuality, age_months=age_months, genetic_conditions=encode_genetic_conditions(genetic_keys), maw_belief=maw_belief)
        except ValueError as exc:
            msg = str(exc)
            title = 'Name Taken' if 'already taken' in msg or 'reserved' in msg else 'Invalid Name'
            embed = howlbert_embed(title, msg, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        identity_fields = {k: v.strip()[:64] for k, v in {'fur_color': fur_color, 'eye_color': eye_color, 'markings': markings, 'scars': scars}.items() if v and v.strip()}
        if identity_fields:
            db.set_wolf_identity(new_wolf_id, **identity_fields)
        lore_fields = {k: v for k, v in {'personality': (self.personality.value or '').strip(), 'backstory': (self.backstory.value or '').strip(), 'family_ties': (self.family_ties.value or '').strip(), 'open_plots': (self.open_plots.value or '').strip(), 'rp_sample': (self.rp_sample.value or '').strip()}.items() if v}
        if lore_fields:
            db.set_character_lore_fields(new_wolf_id, **lore_fields)
        if skill_keys or weakness_keys:
            from engine.character_traits import set_registration_traits
            for sk, val in skill_keys:
                set_registration_traits(new_wolf_id, skill_key=sk, skill_bonus=val)
            for wk, val in weakness_keys:
                set_registration_traits(new_wolf_id, weakness_attr_key=wk, weakness_penalty=val)
        # mods running /register (usually on a player's behalf, from a submitted
        # sheet) are trusted to skip the queue; a self-registering player's wolf
        # goes in pending so a mod can review (and, via /wolfadmin possess +
        # /character, edit) before it's approved.
        db.set_wolf_approval(new_wolf_id, 'approved' if is_admin else 'pending')
        from engine.patron import on_wolf_registered
        invite_note = None
        if interaction.guild:
            invite_note = on_wolf_registered(interaction.user.id, interaction.guild.id, first_wolf=wolf_count == 0)
        user = db.get_user(interaction.user.id)
        embed = howlbert_embed('Welcome to the Den', color=SUCCESS_COLOR)
        embed.add_field(name='Wolf', value=wolf_name, inline=True)
        embed.add_field(name='Birth Sex', value=BIRTH_SEX_LABELS.get(birth_sex, birth_sex.title()), inline=True)
        embed.add_field(name='Sexuality', value=SEXUALITY_LABELS.get(sexuality, sexuality.title()), inline=True)
        embed.add_field(name='Role', value=ROLE_LABELS.get(user['wolf_role'], user['wolf_role'].title()), inline=True)
        age_mo = user['age_months'] if 'age_months' in user.keys() else 24
        embed.add_field(name='Age', value=f'{format_wolf_age(age_mo)} ({stage_label(stage_for_age(age_mo))})', inline=True)
        if age_months is not None and user['wolf_role'] != role:
            embed.add_field(name='Age & Role', value=f"At **{format_wolf_age(age_mo)}** your wolf starts as **{ROLE_LABELS.get(user['wolf_role'], user['wolf_role'])}** (you picked **{ROLE_LABELS.get(role, role)}**).", inline=False)
        embed.add_field(name='Pack', value=_pack_display(pack), inline=False)
        belief_text = format_maw_belief(user)
        if belief_text:
            embed.add_field(name='Maw Belief', value=belief_text, inline=False)
        if user['wolf_role'] == 'drown_sick':
            oracle_blurb = 'Drown-Sick wolves are **Mistmoor oracles**; frail, prophetic, changed by the Belly-Rip. Use `/role action:event`, `/role action:prophecy`, and `/role action:quests`.'
            if stage_for_age(age_mo) == 'pup':
                oracle_blurb += ' You are still **under 6 moons**; mothers nurse via `/pupcare action:feed`; pack caretakers mash-feed; forbidden to hunt, fight, or mate.'
            embed.add_field(name="Oracle's Path", value=oracle_blurb, inline=False)
        elif user['wolf_role'] == 'pup':
            embed.add_field(name="Pup's Path", value='You are under **6 moons**; mothers nurse via `/pupcare action:feed`; pack caretakers mash-feed; forbidden to hunt, fight, or mate. Survive the first moon to be named. Use `/role action:event` and `/role action:quests`.', inline=False)
        elif user['wolf_role'] == 'juvenile':
            from engine.blooding import format_blooding_status, is_unblooded_juvenile
            blooding_line = format_blooding_status(user)
            juvenile_path = 'You are **6 to 24 moons**; practice hunting; your **blooding** comes on your first kill. Forbidden to mate. Complete role quests and `/role action:event` to grow toward an adult role.'
            if blooding_line:
                juvenile_path = blooding_line
            elif not is_unblooded_juvenile(user):
                juvenile_path = 'You are **6 to 24 moons** and **blooded**; role quests and `/role action:event` mark your path toward an adult role. Forbidden to mate.'
            embed.add_field(name="Juvenile's Path", value=juvenile_path, inline=False)
        if genetic_keys:
            from engine.genetics import format_genetic_conditions
            embed.add_field(name='Genetics', value=format_genetic_conditions(user), inline=False)
        if skill_keys or weakness_keys:
            trait_lines = []
            for sk, val in skill_keys:
                trait_lines.append(f"+{val} {SKILLS[sk][1]} (permanent, applies to real rolls)")
            for wk, val in weakness_keys:
                trait_lines.append(f"{val} {wk.replace('attr_', '').title()} (permanent, applies to real rolls)")
            if trait_lines:
                embed.add_field(name='Starting Traits', value='\n'.join(trait_lines), inline=False)
        if pack in GREAT_PACKS:
            faction = GREAT_PACKS[pack]
            embed.add_field(name='Motto', value=f"_{faction['motto']}_", inline=False)
            embed.add_field(name='Pack Trait', value=faction['pack_trait'], inline=False)
            herbs = ', '.join((HERBS[k]['name'] if k in HERBS else k.replace('_', ' ').title() for k in faction['starting_herbs']))
            embed.add_field(name='Starting Herbs', value=f'{herbs}\n_Added to `/bones action:inventory` (stable shop herbs). Foraged stacks use `/bones action:inventory`._', inline=False)
        elif pack not in (LONER_KEY, ROGUE_KEY):
            from engine.factions import founded_pack_heritage_trait, founded_pack_id, resolve_faction
            faction = resolve_faction(pack)
            if faction:
                embed.add_field(name='Motto', value=f"_{faction['motto']}_", inline=False)
                fpid = founded_pack_id(pack)
                trait = founded_pack_heritage_trait(fpid) if fpid else faction['pack_trait']
                embed.add_field(name='Pack Trait', value=trait, inline=False)
        else:
            embed.add_field(name='The Rogue Path', value='No pack treasury, tax, or trait; free to roam. Use `/setfaction` to join a Great Pack later.', inline=False)
        if is_admin:
            embed.add_field(name='Next Steps', value='Try `/profile` for your sheet, `/rpg action:roll` for skill checks, `/bones action:hunt` or `action:work` for bones.\nNew here? **`/help topic:getting-started`** walks through courtship, pups, and the den.', inline=False)
        else:
            embed.add_field(name='⏳ Pending Approval', value='A mod will review this wolf before it can play; you can still explore `/profile` and `/help topic:getting-started` in the meantime.', inline=False)
        if invite_note:
            embed.add_field(name='Invite Reward', value=invite_note, inline=False)
        total = db.count_user_wolves(interaction.user.id)
        slots = db.count_slot_wolves(interaction.user.id)
        born = db.count_born_pups(interaction.user.id)
        if total > 1:
            footer = f'Active wolf · {slots} of {MAX_WOLVES_PER_PLAYER} slots'
            if born:
                footer += f" (+ {born} born pup{('s' if born != 1 else '')})"
            footer += ' · use /switchwolf to change'
            embed.set_footer(text=footer)
        elif not is_admin:
            footer = f'Wolf {slots} of {MAX_WOLVES_PER_PLAYER}'
            if born:
                footer += f" (+ {born} born pup{('s' if born != 1 else '')})"
            footer += ' · /register again for another'
            embed.set_footer(text=footer)
        await interaction.response.send_message(embed=embed)
        from utils.views import make_arrival_scene_view

        is_pup = stage_for_age(age_mo) == 'pup'
        is_loner = pack in UNAFFILIATED_KEYS
        if is_pup and is_loner:
            scene_embed = howlbert_embed(
                'how were they born?',
                f"before **{wolf_name}** opens their eyes for good, no den walls around them yet.",
            )
        elif is_pup:
            scene_embed = howlbert_embed(
                'how were they born?',
                f"before **{wolf_name}** opens their eyes for good, the litter takes shape.",
            )
        else:
            scene_embed = howlbert_embed(
                'how did they arrive?',
                f"before **{wolf_name}** settles in, {'the wild watches them pass' if is_loner else 'the den watches them come'}.",
            )
        view = make_arrival_scene_view(user['id'], wolf_name, interaction.user.id, pup=is_pup, loner=is_loner)
        await interaction.followup.send(embed=scene_embed, view=view)


class Profile(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='register', description=f'Create a wolf (up to {MAX_WOLVES_PER_PLAYER} per player; admins unlimited).')
    @app_commands.describe(name="your wolf's name", pack='join a great pack, a founded pack, or walk as a lone wolf / rogue', birth_sex='birth sex (female, male, or intersex; affects conception)', sexuality='who your wolf is attracted to (pups: too young / none)', role="your wolf's role (sets starting attributes and skills)", starting_age='starting age in moons, 0 to 120 (optional; defaults from role)', genetic='optional rp genetics, comma-separated (blind, deaf, mute, albinism, missing_leg, …)', maw_belief='faith in the maw (defaults to orthodox for great pack wolves)', fur_color='coat color, short (optional; shows on /profile and inherited by pups)', eye_color='eye color, short (optional; shows on /profile and inherited by pups)', markings='natural coat patterns and markings, short (optional; shows on /profile)', scars='earned scars and old wounds, short (optional; shows on /profile)', trait_skill='bonus skills, comma-separated; add :N per skill (e.g. hunting:2, stealth); permanent', trait_skill_bonus='default bonus for skills without an inline :N, 0 to 5 (default 1)', trait_weakness='weak attributes, comma-separated; add :N per attr (e.g. strength:2, wisdom); permanent', trait_weakness_penalty='default penalty for weaknesses without inline :N, -5 to 0 (default -1)')
    @app_commands.autocomplete(pack=_pack_register_autocomplete)
    @app_commands.choices(birth_sex=[app_commands.Choice(name='female', value='female'), app_commands.Choice(name='male', value='male'), app_commands.Choice(name='intersex', value='intersex')], sexuality=[app_commands.Choice(name=choice_label(name), value=value) for name, value in SEXUALITY_OPTIONS], role=[app_commands.Choice(name=choice_label(ROLE_LABELS[key]), value=key) for key in ROLE_LABELS], maw_belief=[app_commands.Choice(name=choice_label(label), value=value) for label, value in MAW_BELIEF_OPTIONS])
    async def register(self, interaction: discord.Interaction, name: str, pack: str, birth_sex: str, sexuality: str, role: str='hunter', starting_age: app_commands.Range[int, 0, 120] | None=None, genetic: str | None=None, maw_belief: str | None=None, fur_color: str | None=None, eye_color: str | None=None, markings: str | None=None, scars: str | None=None, trait_skill: str | None=None, trait_skill_bonus: app_commands.Range[int, 0, 5]=1, trait_weakness: str | None=None, trait_weakness_penalty: app_commands.Range[int, -5, 0]=-1):
        wolf_count = db.count_slot_wolves(interaction.user.id)
        is_admin = is_howlbert_admin(interaction)
        if not is_admin and wolf_count >= MAX_WOLVES_PER_PLAYER:
            embed = howlbert_embed('Wolf Limit Reached', f'You already have **{MAX_WOLVES_PER_PLAYER}** wolves. Use `/switchwolf` to change active character, or `/rpg action:delete confirm:DELETE` to remove one.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        wolf_name, name_err = db.validate_wolf_name_available(name, label='Wolf names')
        if name_err:
            title = 'Name Taken' if 'already taken' in name_err else 'Invalid Name'
            embed = howlbert_embed(title, name_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.factions import is_faction
        if pack not in (LONER_KEY, ROGUE_KEY) and not is_faction(pack):
            embed = howlbert_embed('Unknown Pack', 'pick a pack from the autocomplete list; a great pack, a founded pack, lone wolf, or rogue.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        age_months = starting_age
        from engine.genetics import parse_genetic_register_input
        genetic_keys, genetic_err = parse_genetic_register_input(genetic)
        if genetic_err:
            embed = howlbert_embed('Invalid Genetics', genetic_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        skill_keys, weakness_keys, trait_err = _parse_register_traits(trait_skill, trait_weakness, trait_skill_bonus, trait_weakness_penalty)
        if trait_err:
            embed = howlbert_embed('Invalid Trait', trait_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        bonus_pts = sum(v for _, v in skill_keys)
        weak_pts = sum(abs(v) for _, v in weakness_keys)
        if bonus_pts > weak_pts:
            embed = howlbert_embed('Unbalanced Traits', f'starting skill bonuses (**+{bonus_pts}** total) must be paid for with at least as many weakness points (you have **{weak_pts}**). add more weaknesses (or a bigger penalty), or take fewer or smaller skill bonuses.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        modal = _RegisterLoreModal(params=dict(
            wolf_name=wolf_name, pack=pack, role=role, birth_sex=birth_sex, sexuality=sexuality,
            age_months=age_months, genetic_keys=genetic_keys, maw_belief=maw_belief,
            fur_color=fur_color, eye_color=eye_color, markings=markings, scars=scars,
            skill_keys=skill_keys, weakness_keys=weakness_keys,
            is_admin=is_admin, wolf_count=wolf_count,
        ))
        await interaction.response.send_modal(modal)

    @app_commands.command(name='wolves', description='list all wolves on your account.')
    async def wolves(self, interaction: discord.Interaction):
        rows = db.list_user_wolves(interaction.user.id)
        if not rows:
            embed = howlbert_embed('No Wolves', 'Use `/register` to create your first wolf.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        active_id = db.get_active_wolf_id(interaction.user.id)
        lines = []
        for w in rows:
            marker = ' ◀ active' if w['id'] == active_id else ''
            pack = db.get_user_affiliation(w)
            if pack == LONER_KEY:
                pack_label = LONER_LABEL
            elif pack == ROGUE_KEY:
                pack_label = ROGUE_LABEL
            else:
                pack_label = _pack_display(pack)
            lines.append(f"**{w['wolf_name']}**; {pack_label}{marker}")
        limit_note = 'unlimited' if is_howlbert_admin(interaction) else str(MAX_WOLVES_PER_PLAYER)
        footer = f'{len(rows)} wolf(s) · limit {limit_note} · /switchwolf to play as another' + (' · type a name if yours is not in the list' if len(rows) > 25 else '')
        page_size = 20
        if len(lines) <= page_size:
            embed = howlbert_embed('Your Wolves', '\n'.join(lines))
            embed.set_footer(text=footer)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        pages: list[discord.Embed] = []
        for start in range(0, len(lines), page_size):
            chunk = lines[start:start + page_size]
            page_num = start // page_size + 1
            page_total = (len(lines) + page_size - 1) // page_size
            embed = howlbert_embed(f'Your Wolves ({page_num}/{page_total})', '\n'.join(chunk))
            embed.set_footer(text=footer)
            pages.append(embed)
        view = _EmbedPaginator(pages=pages, owner_id=interaction.user.id)
        await interaction.response.send_message(embed=pages[0], view=view, ephemeral=reply_ephemeral())

    async def _own_wolf_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return await self._switchwolf_autocomplete(interaction, current)

    async def _switchwolf_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        rows = sorted(db.list_user_wolves(interaction.user.id), key=lambda w: w['wolf_name'].lower())
        needle = current.lower()
        choices = []
        for w in rows:
            if needle and needle not in w['wolf_name'].lower():
                continue
            choices.append(app_commands.Choice(name=choice_label(w['wolf_name']), value=w['wolf_name']))
        return choices[:25]

    @app_commands.command(name='switchwolf', description="switch which wolf you're playing as.")
    @app_commands.describe(name='wolf name to activate')
    @app_commands.autocomplete(name=_switchwolf_autocomplete)
    async def switchwolf(self, interaction: discord.Interaction, name: str):
        rows = db.list_user_wolves(interaction.user.id)
        if not rows:
            embed = howlbert_embed('No Wolves', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        match = next((w for w in rows if w['wolf_name'].lower() == name.strip().lower()), None)
        if not match:
            embed = howlbert_embed('Not Found', 'No wolf with that name on your account. Check `/wolves`.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if match['id'] == db.get_active_wolf_id(interaction.user.id):
            embed = howlbert_embed('Already Active', f"You're already playing as **{match['wolf_name']}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        db.set_active_wolf(interaction.user.id, match['id'])
        embed = howlbert_embed('Wolf Switched', f"You're now playing as **{match['wolf_name']}**.\nBones, inventory, quests, and cooldowns follow this wolf.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='setfaction', description='join a great pack, switch packs, or leave to walk as a lone wolf.')
    @app_commands.describe(pack='great pack to join, or lone wolf to leave pack life')
    @app_commands.choices(pack=PACK_CHOICES)
    async def setfaction(self, interaction: discord.Interaction, pack: str):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        current = db.get_user_affiliation(user)
        if current == pack:
            embed = howlbert_embed('No Change', f'You already walk as **{_pack_display(pack)}**.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        charge_bones = current not in UNAFFILIATED_KEYS and pack not in UNAFFILIATED_KEYS
        if charge_bones:
            if user['bones'] < SETFACTION_CHANGE_COST:
                embed = howlbert_embed('Not Enough Bones', f'Switching Great Packs costs {format_bones(SETFACTION_CHANGE_COST)}.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            db.deduct_bones(interaction.user.id, SETFACTION_CHANGE_COST)
        err = db.assign_pack_affiliation(interaction.user.id, pack, guild_id=interaction.guild.id if interaction.guild else None)
        if err:
            if charge_bones:
                db.add_bones(interaction.user.id, SETFACTION_CHANGE_COST)
            embed = howlbert_embed('Cannot Change Pack', err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Pack Updated', color=SUCCESS_COLOR)
        embed.add_field(name='Now', value=_pack_display(pack), inline=False)
        if pack in GREAT_PACKS:
            faction = GREAT_PACKS[pack]
            embed.add_field(name='Path', value=faction['path'], inline=True)
            embed.add_field(name='Motto', value=f"_{faction['motto']}_", inline=False)
        if current not in UNAFFILIATED_KEYS and pack not in UNAFFILIATED_KEYS:
            embed.set_footer(text=f'paid {format_bones(SETFACTION_CHANGE_COST)} to change great packs.')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='foundpack', description='two bonded lone wolves raise a den of their own (each pays bones; founder becomes alpha).')
    @app_commands.describe(name='the name of your new pack', partner='the bonded loner founding it with you')
    async def foundpack(self, interaction: discord.Interaction, name: str, partner: discord.User):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(embed=howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        partner_user = db.get_user(partner.id)
        if not partner_user:
            await interaction.response.send_message(embed=howlbert_embed('No Partner Wolf', f'**{partner.display_name}** has no active wolf.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.found_pack import found_pack
        _world = db.get_world(interaction.guild.id) if interaction.guild else None
        new_id, err = found_pack(
            user, partner_user, name,
            guild_id=interaction.guild.id if interaction.guild else None,
            day=_world['day_number'] if _world else None,
        )
        if err:
            await interaction.response.send_message(embed=howlbert_embed('Cannot Found a Pack', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from config import NEW_PACK_FOUND_COST
        embed = howlbert_embed(
            'A New Pack Rises',
            f"**{user['wolf_name']}** and **{partner_user['wolf_name']}** end their wandering and raise **{name.strip()}**. "
            f"**{user['wolf_name']}** leads as **alpha**.\n\neach paid **{NEW_PACK_FOUND_COST}** bones. you share a den now: "
            "`/pack treasury`, `/pack stash`, collab hunts, and `/packlife`. pups born to you join the pack.",
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text='the loner life is behind you; hold your unity and grow your numbers.')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='rename', description="change your wolf's name.")
    @app_commands.describe(name="your wolf's new name")
    async def rename(self, interaction: discord.Interaction, name: str):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', 'Use `/register` before renaming your wolf.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        new_name, error = validate_display_name(name, label='Wolf names')
        if error:
            embed = howlbert_embed('Invalid Name', error, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if new_name.lower() == user['wolf_name'].lower():
            embed = howlbert_embed('Same Name', f"You're already known as **{user['wolf_name']}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        err = db.rename_wolf(interaction.user.id, new_name)
        if err and err.startswith('name:'):
            body = err[5:]
            title = 'Name Taken' if 'already taken' in body else 'Invalid Name'
            embed = howlbert_embed(title, body, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        old_name = user['wolf_name']
        embed = howlbert_embed('Name Changed', color=SUCCESS_COLOR)
        embed.add_field(name='Was', value=old_name, inline=True)
        embed.add_field(name='Now', value=new_name, inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='character', description="set your wolf's identity: pronouns, sex, belief, size, age, or appearance.")
    @app_commands.describe(pronouns='pronouns, e.g. she/her, ey/em, fae/faer (defaults from lore or birth sex)', birthday="birthday text, e.g. 'early greenleaf' or a date", birth_sex='biological sex (affects conception checks)', sexuality='romantic/sexual attraction', maw_belief='faith in the maw', size='combat build size (auto = role/age default)', age_moons='age in moons, 0 to 120 (role and proficiencies re-sync to the new age)', fur_color='coat color, short (shows on /profile, inherited by pups)', eye_color='eye color, short (shows on /profile, inherited by pups)', markings='natural coat patterns and markings, short (shows on /profile)', scars='earned scars and old wounds, short (shows on /profile)', personality='personality prose (shows on /profile sheet:true)', personality2='more personality if it ran long (appended)', backstory='backstory prose (shows on /profile sheet:true)', backstory2='more backstory if it ran past the limit (appended)', rp_sample='a short writing sample (shows on /profile sheet:true)', family_ties='known family: parents, siblings, kin (shows on /profile sheet:true)', open_plots='hooks other players can pick up (shows on /profile sheet:true)', clear='clear a single field instead of setting it', own_wolf='which of your wolves (defaults to your active wolf)')
    @app_commands.choices(birth_sex=[app_commands.Choice(name='female', value='female'), app_commands.Choice(name='male', value='male'), app_commands.Choice(name='intersex', value='intersex')], sexuality=[app_commands.Choice(name=choice_label(name), value=value) for name, value in SEXUALITY_OPTIONS], maw_belief=[app_commands.Choice(name=choice_label(label), value=value) for label, value in MAW_BELIEF_OPTIONS], size=[app_commands.Choice(name='auto (role / age)', value='auto'), app_commands.Choice(name='small', value='small'), app_commands.Choice(name='medium', value='medium'), app_commands.Choice(name='large', value='large')], clear=[app_commands.Choice(name='pronouns', value='pronouns'), app_commands.Choice(name='birthday', value='birthday'), app_commands.Choice(name='birth sex', value='birth_sex'), app_commands.Choice(name='sexuality', value='sexuality'), app_commands.Choice(name='maw belief', value='maw_belief'), app_commands.Choice(name='combat size', value='size_class'), app_commands.Choice(name='fur color', value='fur_color'), app_commands.Choice(name='eye color', value='eye_color'), app_commands.Choice(name='markings', value='markings'), app_commands.Choice(name='scars', value='scars')])
    @app_commands.autocomplete(own_wolf=_own_wolf_autocomplete)
    async def character(self, interaction: discord.Interaction, pronouns: str | None=None, birthday: str | None=None, birth_sex: str | None=None, sexuality: str | None=None, maw_belief: str | None=None, size: str | None=None, age_moons: app_commands.Range[int, 0, 120] | None=None, fur_color: str | None=None, eye_color: str | None=None, markings: str | None=None, scars: str | None=None, personality: str | None=None, personality2: str | None=None, backstory: str | None=None, backstory2: str | None=None, rp_sample: str | None=None, family_ties: str | None=None, open_plots: str | None=None, clear: str | None=None, own_wolf: str | None=None):
        wolf = db.find_user_wolf(interaction.user.id, own_wolf) if own_wolf else db.get_user(interaction.user.id)
        if not wolf:
            msg = 'No wolf with that name on your account.' if own_wolf else 'Use `/register` first.'
            await interaction.response.send_message(embed=howlbert_embed('No Wolf', msg, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if clear:
            if clear in ('pronouns', 'birthday', 'fur_color', 'eye_color', 'markings', 'scars'):
                db.set_wolf_identity(wolf['id'], **{clear: None})
            else:
                db.update_user(wolf['discord_id'], wolf_id=wolf['id'], **{clear: None})
            await interaction.response.send_message(embed=howlbert_embed(wolf['wolf_name'], f"Cleared **{clear.replace('_', ' ')}**.", color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
            return
        updated_parts: list[str] = []
        if pronouns or birthday:
            fields: dict[str, str] = {}
            if pronouns:
                fields['pronouns'] = pronouns[:64]
            if birthday:
                fields['birthday'] = birthday[:48]
            db.set_wolf_identity(wolf['id'], **fields)
            updated_parts.extend(fields.keys())
        if fur_color or eye_color or markings or scars:
            appearance_fields = {k: v.strip()[:64] for k, v in {'fur_color': fur_color, 'eye_color': eye_color, 'markings': markings, 'scars': scars}.items() if v and v.strip()}
            db.set_wolf_identity(wolf['id'], **appearance_fields)
            updated_parts.extend(appearance_fields.keys())
        if personality or personality2 or backstory or backstory2 or rp_sample or family_ties or open_plots:
            personality_full = '\n\n'.join(p.strip() for p in (personality, personality2) if p and p.strip())
            backstory_full = '\n\n'.join(p.strip() for p in (backstory, backstory2) if p and p.strip())
            lore_fields = {k: v for k, v in {'personality': personality_full, 'backstory': backstory_full, 'family_ties': (family_ties or '').strip(), 'open_plots': (open_plots or '').strip(), 'rp_sample': (rp_sample or '').strip()}.items() if v}
            db.set_character_lore_fields(wolf['id'], **lore_fields)
            updated_parts.extend(lore_fields.keys())
        if birth_sex:
            db.update_user(wolf['discord_id'], wolf_id=wolf['id'], birth_sex=birth_sex)
            updated_parts.append('birth sex')
        if sexuality:
            from engine.attraction import validate_set_sexuality
            stored, err = validate_set_sexuality(wolf, sexuality)
            if err:
                await interaction.response.send_message(embed=howlbert_embed('Cannot Update', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            db.update_user(wolf['discord_id'], wolf_id=wolf['id'], sexuality=stored)
            label = SEXUALITY_LABELS.get(sexuality, sexuality.title())
            updated_parts.append(f'sexuality ({label})')
        if maw_belief:
            ok, err = db.set_maw_belief(wolf['discord_id'], maw_belief, wolf_id=wolf['id'])
            if not ok:
                await interaction.response.send_message(embed=howlbert_embed('Cannot Update', err or 'Invalid belief.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            updated_parts.append('maw belief')
        if size:
            ok, err = db.set_size_class(wolf['discord_id'], size, wolf_id=wolf['id'])
            if not ok:
                await interaction.response.send_message(embed=howlbert_embed('Cannot Update', err or 'Invalid size.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            updated_parts.append('combat size')
        age_result = None
        if age_moons is not None:
            age_result = db.set_wolf_age_moons(wolf['id'], age_moons)
            if not age_result:
                await interaction.response.send_message(embed=howlbert_embed('Cannot Update', 'Could not update age.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            updated_parts.append('age')
        if not updated_parts:
            await interaction.response.send_message(embed=howlbert_embed('Nothing to Update', 'Set at least one field, or use `clear`. Ref image is admin-set via `/wolfadmin refimage`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        updated = ', '.join(updated_parts)
        embed = howlbert_embed(wolf['wolf_name'], f'Updated **{updated}**. See `/profile`.', color=SUCCESS_COLOR)
        if age_result:
            from engine.attraction import is_pup_age
            embed.add_field(name='Age', value=f"**{format_wolf_age(age_result['old_age'])}** → **{format_wolf_age(age_result['new_age'])}** ({stage_label(stage_for_age(age_result['new_age']))})", inline=False)
            if age_result['new_role'] != age_result['old_role']:
                embed.add_field(name='Role', value=f"{ROLE_LABELS.get(age_result['old_role'], age_result['old_role'])} → **{ROLE_LABELS.get(age_result['new_role'], age_result['new_role'])}**", inline=False)
            for note in age_result['notes']:
                embed.add_field(name='Milestone', value=note, inline=False)
            if is_pup_age(age_result['new_age']):
                embed.set_footer(text='pup age; sexuality set to too young / none.')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @app_commands.command(name='family', description="show a wolf's family tree / relationship web as a diagram.")
    @app_commands.describe(member='whose family to show (defaults to you)', own_wolf='one of your wolves (defaults to your active wolf)', member_wolf="specific wolf from that player's roster")
    @app_commands.autocomplete(own_wolf=_own_wolf_autocomplete, member_wolf=_member_wolf_autocomplete)
    async def family(self, interaction: discord.Interaction, member: discord.Member | None=None, own_wolf: str | None=None, member_wolf: str | None=None):
        if own_wolf:
            wolf = db.find_user_wolf(interaction.user.id, own_wolf)
        elif member and member_wolf:
            wolf = db.find_user_wolf(member.id, member_wolf)
        elif member:
            wolf = db.get_user(member.id)
        else:
            wolf = db.get_user(interaction.user.id)
        if not wolf:
            await interaction.response.send_message(embed=howlbert_embed('No Wolf', 'No wolf found. Use `/register` first.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.family_tree import family_tree_image_url
        url, rel = family_tree_image_url(wolf, viewer_discord_id=interaction.user.id)
        if not url:
            await interaction.response.send_message(embed=howlbert_embed(f"{wolf['wolf_name']}'s Family", 'No recorded parents, mate, or offspring yet. Bonds form through `/courtship`, `/pupcare`, and `/bonds`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed(f"{wolf['wolf_name']}'s Family Tree", color=SUCCESS_COLOR)
        lineage = db.format_lineage_for_profile(wolf, viewer_discord_id=interaction.user.id)
        if lineage:
            embed.description = lineage
        wolf_avatar = wolf['avatar_url'] if 'avatar_url' in wolf.keys() else None
        if not wolf_avatar and interaction.guild:
            tree_member = interaction.guild.get_member(wolf['discord_id'])
            if tree_member:
                wolf_avatar = tree_member.display_avatar.url
        if wolf_avatar:
            embed.set_thumbnail(url=wolf_avatar)
        embed.set_image(url=url)
        embed.set_footer(text=f'{rel} relationship(s) · solid = blood, dashed = adopted')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='checklist', description="open setup and daily todos for your wolf (only what's still pending).")
    @app_commands.describe(wolf='which of your wolves (defaults to active)')
    @app_commands.autocomplete(wolf=_own_wolf_autocomplete)
    async def checklist(self, interaction: discord.Interaction, wolf: str | None=None):
        target = db.find_user_wolf(interaction.user.id, wolf) if wolf else db.get_user(interaction.user.id)
        if not target:
            msg = 'No wolf with that name on your account.' if wolf else 'Use `/register` first.'
            await interaction.response.send_message(embed=howlbert_embed('No Wolf', msg, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        await interaction.response.defer(ephemeral=reply_ephemeral())
        day = 0
        if interaction.guild_id:
            day = db.get_world(interaction.guild_id)['day_number']
        account = db.get_account(interaction.user.id)
        prestige_tier = int(account['prestige_tier']) if account else 0
        is_booster = bool(isinstance(interaction.user, discord.Member) and interaction.user.premium_since)
        from engine.donor import donor_daily_bonus
        donor_bonus = donor_daily_bonus(interaction.user.id)
        from engine.wolf_checklist import build_wolf_checklist
        body = build_wolf_checklist(target, day=day, guild_id=interaction.guild_id, prestige_tier=prestige_tier, is_booster=is_booster, donor_bonus=donor_bonus)
        if not body:
            body = 'Nothing on your list; caught up.'
            footer = 'Use `/checklist` for full sunrise timers.'
        else:
            footer = f'Day {day} · `/checklist` for timers' if day else None
        embed = howlbert_embed(f"{target['wolf_name']}'s Checklist", body)
        if footer:
            embed.set_footer(text=footer)
        await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

    @app_commands.command(name='profile', description="view a wolf's profile or character sheet.")
    @app_commands.describe(member='the wolf to look up (defaults to you)', sheet='show lore sheet (appearance, backstory)', own_wolf='one of your other wolves (sheet only; defaults to active wolf)', member_wolf="specific wolf from that player's roster")
    @app_commands.autocomplete(own_wolf=_own_wolf_autocomplete, member_wolf=_member_wolf_autocomplete)
    async def profile(self, interaction: discord.Interaction, member: discord.Member | None=None, sheet: bool=False, own_wolf: str | None=None, member_wolf: str | None=None):
        if sheet:
            await self._bio(interaction, member, own_wolf=own_wolf, member_wolf=member_wolf)
            return
        target = member or interaction.user
        if member and member_wolf:
            user = db.find_user_wolf(member.id, member_wolf)
        else:
            user = db.get_user(target.id)
        if not user:
            message = "You haven't registered yet. Use `/register` to create your wolf." if target == interaction.user else f"{target.display_name} hasn't registered a wolf yet."
            embed = howlbert_embed('No Profile Found', message, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        affiliation = db.get_user_affiliation(user)
        embed = howlbert_embed(user['wolf_name'])
        possess = db.get_possess_session(interaction.user.id)
        if possess and target == interaction.user:
            embed.description = f"_Admin steering **{user['wolf_name']}** (owner <@{possess['owner_discord_id']}>) · `/wolfadmin release` to stop._"
        wolf_avatar = user['avatar_url'] if 'avatar_url' in user.keys() else None
        embed.set_thumbnail(url=wolf_avatar or target.display_avatar.url)
        from engine.pronouns import wolf_pronouns as resolve_wolf_pronouns
        pronoun_line = resolve_wolf_pronouns(user)
        if pronoun_line:
            embed.add_field(name='Pronouns', value=pronoun_line, inline=True)
        wolf_role = user['wolf_role'] if 'wolf_role' in user.keys() else 'hunter'
        embed.add_field(name='Role', value=ROLE_LABELS.get(wolf_role, wolf_role.title()), inline=True)
        from engine.combat_size import format_size_class_profile
        embed.add_field(name='Build', value=format_size_class_profile(user), inline=True)
        age_mo = user['age_months'] if 'age_months' in user.keys() else 24
        embed.add_field(name='Age', value=f'{format_wolf_age(age_mo)} ({stage_label(stage_for_age(age_mo))})', inline=True)
        birth_moon = user['birth_lunar_phase'] if 'birth_lunar_phase' in user.keys() else ''
        if birth_moon:
            from engine.lunar import BIRTH_LUNAR_LABELS
            embed.add_field(name='Birth Moon', value=BIRTH_LUNAR_LABELS.get(birth_moon, birth_moon.replace('_', ' ').title()), inline=True)
        embed.add_field(name='Pack', value=_pack_display(affiliation), inline=True)
        bs = get_birth_sex(user)
        if bs:
            embed.add_field(name='Birth Sex', value=BIRTH_SEX_LABELS.get(bs, bs.title()), inline=True)
        orient = get_sexuality(user)
        embed.add_field(name='Sexuality', value=SEXUALITY_LABELS.get(orient, orient.title()), inline=True)
        belief_text = format_maw_belief(user)
        if belief_text:
            embed.add_field(name='Maw Belief', value=belief_text, inline=False)
        from engine.long_term_injuries import format_long_term_injuries
        lt_text = format_long_term_injuries(user)
        if lt_text:
            embed.add_field(name='Lasting Marks', value=lt_text, inline=False)
        wolf_birthday = user['birthday'] if 'birthday' in user.keys() else None
        if wolf_birthday:
            embed.add_field(name='Birthday', value=str(wolf_birthday), inline=True)
        appearance_bits = [user[k] for k in ('fur_color', 'eye_color', 'markings', 'scars') if k in user.keys() and user[k]]
        if appearance_bits:
            embed.add_field(name='Appearance', value=', '.join(appearance_bits), inline=False)
        wolf_bio = user['bio'] if 'bio' in user.keys() else None
        if wolf_bio:
            bio_text = wolf_bio if len(wolf_bio) <= 1024 else wolf_bio[:1021] + '…'
            embed.add_field(name='Bio', value=bio_text, inline=False)
        ic_loc = user['ic_location'] if 'ic_location' in user.keys() else None
        if ic_loc and str(ic_loc).strip():
            embed.add_field(name='Location', value=f'📍 {str(ic_loc).strip()}', inline=True)
        wolf_ref = user['ref_image_url'] if 'ref_image_url' in user.keys() else None
        if wolf_ref:
            embed.set_image(url=wolf_ref)
        if has_character_lore(user):
            embed.add_field(name='Character Sheet', value='Appearance, backstory, and RP sample on file; use `/profile sheet:true`.', inline=False)
        if 'approval_status' in user.keys() and user['approval_status'] == 'pending':
            embed.add_field(name='⏳ Pending Approval', value='a mod hasn\'t reviewed this wolf yet.', inline=False)
        if 'bonded_mate_id' in user.keys() and user['bonded_mate_id']:
            bonded = db.get_bonded_mate(user)
            if bonded:
                from engine.bonds import has_romance_bond
                is_fling = not has_romance_bond(user['id'], bonded['id'])
                field_name = 'Fling' if is_fling else 'Bonded Mate'
                embed.add_field(name=field_name, value=bonded['wolf_name'], inline=True)
        lineage = db.format_lineage_for_profile(user, viewer_discord_id=interaction.user.id)
        if lineage:
            embed.add_field(name='Family', value=lineage, inline=False)
        from engine.bonds import format_bonds_embed_body
        bonds_preview = format_bonds_embed_body(user)
        if bonds_preview and 'No bonds recorded yet' not in bonds_preview:
            if len(bonds_preview) > 1024:
                bonds_preview = bonds_preview[:1021] + '…\n_Use `/bonds` for the full list._'
            embed.add_field(name='Bonds', value=bonds_preview, inline=False)
        elif target == interaction.user:
            embed.add_field(name='Bonds', value='No bonds yet; `/playpen action:socialize`, `action:groom`, or `/bonds action:Set`.', inline=False)
        embed.add_field(name='Condition', value=user['condition'].title(), inline=True)

        def fmt_attr(key: str) -> str:
            score = user[key] if key in user.keys() else 5
            return f'{score} ({attr_modifier(score):+d})'
        embed.add_field(name='Attributes', value=f"STR {fmt_attr('attr_str')} · DEX {fmt_attr('attr_dex')} · CON {fmt_attr('attr_con')}\nINT {fmt_attr('attr_int')} · CHA {fmt_attr('attr_cha')} · WIS {fmt_attr('attr_wis')}", inline=False)
        if 'hp' in user.keys():
            from engine.character import format_max_hp_breakdown
            from engine.exhaustion_effects import effective_max_hp, user_exhaustion
            cap = effective_max_hp(user)
            str_val = int(user['attr_str']) if 'attr_str' in user.keys() else 5
            con_val = int(user['attr_con']) if 'attr_con' in user.keys() else 5
            hp_line = f"{user['hp']} / {cap}\n{format_max_hp_breakdown(str_val, con_val, max_hp=int(user['max_hp']))}"
            if user_exhaustion(user) >= 6:
                hp_line += f"\n_(exhaustion cap {cap}; base {user['max_hp']})_"
            embed.add_field(name='HP', value=hp_line, inline=True)
        from engine.character_traits import format_traits_for_profile, format_skill_strain_line
        strain_line = format_skill_strain_line(user)
        if strain_line:
            embed.add_field(name='Practice Strain', value=strain_line, inline=False)
        traits_text = format_traits_for_profile(user)
        if wolf_role in ROLE_FEATURES:
            from engine.role_features import bonus_feature_label
            role_text = ROLE_FEATURES[wolf_role]
            bonus = bonus_feature_label(user)
            if bonus:
                role_text += f'\n**Bonus feature:** {bonus}'
            embed.add_field(name='Role Feature', value=role_text, inline=False)
        if traits_text:
            if len(traits_text) > 1024:
                traits_text = traits_text[:1021] + '…'
            embed.add_field(name='Skills & Weaknesses', value=traits_text, inline=False)
        from engine.conditions import format_conditions
        day = None
        if interaction.guild_id:
            world = db.get_world(interaction.guild_id)
            if world:
                day = world['day_number']
        cond_text = format_conditions(user, day=day)
        from engine.role_features import is_full_medic
        if cond_text != 'Healthy: no active conditions.' or (is_full_medic(user) and day is not None):
            embed.add_field(name='Conditions', value=cond_text, inline=False)
        from engine.factions import founded_pack_heritage_trait, founded_pack_id, resolve_faction as _resolve_faction
        _faction_info = _resolve_faction(affiliation)
        if _faction_info:
            _fpid = founded_pack_id(affiliation)
            _trait = founded_pack_heritage_trait(_fpid) if _fpid else _faction_info['pack_trait']
            embed.add_field(name='Pack Trait', value=_trait, inline=False)
        # standing is a pack-reputation stat; loners and rogues have no pack, so hide it.
        if affiliation not in UNAFFILIATED_KEYS:
            standing = int(user['standing'])
            embed.add_field(name='Standing', value=f'**{standing}**\n{standing_effect_text(standing)}', inline=False)
        else:
            from engine.role_features import is_rogue_wolf
            if is_rogue_wolf(user):
                from engine.rogue_notoriety import notoriety_note
                _noto = notoriety_note(user)
                if _noto:
                    embed.add_field(name='Notoriety', value=_noto, inline=False)
        oath_breaks = db.oathbreaker_count(user)
        if oath_breaks:
            embed.add_field(
                name='Oathbreaker',
                value=f"**{oath_breaks}** treaty(s) personally broken; other dens remember `/pact action:forge` led by this wolf.",
                inline=False,
            )
        mood = int(user['mood']) if 'mood' in user.keys() else 75
        from config import MOOD_LOW_THRESHOLD
        from engine.hunger import format_hunger_line
        from engine.thirst import format_thirst_line
        from engine.energy import energy_line
        mood_note = '; play and socialize to lift it.' if mood < MOOD_LOW_THRESHOLD else ''
        embed.add_field(name='Vitals', value=f'**Mood** {mood}/100{mood_note}\n**Satiety** {format_hunger_line(user)}\n**Hydration** {format_thirst_line(user)}\n**Energy** {energy_line(user)}', inline=False)
        embed.add_field(name=CURRENCY_LABEL, value=format_bones(user['bones']), inline=True)
        account = db.get_account(target.id)
        tier = get_tier_info(account['prestige_tier'])
        xp = int(account['xp']) if account and 'xp' in account.keys() else 0
        prestige_value = f"Tier {tier['tier']}; {tier['name']} · **{xp}** account XP"
        if target == interaction.user and interaction.guild_id:
            from engine.chat_xp import format_chat_xp_status
            world = db.get_world(interaction.guild_id)
            if world:
                prestige_value += f"\n_{format_chat_xp_status(target.id, interaction.guild_id, world['day_number'])}_"
        embed.add_field(name='Prestige', value=prestige_value, inline=False)
        if target == interaction.user:
            slots = db.count_slot_wolves(target.id)
            born = db.count_born_pups(target.id)
            if slots > 1 or born:
                footer = f'Active wolf · {slots} of {MAX_WOLVES_PER_PLAYER} slots'
                if born:
                    footer += f" (+ {born} born pup{('s' if born != 1 else '')})"
                footer += ' · /switchwolf to change'
                badge = _profile_badges(target.id)
                if badge:
                    footer = f'{badge} · {footer}'
                embed.set_footer(text=footer)
            else:
                badge = _profile_badges(target.id)
                if badge:
                    embed.set_footer(text=badge)
        else:
            badge = _profile_badges(target.id)
            if badge:
                embed.set_footer(text=badge)
        trim_embed_fields(embed)
        pages = _paginate_embed_fields(embed, max_fields=25)
        if len(pages) == 1:
            await interaction.response.send_message(embed=embed)
            return
        view = _EmbedPaginator(pages=pages, owner_id=interaction.user.id)
        await interaction.response.send_message(embed=pages[0], view=view)

    async def _bio(self, interaction: discord.Interaction, member: discord.Member | None=None, *, own_wolf: str | None=None, member_wolf: str | None=None):
        if member and own_wolf:
            embed = howlbert_embed('Pick One', "Use **member** for another player's active wolf, or **own_wolf** for one of yours; not both.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if own_wolf:
            match = db.find_user_wolf(interaction.user.id, own_wolf)
            if not match:
                embed = howlbert_embed('Not Found', f'No wolf named **{own_wolf}** on your account. Check `/wolves`.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            user = db.get_user_by_id(match['id'])
            title_name = user['wolf_name'] if user else ''
            avatar = interaction.user.display_avatar.url
        else:
            target = member or interaction.user
            if member and member_wolf:
                user = db.find_user_wolf(member.id, member_wolf)
            else:
                user = db.get_user(target.id)
            title_name = user['wolf_name'] if user else ''
            avatar = target.display_avatar.url
        if not user:
            message = "You haven't registered yet. Use `/register` to create your wolf." if not member and (not own_wolf) else f"{(member or interaction.user).display_name} hasn't registered a wolf yet."
            embed = howlbert_embed('No Profile Found', message, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        fields = lore_embed_fields(user)
        if not fields:
            embed = howlbert_embed('No Lore Saved', f'**{title_name}** has no character sheet on file yet.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed(f'{title_name}; Character Sheet')
        art_path = canonical_art_path(title_name)
        if art_path:
            art_file = discord.File(art_path, filename=art_path.name)
            art_url = f'attachment://{art_path.name}'
            embed.set_image(url=art_url)
            embed.set_thumbnail(url=avatar)
            for name, value in fields:
                embed.add_field(name=name, value=value, inline=False)
            await interaction.response.send_message(embed=embed, files=[art_file])
            return
        embed.set_thumbnail(url=avatar)
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Profile(bot))