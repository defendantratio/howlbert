"""Random wilderness ambushes; rolled threats, not hand-picked from the bestiary."""

from __future__ import annotations

import random

import database as db
from config import (
    EXPLORE_WILD_ENCOUNTER_CHANCE,
    HUNT_WILD_ENCOUNTER_CHANCE,
    SIGN_FREEZE_AMBUSH_MULTIPLIER,
    SIGN_FREEZE_AMBUSH_WINDOW_MINUTES,
    WILD_ENCOUNTER_COOLDOWN_MINUTES,
)
from config import COLLAB_PATROL_AMBUSH_CHANCE
from engine.bestiary import BESTIARY_NPCS, npc_hp
from engine.time_cooldowns import cooldown_minutes_remaining

# Weighted table; excludes legendary prey-only entries (grizzly, large_prey, fighting hearth-hounds).
WILD_ENCOUNTER_WEIGHTS: tuple[tuple[str, int], ...] = (
    ("coyote", 24),
    ("fox", 20),
    ("dog_feral", 14),
    ("badger", 11),
    ("wolverine", 9),
    ("rogue_cat", 8),
    ("loner_cat", 7),
    ("clan_warrior", 6),
    ("dog_guard", 5),
    ("kittypet", 5),
    ("dog_hunting", 4),
    ("cougar", 1),
    ("black_bear", 1),
)

# Extra ambush weights merged in pick_wild_encounter_template by great pack.
REPTILE_ENCOUNTER_BY_PACK: dict[str, tuple[tuple[str, int], ...]] = {
    "mistmoor": (
        ("water_snake", 14),
        ("garter_snake", 8),
        ("spider", 6),
    ),
    "silverrush": (
        ("water_snake", 12),
        ("garter_snake", 10),
        ("spider", 5),
    ),
    "thistlehide": (
        ("garter_snake", 10),
        ("skink", 12),
        ("spider", 5),
    ),
}
DEFAULT_REPTILE_ENCOUNTER_WEIGHTS: tuple[tuple[str, int], ...] = (
    ("garter_snake", 4),
    ("spider", 3),
)

ACTIVITY_ENCOUNTER_CHANCE: dict[str, int] = {
    "hunt": HUNT_WILD_ENCOUNTER_CHANCE,
    "explore": EXPLORE_WILD_ENCOUNTER_CHANCE,
    "collab_patrol": COLLAB_PATROL_AMBUSH_CHANCE,
}

WILD_ENCOUNTER_FLAVOR: dict[str, tuple[str, ...]] = {
    "coyote": (
        "a **coyote** slinks from the brush; lean, grinning, already sizing your flank.",
        "Yipping cuts off as a **coyote** steps into the open, hackles up.",
    ),
    "fox": (
        "Russet movement; a **fox** doubles back when it realizes you're not prey.",
        "A **fox** freezes on a fallen log, then bares needle teeth when you close in.",
    ),
    "badger": (
        "Low growling from a burrow mouth; a **badger** won't yield its ground.",
        "Striped face and iron claws: a **badger** means to make you regret the trail.",
    ),
    "wolverine": (
        "Something foul on the wind. A **wolverine**; too bold, too angry to flee.",
        "A **wolverine** barrels from the rocks, fearless and furious.",
    ),
    "cougar": (
        "No birdsong. A **cougar** drops from the ridge without a sound.",
        "Pale eyes in the dusk; **mountain lion** scent, and nowhere clean to run.",
    ),
    "black_bear": (
        "Branches snap. A **black bear** stands on hind legs, blocking the path.",
        "Berry-sweet breath and bulk; a **black bear** won't move aside.",
    ),
    "dog_feral": (
        "Feral **hearth-hound** scent; a loose Twoleg hound turned wild, ribs sharp under matted fur.",
        "A **feral hearth-hound** circles, lips peeled, looking for the weak angle.",
    ),
    "dog_guard": (
        "Chain-rust and kennel musk; a **guard hearth-hound** broke its line and found you first.",
        "A heavy **guard hearth-hound** charges from the Twoleg fence-line.",
    ),
    "dog_hunting": (
        "Horn and hound; a **hunting hearth-hound** lost the deer and found wolf instead.",
        "Baying cuts short as a **hunting hearth-hound** locks onto your scent.",
    ),
    "clan_warrior": (
        "Cat-scent on the wind. A **clan warrior** drops from the branches, tail stiff.",
        "A forest **patrol cat** blocks the trail; territory, not curiosity.",
    ),
    "rogue_cat": (
        "A **rogue cat** slinks from the bracken; no clan scent, only hunger.",
        "Torn ears and spite: a **rogue** means to steal your kill or your life.",
    ),
    "loner_cat": (
        "A **loner** freezes on the ridge; neither clan nor kittypet.",
        "Solitary cat-scent. A **loner** watches from the holly.",
    ),
    "kittypet": (
        "Collar-bells and milk-scent; a lost **kittypet** yowls when it sees you.",
        "A plump **kittypet** wandered too far from the Twoleg nests.",
    ),
    "water_snake": (
        "Reed-rustle; a **water snake** uncoils from the mud and strikes without warning.",
        "Warm bank, cold eyes; a **water snake** blocks the shallows.",
    ),
    "garter_snake": (
        "A **garter snake** suns on the trail and won't yield until you pass too close.",
        "Striped scales in the grass; a **garter snake** rears, hissing.",
    ),
    "skink": (
        "A **skink** bolts from sun-warmed stone, then turns to snap when cornered.",
        "Dry gulch flicker; a **skink** darts between your paws.",
    ),
    "spider": (
        "Leaf-litter shifts; a **wolf spider** the size of your paw rushes your muzzle.",
        "Too many legs at once; a **spider** drops from a web-strand onto your shoulder.",
    ),
}


