"""Body / visual language (`/sign`); how wolves speak without a voice.

Wolves communicate enormously through posture, ears, tail and hackles. `/sign`
lets any wolf broadcast a visual signal to their den; denmates can `/sign`
`read` to answer it. For a **mute** wolf (who cannot `/howl`) the rally signal
is a real stand-in for the howl, paying out extra pack unity.
"""

from __future__ import annotations

import random

import discord

import database as db
from config import (
    SIGN_ALERT_STANDING,
    SIGN_ALERT_UNITY,
    SIGN_CHALLENGE_LOSE_STANDING,
    SIGN_CHALLENGE_WIN_STANDING,
    SIGN_DIMINISH_FACTOR,
    SIGN_DIMINISH_FLOOR,
    SIGN_DIMINISH_WINDOW_MINUTES,
    SIGN_FREEZE_STANDING,
    SIGN_GREET_MOOD,
    SIGN_GRIEVE_MOOD_SELF,
    SIGN_GRIEVE_MOOD_TARGET,
    SIGN_GRIEVE_UNITY,
    SIGN_PLAY_MOOD,
    SIGN_PLAY_UNITY,
    SIGN_RALLY_STANDING,
    SIGN_RALLY_UNITY_MUTE,
    SIGN_RALLY_UNITY_NORMAL,
    SIGN_READ_MOOD,
    SIGN_READ_RALLY_UNITY,
    SIGN_READ_STANDING,
    SIGN_SOOTHE_MOOD_SELF,
    SIGN_SOOTHE_MOOD_TARGET,
    SIGN_SOOTHE_UNITY,
    SIGN_SUBMIT_MOOD_SELF,
    SIGN_SUBMIT_MOOD_TARGET,
    SIGN_SUBMIT_UNITY,
    SIGN_THREATEN_BACKFIRE_CHANCE,
    SIGN_THREATEN_BACKFIRE_MOOD,
    SIGN_THREATEN_BACKFIRE_STANDING,
    SIGN_THREATEN_STANDING,
    SIGN_THREATEN_TARGET_MOOD,
    SIGN_THREATEN_UNITY,
    SIGN_TRACK_MOOD,
    SIGN_TRACK_UNITY,
)
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from utils.replies import reply_ephemeral