def pick_wild_encounter_template(user=None) -> str:
    table = list(WILD_ENCOUNTER_WEIGHTS)
    gp = None
    if user is not None:
        if hasattr(user, "keys") and "great_pack" in user.keys():
            gp = user["great_pack"]
        elif isinstance(user, dict):
            gp = user.get("great_pack")
    extras = REPTILE_ENCOUNTER_BY_PACK.get(gp or "", DEFAULT_REPTILE_ENCOUNTER_WEIGHTS)
    table.extend(extras)
    keys, weights = zip(*table)
    return random.choices(keys, weights=weights, k=1)[0]


def wild_encounter_flavor(template_key: str) -> str:
    lines = WILD_ENCOUNTER_FLAVOR.get(template_key, WILD_ENCOUNTER_FLAVOR["coyote"])
    return random.choice(lines)


def wild_encounter_cooldown_minutes(user) -> int:
    last_at = user["last_wild_encounter_at"] if "last_wild_encounter_at" in user.keys() else ""
    return cooldown_minutes_remaining(last_at or None, WILD_ENCOUNTER_COOLDOWN_MINUTES)


def can_trigger_wild_encounter(user, channel_id: int) -> bool:
    return wild_encounter_cooldown_minutes(user) == 0


def recently_froze(user) -> bool:
    """True if `/sign signal:freeze` is still within its danger-avoidance window."""
    last_at = user["last_freeze_at"] if "last_freeze_at" in user.keys() else ""
    return cooldown_minutes_remaining(last_at or None, SIGN_FREEZE_AMBUSH_WINDOW_MINUTES) > 0


def roll_activity_ambush(activity: str, user=None) -> bool:
    chance = ACTIVITY_ENCOUNTER_CHANCE.get(activity, 0)
    if chance <= 0:
        return False
    if user is not None and recently_froze(user):
        chance *= SIGN_FREEZE_AMBUSH_MULTIPLIER
    return random.uniform(0, 100) <= chance


def maybe_start_activity_ambush(
    user,
    *,
    guild_id: int,
    channel_id: int,
    activity: str,
) -> tuple[int, str, str] | None:
    """Roll an ambush while hunting or exploring. Returns None if no fight."""
    if not can_trigger_wild_encounter(user, channel_id):
        return None
    if not roll_activity_ambush(activity, user):
        return None
    return start_wild_encounter(
        user, guild_id=guild_id, channel_id=channel_id, activity=activity
    )


def start_verge_dog_ambush(
    user,
    *,
    guild_id: int,
    channel_id: int,
    activity: str = "verge",
) -> tuple[int, str, str] | None:
    """Force a guard hearth-hound ambush when compound dogs charge."""
    if not channel_id or not can_trigger_wild_encounter(user, channel_id):
        return None
    return start_wild_encounter(
        user,
        guild_id=guild_id,
        channel_id=channel_id,
        activity=activity,
        template_key="dog_guard",
    )


def verge_dog_bite_fallback(user, *, day: int) -> str:
    """Bite damage when ambush cannot start (cooldown or no channel)."""
    from engine.disease_contract import try_contract_disease

    dmg = random.randint(2, 8)
    new_hp = max(0, int(user["hp"]) - dmg)
    db.set_user_conditions(user["discord_id"], wolf_id=user["id"], hp=new_hp)
    lines = [f"teeth rake your haunches; **−{dmg} hp**."]
    distemper = try_contract_disease(user, "distemper", chance=0.12)
    if distemper:
        lines.append(f"canid bite: {distemper}")
    return "\n".join(lines)


def start_wild_encounter(
    user,
    *,
    guild_id: int,
    channel_id: int,
    activity: str = "",
    template_key: str | None = None,
) -> tuple[int, str, str]:
    """Begin an active ambush vs a random wilderness threat."""
    template_key = template_key or pick_wild_encounter_template(user)
    template = BESTIARY_NPCS[template_key]
    threat_hp = npc_hp(template)

    enc_id = db.setup_npc_ambush_encounter(
        guild_id,
        channel_id,
        user["discord_id"],
        user["id"],
        hunter_hp=user["hp"],
        hunter_max_hp=user["max_hp"],
        npc_template=template_key,
        npc_hp=threat_hp,
        npc_base_name=template["name"],
        ambush_activity=activity,
    )
    db.update_user(
        user["discord_id"],
        last_wild_encounter_at=db.utcnow(),
        wolf_id=user["id"],
    )
    return enc_id, template_key, wild_encounter_flavor(template_key)


def ambush_embed(template_key: str, flavor: str, user=None, *, activity: str = ""):
    """Build the ambush announcement embed."""
    from utils.embeds import ERROR_COLOR, howlbert_embed

    from engine.bestiary import format_npc_category, format_npc_summary
    from engine.reptile_fear import reptile_ambush_fear_note

    template = BESTIARY_NPCS[template_key]
    fear = reptile_ambush_fear_note(user, template_key) if user else ""
    body = f"{flavor}{fear}\n\n{format_npc_summary(template_key)}"
    embed = howlbert_embed(f"ambush; {template['name']}", body, color=ERROR_COLOR)
    footer = f"{format_npc_category(template_key)} · combat started; use the panel below"
    if activity:
        activity_labels = {
            "hunt": "rolled on hunt",
            "explore": "rolled on explore",
            "collab_patrol": "rolled on patrol",
            "verge": "verge dogs",
        }
        label = activity_labels.get(activity, activity.replace("_", " "))
        footer += f" · {label}"
    embed.set_footer(text=footer)
    return embed