# scope: "pack" (broadcast, no target), "target" (directed), "either"
SIGNAL_CATALOG: dict[str, dict] = {
    "alert": {
        "name": "Alert",
        "scope": "pack",
        "summary": "Warn the den of danger.",
        "posture": (
            "ears pricked hard forward, body gone still and tall, tail held stiff",
            "muzzle snapping toward the treeline, hackles half-raised, every muscle wired",
            "a sharp freeze mid-step, weight back on the haunches, gaze locked and unblinking",
        ),
    },
    "rally": {
        "name": "Rally",
        "scope": "pack",
        "summary": "Gather and lift the pack (a mute wolf's stand-in for a howl).",
        "posture": (
            "standing tall at the den-mouth, tail sweeping a slow arc, gaze gathering every wolf in",
            "chest out, head high, weaving among the pack to press flank to flank",
            "a rolling shoulder-shrug and lifted muzzle that pulls the den into one shape",
        ),
    },
    "play": {
        "name": "Play-bow",
        "scope": "either",
        "summary": "Invite a romp; lifts the mood.",
        "posture": (
            "front legs splayed flat, rump high, tail whipping in loose figure-eights",
            "a bouncing dip and spring, jaws wide in a loll-tongued grin",
            "a play-bow, paw-bat, and a dart sideways daring a chase",
        ),
    },
    "submit": {
        "name": "Submit",
        "scope": "target",
        "summary": "Appease and de-escalate; lowers tension.",
        "posture": (
            "body sunk low, ears pinned flat, tail tucked, throat bared in deference",
            "a slow belly-roll, paws limp, eyes averted soft and unthreatening",
            "muzzle-licking and a crouching wriggle, all the fight drained out of the line",
        ),
    },
    "soothe": {
        "name": "Soothe",
        "scope": "target",
        "summary": "Comfort a denmate; calms and steadies.",
        "posture": (
            "a gentle muzzle-nudge along the cheek, slow blinks, body curled in close",
            "warm grooming at the ears and a low, steady lean of shoulder against shoulder",
            "a soft chin rested over the withers, breathing slowed to match theirs",
        ),
    },
    "threaten": {
        "name": "Threaten",
        "scope": "target",
        "summary": "A dominance display; risky, it can backfire.",
        "posture": (
            "hackles up in a ridge, lips peeled off white teeth, legs stiff and squared",
            "a hard direct stare, tail flagged high, weight rolled forward over the toes",
            "a low growl-stance, ears forward and aggressive, body angled to loom larger",
        ),
    },
    "freeze": {
        "name": "Freeze",
        "scope": "pack",
        "summary": "Silent danger crouch; quieter than alert, for when sound could give you away.",
        "posture": (
            "a sudden, total stillness, one paw lifted mid-step, breath held",
            "body dropped low to the ground, ears flat, eyes fixed without blinking",
            "weight gone dead still, tail clamped flat, nothing moving but the nose",
        ),
    },
    "track": {
        "name": "Track",
        "scope": "either",
        "summary": "Point out a scent trail; rallies a hunt or patrol without a word.",
        "posture": (
            "nose pinned to a thread of scent, tail flagged stiff in the direction it runs",
            "a held point, muzzle low, one ear cocked back to see who follows",
            "a tight figure-eight over the trail, then a hard look toward the line it leads",
        ),
    },
    "greet": {
        "name": "Greet",
        "scope": "either",
        "summary": "A warm hello; ears back, tail low and loose.",
        "posture": (
            "ears pinned back soft, tail sweeping low, a happy full-body wiggle",
            "a muzzle-nuzzle and a play-soft nip at the jaw, tail going like a metronome",
            "a low, pleased whine and a face pushed up under another's chin",
        ),
    },
    "grieve": {
        "name": "Grieve",
        "scope": "either",
        "summary": "Mourn openly; a held vigil, alone or beside another.",
        "posture": (
            "head low, tail still, a long unmoving stare at nothing in particular",
            "a slow lie-down beside the loss, chin on paws, breath gone shallow and even",
            "a single low keen, cut short, fur gone dull and unkept for the moment",
        ),
    },
    "challenge": {
        "name": "Challenge",
        "scope": "target",
        "summary": "A formal duel invitation; ritual, not a binding rite on its own.",
        "posture": (
            "a stiff-legged circle, tail flagged high, daring the other to break first",
            "head and tail both raised level with the spine, a slow stalking approach",
            "a hard shoulder-check that stops just short of contact, eyes never leaving theirs",
        ),
    },
}

TARGET_REQUIRED = {key for key, info in SIGNAL_CATALOG.items() if info["scope"] == "target"}
PACK_WIDE = {key for key, info in SIGNAL_CATALOG.items() if info["scope"] == "pack"}
EITHER_SCOPE = {key for key, info in SIGNAL_CATALOG.items() if info["scope"] == "either"}


def signal_choices() -> list[tuple[str, str]]:
    """(label, key) pairs for the command choice list."""
    return [(info["name"], key) for key, info in SIGNAL_CATALOG.items()]


def wolf_is_silenced(user) -> tuple[bool, str]:
    """true if a trait or genetic condition stops this wolf from howling."""
    from engine.character_traits import trait_blocks_howl
    from engine.genetics import genetic_blocks_howl

    blocked, name = trait_blocks_howl(user)
    if blocked:
        return True, name
    return genetic_blocks_howl(user)


def _posture(signal_key: str) -> str:
    return random.choice(SIGNAL_CATALOG[signal_key]["posture"])


def _standing_field(kick: str, delta: int) -> str:
    if kick == "kicked":
        return "**cast out**; loner"
    if kick == "broken_rite":
        return "**rite of the broken canine**"
    return f"{'+' if delta >= 0 else ''}{delta}"


def _resolve_target(interaction, user, wolf, own_wolf) -> tuple[object | None, str | None]:
    """Resolve a directed-signal target; returns (target_row, error_message)."""
    if wolf and own_wolf:
        return None, "pick either another **player** or `own_wolf`; not both."
    if own_wolf:
        rows = db.list_user_wolves(interaction.user.id)
        target = next(
            (w for w in rows if w["wolf_name"].lower() == own_wolf.strip().lower()), None
        )
        if not target:
            return None, "no wolf with that name on your account. check `/wolves`."
        if target["id"] == user["id"]:
            return None, "you can't sign at yourself; pick another wolf."
        return target, None
    if wolf:
        if wolf.bot or wolf.id == interaction.user.id:
            return None, "pick another **player**, or your other wolf via `own_wolf`."
        target = db.get_user(wolf.id)
        if not target:
            return None, "they haven't registered a wolf."
        return target, None
    return None, "__no_target__"


NPC_CAPABLE_SIGNALS = {"submit", "soothe", "threaten", "greet", "grieve", "challenge"}


def apply_signal_to_target(signal_key: str, target, *, npc_id: int | None = None) -> str:
    """
    Apply a directed signal's real mechanical effect to its target only (no
    signer-side state to touch). Used by `/npc sign`, since non-wolf NPCs and
    foreign-tongue animals have no mood/standing of their own to update, but
    the wolf on the receiving end is a real game character either way.

    `/npc sign` isn't admin-gated, so pass `npc_id` to apply the same
    diminishing-returns guard as wolf-to-wolf signing (otherwise a player
    could spam any NPC at their own wolf for free, unlimited mood).
    """
    mult = 1.0
    if npc_id is not None:
        streak = db.bump_npc_sign_streak(npc_id, target["id"], window_minutes=SIGN_DIMINISH_WINDOW_MINUTES)
        mult = max(SIGN_DIMINISH_FLOOR, SIGN_DIMINISH_FACTOR ** (streak - 1))

    def _scaled(value: int) -> int:
        if value == 0 or mult >= 1.0:
            return value
        scaled = round(value * mult)
        return scaled if scaled != 0 else (1 if value > 0 else -1)

    if signal_key == "threaten":
        if random.random() < SIGN_THREATEN_BACKFIRE_CHANCE:
            return f"**{target['wolf_name']}** holds their ground; the bluff doesn't land."
        db.update_user_by_id(target["id"], distressed=1)
        mood = db.adjust_mood(target["id"], _scaled(SIGN_THREATEN_TARGET_MOOD))
        return f"**{target['wolf_name']}** flinches and gives ground (mood **{mood}**)."

    if signal_key == "soothe":
        db.update_user_by_id(target["id"], distressed=0)
        mood = db.adjust_mood(target["id"], _scaled(SIGN_SOOTHE_MOOD_TARGET))
        return f"**{target['wolf_name']}** settles; their fear quiets (mood **{mood}**)."

    if signal_key == "submit":
        mood = db.adjust_mood(target["id"], _scaled(SIGN_SUBMIT_MOOD_TARGET))
        return f"**{target['wolf_name']}** eases off; the tension drains (mood **{mood}**)."

    if signal_key == "greet":
        mood = db.adjust_mood(target["id"], _scaled(SIGN_GREET_MOOD))
        return f"**{target['wolf_name']}** brightens at the gesture (mood **{mood}**)."

    if signal_key == "grieve":
        db.update_user_by_id(target["id"], distressed=0)
        mood = db.adjust_mood(target["id"], _scaled(SIGN_GRIEVE_MOOD_TARGET))
        line = f"**{target['wolf_name']}** is less alone in it (mood **{mood}**)."
        from engine.diseases import parse_disease

        key, _stage = parse_disease(target["disease"] if "disease" in target.keys() else None)
        if key == "grief_melancholy":
            db.set_user_conditions(int(target["discord_id"]), wolf_id=target["id"], clear_disease=True)
            line += " _their grief breaks loose._"
        return line

    if signal_key == "challenge":
        from engine.character import attr_modifier
        from engine.dice import roll_d20

        them_total = roll_d20() + attr_modifier(int(target["attr_str"])) + attr_modifier(int(target["attr_cha"]))
        wild_total = roll_d20() + 1
        if wild_total >= them_total:
            db.adjust_wolf_standing_by_id(target["id"], SIGN_CHALLENGE_LOSE_STANDING)
            return f"**{them_total}** vs the wild's **{wild_total}**; **{target['wolf_name']}** gives ground (standing **{SIGN_CHALLENGE_LOSE_STANDING}**)."
        db.adjust_wolf_standing_by_id(target["id"], SIGN_CHALLENGE_WIN_STANDING)
        return f"**{them_total}** vs the wild's **{wild_total}**; **{target['wolf_name']}** holds the line (standing **+{SIGN_CHALLENGE_WIN_STANDING}**)."

    return ""


async def execute_sign(
    interaction: discord.Interaction,
    signal_key: str,
    *,
    wolf: discord.Member | None = None,
    own_wolf: str | None = None,
    message: str | None = None,
) -> None:
    """Broadcast a body-language signal to the den."""
    user = db.get_user(interaction.user.id)
    if not user:
        await interaction.response.send_message(
            embed=howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR),
            ephemeral=reply_ephemeral(),
        )
        return
    if not interaction.guild:
        await interaction.response.send_message("use this in a server.", ephemeral=reply_ephemeral())
        return

    info = SIGNAL_CATALOG.get(signal_key)
    if not info:
        await interaction.response.send_message(
            embed=howlbert_embed("unknown signal", "pick a signal from the list.", color=ERROR_COLOR),
            ephemeral=reply_ephemeral(),
        )
        return

    world = db.get_world(interaction.guild.id)
    day = int(world["day_number"])
    wolf_name = user["wolf_name"]

    pack_id = int(user["pack_id"]) if user["pack_id"] else 0

    # Resolve target for directed signals (and optional for either-scope signals).
    target = None
    if signal_key in TARGET_REQUIRED or (signal_key in EITHER_SCOPE and (wolf or own_wolf)):
        target, err = _resolve_target(interaction, user, wolf, own_wolf)
        if err == "__no_target__":
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "no target",
                    f"**{info['name']}** is aimed at a denmate; pick a **player** or `own_wolf`.",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return
        if err:
            await interaction.response.send_message(
                embed=howlbert_embed("pick a target", err, color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        if signal_key != "greet" and (not pack_id or int(target["pack_id"] or 0) != pack_id):
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "not packmates",
                    "you can only sign at wolves in the **same den** (greet works across packs).",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

    silenced, silence_label = wolf_is_silenced(user)
    posture = _posture(signal_key)
    lines = [f"**{wolf_name}** {posture}."]
    fields: list[tuple[str, str, bool]] = []
    footer_bits: list[str] = []

    standing_delta = 0
    unity_delta = 0
    target_id = target["id"] if target else None

    mood_mult = 1.0
    if target:
        streak = db.bump_sign_partner_streak(
            user["id"], target["id"], window_minutes=SIGN_DIMINISH_WINDOW_MINUTES
        )
        mood_mult = max(SIGN_DIMINISH_FLOOR, SIGN_DIMINISH_FACTOR ** (streak - 1))
        if streak > 1:
            footer_bits.append(f"repeat sign on this partner within {SIGN_DIMINISH_WINDOW_MINUTES}m: mood payout x{mood_mult:.2f}")

    def _scaled(value: int) -> int:
        if value == 0 or mood_mult >= 1.0:
            return value
        scaled = round(value * mood_mult)
        if scaled == 0:
            scaled = 1 if value > 0 else -1
        return scaled

    if signal_key == "rally":
        lines.append("_the pack reads the call to gather._")
        standing_delta = SIGN_RALLY_STANDING
        if pack_id:
            unity_delta = SIGN_RALLY_UNITY_MUTE if silenced else SIGN_RALLY_UNITY_NORMAL
            if silenced:
                footer_bits.append(f"{silence_label}: body-rally replaces your howl")
        else:
            lines.append("_no den answers a lone rally._")

    elif signal_key == "alert":
        lines.append("_heads snap up across the den; everyone is watching now._")
        standing_delta = SIGN_ALERT_STANDING
        if pack_id:
            unity_delta = SIGN_ALERT_UNITY

    elif signal_key == "play":
        your_mood = db.adjust_mood(user["id"], _scaled(SIGN_PLAY_MOOD))
        if target:
            their_mood = db.adjust_mood(target["id"], _scaled(SIGN_PLAY_MOOD))
            lines.append(
                f"**{target['wolf_name']}** bounces back into it; "
                f"mood each (you: **{your_mood}**, them: **{their_mood}**)."
            )
        else:
            lines.append(f"the den loosens up; **+{SIGN_PLAY_MOOD} mood** (you: **{your_mood}**).")
        if pack_id:
            unity_delta = SIGN_PLAY_UNITY

    elif signal_key == "submit":
        db.update_user_by_id(user["id"], distressed=0)
        your_mood = db.adjust_mood(user["id"], _scaled(SIGN_SUBMIT_MOOD_SELF))
        their_mood = db.adjust_mood(target["id"], _scaled(SIGN_SUBMIT_MOOD_TARGET))
        lines.append(
            f"**{target['wolf_name']}** eases off; the tension drains out of you both "
            f"(you: **{your_mood}** mood, them: **{their_mood}**)."
        )
        if pack_id:
            unity_delta = SIGN_SUBMIT_UNITY

    elif signal_key == "soothe":
        db.update_user_by_id(target["id"], distressed=0)
        their_mood = db.adjust_mood(target["id"], _scaled(SIGN_SOOTHE_MOOD_TARGET))
        your_mood = db.adjust_mood(user["id"], _scaled(SIGN_SOOTHE_MOOD_SELF))
        lines.append(
            f"**{target['wolf_name']}** settles under you; their fear quiets "
            f"(mood → **{their_mood}**; you: **{your_mood}**)."
        )
        if pack_id:
            unity_delta = SIGN_SOOTHE_UNITY

    elif signal_key == "threaten":
        if random.random() < SIGN_THREATEN_BACKFIRE_CHANCE:
            db.update_user_by_id(user["id"], distressed=1)
            your_mood = db.adjust_mood(user["id"], _scaled(SIGN_THREATEN_BACKFIRE_MOOD))
            standing_delta = SIGN_THREATEN_BACKFIRE_STANDING
            unity_delta = SIGN_THREATEN_UNITY if pack_id else 0
            lines.append(
                f"**{target['wolf_name']}** does **not** yield; they hold your stare and "
                f"the bluff curdles (your mood **{your_mood}**)."
            )
        else:
            db.update_user_by_id(target["id"], distressed=1)
            their_mood = db.adjust_mood(target["id"], _scaled(SIGN_THREATEN_TARGET_MOOD))
            standing_delta = SIGN_THREATEN_STANDING
            unity_delta = SIGN_THREATEN_UNITY if pack_id else 0
            lines.append(
                f"**{target['wolf_name']}** flinches and gives ground "
                f"(their mood **{their_mood}**); but the den feels the friction."
            )

    elif signal_key == "freeze":
        db.update_user(interaction.user.id, last_freeze_at=db.utcnow(), wolf_id=user["id"])
        from config import SIGN_FREEZE_AMBUSH_WINDOW_MINUTES

        lines.append(
            f"_the den drops silent and still; whatever's out there doesn't hear a sound. "
            f"ambush odds drop for the next **{SIGN_FREEZE_AMBUSH_WINDOW_MINUTES} min** "
            f"on hunt, explore, or patrol._"
        )
        standing_delta = SIGN_FREEZE_STANDING

    elif signal_key == "track":
        if int(user["last_track_day"]) >= day:
            unity_delta = SIGN_TRACK_UNITY if pack_id else 0
            your_mood = db.adjust_mood(user["id"], _scaled(SIGN_TRACK_MOOD))
            if target:
                their_mood = db.adjust_mood(target["id"], _scaled(SIGN_TRACK_MOOD))
                lines.append(
                    f"**{target['wolf_name']}** picks up the line with you; "
                    f"today's trail, shared (you: **{your_mood}**, them: **{their_mood}**)."
                )
            else:
                lines.append(f"the den falls in on today's trail; **+{SIGN_TRACK_MOOD} mood** (you: **{your_mood}**).")
        else:
            lines.append("_no fresh trail to share; sign means more after `/field action:track` finds one._")

    elif signal_key == "greet":
        # Mood-only, deliberately: pack-relation standing already has a real,
        # cooldown-gated lever in `/pack share` (+1, once/sunrise per pair).
        # Signing has no cooldown, so greet must never move pack_relations or
        # it becomes free, unlimited diplomacy farming.
        your_mood = db.adjust_mood(user["id"], _scaled(SIGN_GREET_MOOD))
        if target:
            their_mood = db.adjust_mood(target["id"], _scaled(SIGN_GREET_MOOD))
            if int(target["pack_id"] or 0) != pack_id:
                lines.append(
                    f"**{target['wolf_name']}** (a different den) eases at the gesture "
                    f"(you: **{your_mood}**, them: **{their_mood}**); "
                    f"_for real standing, dens still need `/pack share`._"
                )
            else:
                lines.append(
                    f"**{target['wolf_name']}** brightens at the hello "
                    f"(you: **{your_mood}**, them: **{their_mood}**)."
                )
        else:
            lines.append(f"a friendly hello to whoever's near; **+{SIGN_GREET_MOOD} mood** (you: **{your_mood}**).")

    elif signal_key == "grieve":
        your_mood = db.adjust_mood(user["id"], _scaled(SIGN_GRIEVE_MOOD_SELF))
        if target:
            db.update_user_by_id(target["id"], distressed=0)
            their_mood = db.adjust_mood(target["id"], _scaled(SIGN_GRIEVE_MOOD_TARGET))
            lines.append(
                f"**{target['wolf_name']}** grieves beside you, less alone in it "
                f"(them: **{their_mood}** mood, you: **{your_mood}**)."
            )
            from engine.diseases import parse_disease

            key, _stage = parse_disease(target["disease"] if "disease" in target.keys() else None)
            if key == "grief_melancholy":
                db.set_user_conditions(int(target["discord_id"]), wolf_id=target["id"], clear_disease=True)
                lines.append(f"_held vigil eases **{target['wolf_name']}**'s grief loose._")
            if pack_id:
                unity_delta = SIGN_GRIEVE_UNITY
        else:
            lines.append(f"a held vigil, alone; **+{SIGN_GRIEVE_MOOD_SELF} mood** (you: **{your_mood}**).")
            from engine.diseases import parse_disease

            key, _stage = parse_disease(user["disease"] if "disease" in user.keys() else None)
            if key == "grief_melancholy":
                db.set_user_conditions(interaction.user.id, wolf_id=user["id"], clear_disease=True)
                lines.append("_the grief breaks loose, at least for now._")

    elif signal_key == "challenge":
        from engine.character import attr_modifier
        from engine.dice import roll_d20

        you_total = roll_d20() + attr_modifier(int(user["attr_str"])) + attr_modifier(int(user["attr_cha"]))
        them_total = roll_d20() + attr_modifier(int(target["attr_str"])) + attr_modifier(int(target["attr_cha"]))
        if you_total >= them_total:
            standing_delta = SIGN_CHALLENGE_WIN_STANDING
            db.adjust_wolf_standing_by_id(target["id"], SIGN_CHALLENGE_LOSE_STANDING)
            lines.append(
                f"**{you_total}** vs **{target['wolf_name']}**'s **{them_total}**; "
                f"**{wolf_name}** holds the ground."
            )
        else:
            standing_delta = SIGN_CHALLENGE_LOSE_STANDING
            db.adjust_wolf_standing_by_id(target["id"], SIGN_CHALLENGE_WIN_STANDING)
            lines.append(
                f"**{you_total}** vs **{target['wolf_name']}**'s **{them_total}**; "
                f"**{target['wolf_name']}** holds the ground."
            )
        lines.append("_a rank dispute, not the rite; the alpha's seat is untouched._")

    # Apply pack unity + standing.
    if unity_delta and pack_id:
        db.adjust_pack_unity(pack_id, unity_delta)
        fields.append(("den unity", f"{'+' if unity_delta >= 0 else ''}{unity_delta}", True))
    if standing_delta:
        kick = db.adjust_wolf_standing(interaction.user.id, standing_delta)
        fields.append(("standing", _standing_field(kick, standing_delta), True))
        from engine.broken_canine import standing_expulsion_note

        note = standing_expulsion_note(kick, pack_id or None)
        if note:
            lines.append(note)

    if pack_id:
        db.record_pack_signal(
            interaction.guild.id, pack_id, user["id"], signal_key, day, target_id
        )

    if message:
        lines.append(f"\n_{message.strip()}_")

    color = ERROR_COLOR if signal_key == "threaten" else SUCCESS_COLOR
    embed = howlbert_embed(f"sign · {info['name']}", "\n".join(lines), color=color)
    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)
    if signal_key in PACK_WIDE and pack_id:
        footer_bits.append("denmates can answer with /sign signal:read")
    embed.set_footer(text=" · ".join(footer_bits) if footer_bits else "/sign signal:read to answer denmates")
    await interaction.response.send_message(embed=embed)


async def execute_read(interaction: discord.Interaction) -> None:
    """Read and answer the most recent body-language signal in your den."""
    user = db.get_user(interaction.user.id)
    if not user:
        await interaction.response.send_message(
            embed=howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR),
            ephemeral=reply_ephemeral(),
        )
        return
    if not interaction.guild:
        await interaction.response.send_message("use this in a server.", ephemeral=reply_ephemeral())
        return

    pack_id = int(user["pack_id"]) if user["pack_id"] else 0
    if not pack_id:
        await interaction.response.send_message(
            embed=howlbert_embed(
                "no den",
                "you have no den to read; join a great pack with `/setfaction`.",
                color=ERROR_COLOR,
            ),
            ephemeral=reply_ephemeral(),
        )
        return

    world = db.get_world(interaction.guild.id)
    day = int(world["day_number"])

    if int(user["last_sign_read_day"]) >= day:
        embed = howlbert_embed(
            "already answered",
            "you've already read and answered the den's signs this sunrise.",
            color=ERROR_COLOR,
        )
        embed.set_footer(text="resets next sunrise · /world action:cooldowns")
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    signal = db.get_readable_pack_signal(interaction.guild.id, pack_id, day, user["id"])
    if not signal:
        await interaction.response.send_message(
            embed=howlbert_embed(
                "den is quiet",
                "no new body-language to read in your den this sunrise.",
                color=ERROR_COLOR,
            ),
            ephemeral=reply_ephemeral(),
        )
        return

    info = SIGNAL_CATALOG.get(signal["signal_key"], {"name": signal["signal_key"]})
    signaler = db.get_user_by_id(int(signal["signaler_id"]))
    signaler_name = signaler["wolf_name"] if signaler else "a denmate"

    your_mood = db.adjust_mood(user["id"], SIGN_READ_MOOD)
    lines = [
        f"**{user['wolf_name']}** reads **{signaler_name}**'s **{info['name']}** and answers in kind.",
        f"**+{SIGN_READ_MOOD} mood** → **{your_mood}**.",
    ]
    fields: list[tuple[str, str]] = [("Mood", f"+{SIGN_READ_MOOD}")]

    if signal["signal_key"] == "rally":
        db.adjust_pack_unity(pack_id, SIGN_READ_RALLY_UNITY)
        kick = db.adjust_wolf_standing(interaction.user.id, SIGN_READ_STANDING)
        lines.append(f"you join the rally; den unity **+{SIGN_READ_RALLY_UNITY}**.")
        fields.append(("den unity", f"+{SIGN_READ_RALLY_UNITY}"))
        fields.append(("standing", _standing_field(kick, SIGN_READ_STANDING)))

    db.mark_signal_responded(int(signal["id"]), user["id"])
    db.update_user(interaction.user.id, last_sign_read_day=day)

    embed = howlbert_embed("sign · read", "\n".join(lines), color=SUCCESS_COLOR)
    for name, value in fields:
        embed.add_field(name=name, value=value, inline=True)
    embed.set_footer(text="once per sunrise · /world action:cooldowns")
    await interaction.response.send_message(embed=embed)
