import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
_db_override = os.getenv("HOWLBERT_DB_PATH", "").strip()
DB_PATH = Path(_db_override) if _db_override else BASE_DIR / "fable.db"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
STATUS_CHANNEL_ID = os.getenv("STATUS_CHANNEL_ID")
BOT_DISPLAY_NAME = os.getenv("BOT_DISPLAY_NAME", "Howlbert")

# Auto rollover; one sunrise per IRL day at this clock time (server TZ)
AUTO_ROLLOVER_ENABLED = os.getenv("AUTO_ROLLOVER_ENABLED", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)
ROLLOVER_TIMEZONE = os.getenv("ROLLOVER_TIMEZONE", "America/New_York").strip() or "America/New_York"
ROLLOVER_HOUR = max(0, min(23, int(os.getenv("ROLLOVER_HOUR", "0") or 0)))
ROLLOVER_MINUTE = max(0, min(59, int(os.getenv("ROLLOVER_MINUTE", "0") or 0)))
AUTO_ROLLOVER_ANNOUNCE_CHANNEL_ID = os.getenv("AUTO_ROLLOVER_ANNOUNCE_CHANNEL_ID", "").strip()
_auto_ch = AUTO_ROLLOVER_ANNOUNCE_CHANNEL_ID
AUTO_ROLLOVER_ANNOUNCE_CHANNEL_ID = int(_auto_ch) if _auto_ch.isdigit() else None
# Wolves age +1 moon only when the real sky matches their birth phase (new/half/full)
LUNAR_BIRTH_AGING = os.getenv("LUNAR_BIRTH_AGING", "true").strip().lower() not in (
    "0",
    "false",
    "no",
)

# Tupperbox-style `/proxy` message listening. Requires BOTH this flag AND the
# "Message Content Intent" toggle in the Discord Developer Portal (Bot tab).
ENABLE_MESSAGE_CONTENT_INTENT = os.getenv(
    "ENABLE_MESSAGE_CONTENT_INTENT", "false"
).strip().lower() in ("1", "true", "yes", "on")

_avatar_cache_ch = os.getenv("AVATAR_CACHE_CHANNEL_ID", "").strip()
AVATAR_CACHE_CHANNEL_ID = int(_avatar_cache_ch) if _avatar_cache_ch.isdigit() else None

_rp_ambience_raw = os.getenv("RP_AMBIENCE_CHANNEL_IDS", "").strip()
RP_AMBIENCE_CHANNEL_IDS: list[int] = []
for _part in _rp_ambience_raw.replace(";", ",").split(","):
    _part = _part.strip()
    if _part.isdigit():
        RP_AMBIENCE_CHANNEL_IDS.append(int(_part))

# Slash replies: when true, bot posts to the channel (profiles, hunts, errors, everything)
PUBLIC_GAMEPLAY_MESSAGES = os.getenv("PUBLIC_GAMEPLAY_MESSAGES", "true").strip().lower() in (
    "1",
    "true",
    "yes",
)

# Currency; bones only
CURRENCY_EMOJI = "🦴"
CURRENCY_NAME = "Bones"
CURRENCY_LABEL = f"{CURRENCY_EMOJI} {CURRENCY_NAME}"

# Economy; sunrise stipend paid from pack treasury (see claim_daily_stipend)
DAILY_REWARD = 25
MAX_PACK_TAX_RATE = 25
MAX_WOLVES_PER_PLAYER = 10

# Hunt outcomes: (min_bones, max_bones, weight)
HUNT_OUTCOMES = [
    (0, 0, 15),
    (5, 15, 35),
    (16, 35, 35),
    (36, 60, 12),
    (61, 100, 3),
]

# Chance (percent) that `/bones action:hunt` triggers a cornered deer/elk fight instead of a normal roll
LARGE_PREY_ENCOUNTER_CHANCE = 15
LARGE_PREY_BONES = (30, 55)
# A lone wolf rarely commits to elk/moose-sized prey; only a cornered, sick, or
# desperate large animal is takeable solo. Solo hunts meet large prey at this
# fraction of the base chance (pack hunts keep the full rate).
SOLO_LARGE_PREY_ENCOUNTER_PCT = 40

# World / rollover; one rollover = one in-game day
SEASONS = ("spring", "summer", "autumn", "winter")
SEASON_LENGTH_DAYS = 6
TIMES_OF_DAY = ("dawn", "day", "dusk", "night")

# Wolf age (in-world moons; one rollover = one sunrise)
PUP_MAX_MOONS = 6           # under 6 moons = pup life stage
JUVENILE_MAX_MOONS = 24     # 6-24 moons = juvenile life stage
ELDER_MIN_MOONS = 60        # 60+ moons = elder life stage (24-59 = adult)
MOONS_PER_ROLLOVER = 1      # moons gained when a wolf ages on rollover

WEATHER_TYPES = (
    "clear",
    "cloudy",
    "sunny",
    "rain",
    "fog",
    "wind",
    "sleet",
    "snow",
    "hail",
    "storm",
    "heatwave",
    "thunderstorm",
)

# Hunt success modifier by weather (percent points, e.g. -20 = -20%)
WEATHER_HUNT_MODIFIERS = {
    "clear": 0,
    "cloudy": 0,
    "sunny": 5,
    "rain": -10,
    "fog": -15,
    "wind": -10,
    "sleet": -15,
    "snow": -20,
    "hail": -25,
    "storm": -30,
    "heatwave": -15,
    "thunderstorm": -25,
}

# Season hunt payout modifier (percent points on bones after weather; stacks with weather)
SEASON_HUNT_MODIFIERS = {
    "spring": 5,
    "summer": 10,
    "autumn": -5,
    "winter": -20,
}

# Added to forage Survival DC by season (higher = harder to find herbs)
SEASON_FORAGE_DC_MOD = {
    "spring": -2,
    "summer": 0,
    "autumn": 2,
    "winter": 5,
}

DEFAULT_SHOP_ITEMS = (
    (
        "herb_bundle",
        "Herb Bundle",
        "Use `/bones action:use item:herb_bundle`; random common herbs (2 to 4) added to `/bones action:inventory`.",
        40,
        12,
    ),
    (
        "prey_bundle",
        "Prey Bundle",
        "Use `/bones action:use item:prey_bundle`; random carcasses (2 to 3) added to `/food`.",
        55,
        18,
    ),
    (
        "vitality_salve",
        "Vitality Salve",
        "Neonatal care; buy from `/bones action:shop`, then `/pupcare action:save name:<pup>` on the **same sunrise** "
        "a lethal-at-birth pup is born to keep them alive.",
        550,
        150,
    ),
    (
        "lucky_tooth",
        "Lucky Tooth",
        "Passive: +15% bones on `/bones action:hunt` while carried.",
        75,
        20,
    ),
    (
        "raven_companion",
        "Raven Companion",
        "Passive: +20% bones on `/field action:scavenge` and +10% on `/field action:track` while carried.",
        300,
        85,
    ),
    (
        "den_charm",
        "Den Charm",
        "Use `/bones action:use item:den_charm`; +1 pack unity once per rollover (must be in a pack).",
        100,
        30,
    ),
    (
        "rabbit_pelt",
        "Rabbit Pelt",
        "Use `/bones action:use item:rabbit_pelt recipient:@wolf`; trade for +2 standing; they gain 10 bones.",
        55,
        15,
    ),
    (
        "extra_paw",
        "An Extra Paw",
        "Add RP to `/bones action:work` or `/bones action:crime`: your own `scene:` text, or `staff:true` for admin-written flavor (uses one).",
        150,
        40,
    ),
    (
        "safe_roll",
        "Safe Roll",
        "🎲 `/rpg action:roll use_safe_roll:true`; reroll a failed d20 once. **Cannot** be used in combat.",
        100,
        30,
    ),
    (
        "revive",
        "Revive",
        "Use `/bones action:use item:revive` when your active wolf is **dead**; same name & stats, back at 1 HP. "
        "Old-age deaths reset to 60 moons. **Ko-fi shop only**.",
        0,
        0,
    ),
    (
        "reincarnation",
        "Reincarnation",
        "Use `/bones action:use item:reincarnation new_name:<name>` when **dead**; new name & juvenile age (12 moons), "
        "but keep attributes, skills, standing & bones. Clears prey/toys. **Ko-fi shop only**.",
        0,
        0,
    ),
)

# Removed from the trading post; kept at price 0 so old inventory keys still resolve
RETIRED_SHOP_ITEM_KEYS = ("coffin",)

# Trading post; prey carcasses & amusement toys (buy with bones → hoard)
SHOP_PREY_PRICES: dict[str, tuple[int, int]] = {
    "vole": (18, 4),
    "hare": (38, 10),
    "rabbit": (32, 8),
    "fish": (30, 8),
    "grouse": (48, 14),
}
SHOP_TOY_PRICES: dict[str, tuple[int, int]] = {
    "bone": (10, 2),
    "feather": (14, 3),
    "acorn": (8, 1),
    "shell": (12, 2),
    "talon": (20, 5),
    "stick": (10, 2),
}
MAX_WOLF_AGE_MOONS = 120  # peaceful death from old age on rollover at this age
REVIVE_OLD_AGE_RESET = 60  # moons after reviving from old-age death
REVIVE_MOOD_FLOOR = 40
REINCARNATION_START_AGE_MOONS = 12
REINCARNATION_MOOD = 50

# Energy; wolvden-style activity stamina. Every repeatable field/social/den
# action spends energy instead of being hard-capped or paying out on a
# diminishing curve. Energy never blocks an action outright: acting at 0
# energy still works, it just costs extra exhaustion and mood instead.
# Refills with a passive drip each sunrise (inactivity) and a bigger chunk
# from a long rest (manual `/vitals action:rest` or automatic sunrise sleep).
ENERGY_MIN = 0
ENERGY_MAX = 100
ENERGY_DEFAULT = 100
ENERGY_SUNRISE_REGEN = 25
ENERGY_LONG_REST_GAIN = 35
ENERGY_SHORT_REST_GAIN = 15
ENERGY_EMPTY_EXHAUSTION_GAIN = 1
ENERGY_EMPTY_MOOD_LOSS = 4
# Real-time daytime drip; energy trickles back while a wolf is idle (not acting)
# during the day, on top of the sunrise sleep. Coupled to hunger: a starving
# wolf has no calories to spare, so regen (drip and sunrise) scales with hunger
# down to a floor. hunger at/above ENERGY_HUNGER_FULL restores at full rate.
ENERGY_REALTIME_REGEN_PER_HOUR = 6
ENERGY_HUNGER_FULL = 80
ENERGY_HUNGER_FLOOR = 0.2

# Per-activity energy costs. Role-privileged specialists (full forager,
# scout, medic, ...) pay a discounted cost on their signature actions
# instead of being unlimited outright; everyone else pays the base cost.
ENERGY_COST_LOW = 8
ENERGY_COST_MED = 12
ENERGY_COST_HIGH = 18
ENERGY_COST_DISCOUNTED = 4

# Mood; Wolvden-style pack morale (amusement & socialize restore it)
MOOD_MIN = 0
MOOD_MAX = 100
MOOD_ROLLOVER_DECAY = 3
MOOD_LOW_THRESHOLD = 30
MOOD_CRITICAL_THRESHOLD = 15
MOOD_HUNT_PENALTY_PCT = 25
COURT_SUCCESS_MOOD_GAIN = 6
COURT_FAIL_MOOD_LOSS = 4
COURT_HOSTILE_FAIL_MOOD_LOSS = 7
MATE_MOOD_GAIN = 12
# Inbreeding is not blocked (as in wolvden), but it is taboo. Any completed kin
# mating (engine.mating.execute_mating) turns the den on the elder and scars the
# younger; no hard block, only real penalties.
KIN_MATING_STANDING_LOSS = 8        # older wolf; the den blames the elder for the pairing
KIN_MATING_YOUNGER_MOOD_LOSS = 15   # younger wolf; shame and distress
KIN_MATING_FEAR_DAYS = 7            # younger wolf; fear of mating (court/mate at disadvantage) for this many sunrises
HUNGER_MIN = 0
HUNGER_MAX = 100
HUNGER_DEFAULT = 80
HUNGER_ROLLOVER_DECAY = 12
HUNGER_LOW_THRESHOLD = 30
HUNGER_CRITICAL_THRESHOLD = 15
HUNGER_HUNT_PENALTY_PCT = 20
HUNGER_SICK_EXTRA_DECAY = 6

# Intra-day (lazy, real-time) hunger and thirst decay, applied when a wolf
# checks vitals / eats / drinks. Points per real hour. Keeps depletion feeling
# continuous instead of only ticking at the sunrise rollover. A safety cap
# limits how much intra-day decay can accrue between two rollovers.
HUNGER_HOURLY_DECAY = 0.4
THIRST_HOURLY_DECAY = 0.5
VITALS_INTRADAY_DECAY_CAP = 40

# Carnivore nutrition: wolves survive short-term on forage and liquids, but a
# meat-free stretch this many sunrises long risks wasting sickness (malnutrition).
MEATLESS_WASTING_DAYS = 8
MEATLESS_WASTING_CHANCE = 0.25

# Sunrise auto-feeding: each pack first feeds its members from the food reserve
# (lore order: elders, pups, den-keepers, sick first). Wolves left with no
# reserve then forage/scavenge for themselves. Wolves are opportunistic omnivores
# (facultative carnivores): they scrape by on berries, roots, and fallen fruit in
# growing seasons, or scavenged scraps and carrion in lean ones. The roll usually
# succeeds but CAN fail; pups, the injured, elders, and winter all make
# starvation a real risk, so neglect and bad seasons still bite.
ROLLOVER_SCAVENGE_BASE_CHANCE = 0.70
ROLLOVER_SCAVENGE_HUNGER = 14  # small; enough to get by, not to thrive
ROLLOVER_SCAVENGE_THIRST = 6

# Solo hunters (loners / rogues) miss pack coordination. Applied after
# sniff/dex bonuses so individual traits can still compensate somewhat.
LONER_HUNT_PENALTY_PCT = 20  # % reduction on hunt yield when no pack_id

# Pups in winter gain exhaustion from cold exposure each sunrise even when fed.
PUP_WINTER_COLD_EXHAUSTION_CHANCE = 0.15  # 15% per sunrise in winter

# Nursing; mothers feed milk until pups reach juvenile stage (PUP_MAX_MOONS)
MILK_HUNGER_GAIN = 28
MILK_THIRST_GAIN = 12
MOTHER_NURSE_HUNGER_COST_PER_PUP = 6
CARETAKER_MASH_HUNGER_GAIN = 18
CARETAKER_MASH_THIRST_GAIN = 6
PUP_UNFED_EXTRA_DECAY = 6
HONEY_PUP_HUNGER_BONUS = 10
HONEY_PUP_EXHAUSTION_RELIEF = 1

# Thirst; slips faster than hunger; /drink and prey moisture restore it
THIRST_MIN = 0
THIRST_MAX = 100
THIRST_DEFAULT = 80
THIRST_ROLLOVER_DECAY = 14
THIRST_LOW_THRESHOLD = 30
THIRST_CRITICAL_THRESHOLD = 15
THIRST_HUNT_PENALTY_PCT = 15
THIRST_SICK_EXTRA_DECAY = 8
DRINK_COOLDOWN_MINUTES = 60
DRINK_THIRST_RESTORE = 22
DRINK_HUNGER_RESTORE = 2
DRINK_MOOD_RESTORE = 2
DRINK_HP_RESTORE = 2
DRINK_EXHAUSTION_RELIEF = 2  # eat only relieves 1; cool water off a hot run does more
HUNT_WILD_ENCOUNTER_CHANCE = 8
EXPLORE_WILD_ENCOUNTER_CHANCE = 10
WILD_ENCOUNTER_COOLDOWN_MINUTES = 90
# `/sign signal:freeze`; a recent silent danger-crouch makes the next ambush
# roll less likely to find you (real-time window, not a sunrise gate).
SIGN_FREEZE_AMBUSH_WINDOW_MINUTES = 20
SIGN_FREEZE_AMBUSH_MULTIPLIER = 0.4
HUNTER_HUNTS_PER_SUNRISE = 10
# Repeated field work: 2nd+ same activity tires wolves; untrained skills tire faster.
ACTIVITY_FATIGUE_CROSS_TOTAL_THRESHOLD = 4

# Auto-dormant: wolves inactive this many days are treated as "away" and skip
# vitals decay, needs-collapse, and exhaustion death on rollover. Set to 1 so a
# wolf nobody plays for a sunrise stops decaying (and can't slowly die).
AUTO_DORMANT_INACTIVE_DAYS = 1
# Low mood streak: consecutive sunrises below threshold give a hunt penalty.
LOW_MOOD_STREAK_THRESHOLD = 30
LOW_MOOD_STREAK_HUNT_PENALTY_PCT = 10
# Hunt thirst drain: chasing prey in summer/heatwave costs thirst.
HUNT_SUMMER_THIRST_COST = 1
HUNT_SUMMER_THIRST_WEATHER = frozenset({"heatwave"})
# Pack size instability: packs below threshold drain unity each rollover.
SMALL_PACK_ACTIVE_THRESHOLD = 3
SMALL_PACK_UNITY_DRAIN = 1
# Scent marks older than this many days are pruned from the DB on rollover.
SCENT_MARK_PRUNE_DAYS = 10
# Deep grief after bonded mate dies; sunrises before re-mate eligibility.
MATE_GRIEF_SUNRISES = 7
MATE_GRIEF_HUNT_PENALTY_PCT = 15
# Weather-scaled rollover thirst decay.
THIRST_ROLLOVER_HEATWAVE_EXTRA = 4
THIRST_ROLLOVER_SNOW_REDUCTION = 4
THIRST_ROLLOVER_SNOW_WEATHER = frozenset({"snow", "sleet", "hail", "storm", "thunderstorm"})
THIRST_ROLLOVER_HEATWAVE_WEATHER = frozenset({"heatwave"})
# Hunger passive mood drain; chronic hunger compounds distress.
HUNGER_LOW_THRESHOLD_MOOD_DRAIN = 30
HUNGER_PASSIVE_MOOD_DRAIN = 2
# Age-based physical stat drift: strength erodes, wisdom grows.
ELDER_STAT_DRIFT_START_MOONS = 84
ELDER_STAT_DRIFT_INTERVAL_MOONS = 12
# Howl exposure: hostile packs heard the call; sniff border odds increase.
HOWL_EXPOSED_BORDER_BONUS = 0.15

# Pack collaborative hunt (/bones action:hunt collaborate:true)
COLLAB_HUNT_MIN_WOLVES = 2
COLLAB_HUNT_MAX_WOLVES = 4
COLLAB_HUNT_BONUS_PCT_PER_WOLF = 12  # percent on total roll per wolf after the first
COLLAB_HUNT_ALL_HUNTERS_BONUS = 8  # extra if every participant is Hunter rank
COLLAB_HUNT_MOOD_BONUS = 2

# Pack collaborative patrol (/scout survey collaborate:true)
COLLAB_PATROL_MIN_WOLVES = 2
COLLAB_PATROL_MAX_WOLVES = 4
COLLAB_PATROL_BONUS_PCT_PER_SCOUT = 10
COLLAB_PATROL_ALL_SCOUTS_BONUS = 8
COLLAB_PATROL_MOOD_BONUS = 2
COLLAB_PATROL_AMBUSH_CHANCE = 8
CANNIBALISM_CAUGHT_CHANCE = 40
CANNIBALISM_STANDING_PENALTY = 3
CANNIBALISM_MOOD_PENALTY = 5
CANNIBALISM_EAT_MOOD_PENALTY = 2

# Fresh foraged herbs must be dried within this many sunrises or they rot
HERB_FRESH_DRY_DAYS = 1
HERB_DRIED_STORAGE_DAYS = 180
# Poultice and tea spoil after this many sunrises (Basil: 4-5)
HERB_PREPARED_STORAGE_DAYS = 5
# All valid preparation forms that can be applied to herbs.
# These match the keys used in each herb's `preparations` dict.
HERB_PREPARED_FORMS = (
    "poultice",
    "juice",
    "tea",
    "ointment",
    "sap",
    "rub",
    "cooked",
    "simmered_milk",
    "dried",   # dried is also a preparation (storage)
)
# Failed winter forage may spoil a random herb stack in the bag
WINTER_FORAGE_SPOIL_CHANCE = 0.35

# --- Grow-your-own herb garden ---
GARDEN_MAX_PLOTS = 6            # living plantings per pack garden at once
LONG_REST_MOOD_GAIN = 6
LONG_REST_HP_GAIN = 3
LONG_REST_EXHAUSTION_RELIEF = 3
SHORT_REST_EXHAUSTION_RELIEF = 1  # quick breather; always relieves some, comfrey adds hp on top
GARDEN_SEED_BONE_COST = 12     # buy a seed packet from the den
GARDEN_FORAGE_SEED_CHANCE = 0.40  # chance foraging also yields a seed
GARDEN_HARVEST_SEED_MIN = 1    # seeds returned when harvesting a healthy plant
GARDEN_HARVEST_SEED_MAX = 2
GARDEN_TEND_HEALTH_RESTORE = 15   # health regained per tending
# Bone splint rest after successful set_bone surgery (sunrises)
BONE_REST_DAYS = 7
# Difficulty classes for each preparation method.
# Used when a player attempts to prepare an herb from inventory.
HERB_PREP_DC = {
    "poultice": 10,
    "poultice_simple": 0,       # for medics with proper tools
    "dry": 8,
    "dry_storage": 10,
    "chew_poultice": 8,
    "preserve_rare": 15,
    "antidote": 18,
    "sedative": 8,
    "incomplete_antidote": 20,
    # new methods
    "juice": 10,
    "tea": 10,
    "ointment": 12,
    "sap": 10,
    "rub": 8,
    "cooked": 12,
    "simmered_milk": 14,
}
VERGE_ROADSIDE_DC = 10
VERGE_COMPOUND_DC = 13
VERGE_FAIL_MOOD = 3
VERGE_CRIT_FAIL_MOOD = 6
VERGE_MONSTER_NEAR_MISS_CHANCE = 35
VERGE_COMPOUND_DOG_CHANCE = 40
VERGE_TOXIC_MISID_CHANCE = 12
NEEDS_SURVIVAL_RESTORE = 8  # hunger/thirst restored on stabilize after vitals crisis
NEEDS_EXHAUSTION_GAIN = 1  # +1 exhaustion per sunrise per depleted vital (hunger/thirst below low threshold)
PACK_STASH_ROT_BONUS_DAYS = 3
RESCOUT_MOOD_GAIN = 4
SCOUT_RESCOUTS_PER_DAY = 2
SCOUT_EXPLORE_DC_BONUS = 1
SCOUT_SURVEY_BONES = (6, 16)
SCOUT_TRAIL_BONES = (8, 22)
PLAYALL_MOOD_GAIN = 6
SOCIALIZE_MOOD_WARM = 10
SOCIALIZE_MOOD_GOOD = 8
SOCIALIZE_MOOD_AWKWARD = -4
SOCIALIZE_MOOD_SCRAP = -7
SOCIALIZE_UNITY_WARM = 1
SOCIALIZE_UNITY_GOOD = 1
SOCIALIZE_UNITY_AWKWARD = -1
SOCIALIZE_UNITY_SCRAP = -2
SOCIALIZE_STANDING_GOOD = 1
SOCIALIZE_STANDING_SCRAP = -1
# Cross-pack socialize/groom/sign always works, but on hostile ground there's
# a real chance it breaks into a border skirmish instead of going through.
CROSS_PACK_SOCIAL_COMBAT_CHANCE = 0.35

# Body / visual language (`/sign`); how wolves "speak" without howling.
# Rally is the mute wolf's stand-in for a howl, so it pays out more for the silenced.
SIGN_RALLY_UNITY_MUTE = 3
SIGN_RALLY_UNITY_NORMAL = 1
SIGN_RALLY_STANDING = 1
SIGN_ALERT_UNITY = 1
SIGN_ALERT_STANDING = 1
SIGN_PLAY_MOOD = 6
SIGN_PLAY_UNITY = 1
SIGN_SUBMIT_MOOD_SELF = 3
SIGN_SUBMIT_MOOD_TARGET = 4
SIGN_SUBMIT_UNITY = 1
SIGN_SOOTHE_MOOD_TARGET = 10
SIGN_SOOTHE_MOOD_SELF = 3
SIGN_SOOTHE_UNITY = 1
SIGN_THREATEN_STANDING = 1
SIGN_THREATEN_TARGET_MOOD = -5
SIGN_THREATEN_UNITY = -1
SIGN_THREATEN_BACKFIRE_CHANCE = 0.30
SIGN_THREATEN_BACKFIRE_MOOD = -5
SIGN_THREATEN_BACKFIRE_STANDING = -1
SIGN_FREEZE_STANDING = 1
SIGN_GREET_MOOD = 4
SIGN_GRIEVE_MOOD_SELF = 5
SIGN_GRIEVE_MOOD_TARGET = 8
SIGN_GRIEVE_UNITY = 1
SIGN_TRACK_MOOD = 4
SIGN_TRACK_UNITY = 1
SIGN_CHALLENGE_WIN_STANDING = 2
SIGN_CHALLENGE_LOSE_STANDING = -1
# Lightweight "emote" signals: lower stakes than alert/threaten/challenge,
# but still real mechanics (no flavor-only signs).
SIGN_NUZZLE_MOOD = 3
SIGN_NUZZLE_BOND_GAIN = 4
SIGN_STRETCH_EXHAUSTION_RELIEF = 1
# whimper: a plea for comfort; small own-mood lift, larger softening of the target.
SIGN_WHIMPER_MOOD_SELF = 2
SIGN_WHIMPER_MOOD_TARGET = 4
# growl: a low warning, lighter than threaten (no distress flag, no standing);
# knocks the target's mood, but can be called and backfire on you.
SIGN_GROWL_MOOD_TARGET = -3
SIGN_GROWL_BACKFIRE_CHANCE = 0.25
SIGN_GROWL_BACKFIRE_MOOD = -2
# lick: a grooming lick; mood for both and a small care bond.
SIGN_LICK_MOOD = 3
SIGN_LICK_BOND_GAIN = 3
# ASL-style /sign composition (base/motion/field) isn't flavor-only: matching
# the anatomically correct combo for the signal (engine.signing.CANONICAL_POSTURE)
# grants a real bonus on top of the signal's normal effect; bond strength
# with the target when one exists, standing when the signal is pack-wide.
# Getting 2 of 3 parts right grants half (rounded down, min 1); all 3 grants
# the full bonus.
SIGN_ASL_MATCH_BOND_GAIN = 4
SIGN_ASL_MATCH_STANDING_BONUS = 2
# Mentor bonus; medic apprentices already get this from `/medic action:observe`.
# `/role action:shadow` grants the same boost to hunter/scout/forager/diplomat/
# caretaker apprentices on their focus skill (engine.herb_buffs mentor_bonus_*).
MENTOR_BONUS_VALUE = 2
# Each /role action:shadow session also deepens a real mentor bond; once it
# crosses the threshold the apprentice gains one permanent rank in the
# mentor's focus skill; a one-time payoff for a mentorship that actually
# ran deep, not just a repeatable temp buff.
MENTOR_BOND_SKILL_TRANSFER_GAIN = 8
MENTOR_BOND_SKILL_TRANSFER_THRESHOLD = 70
# Bonds are living relationships, not a ratchet: friendship/rivalry/romance
# bonds untouched for this many sunrises lose a little strength each rollover
# until someone interacts again. Kin and mentor bonds don't decay.
BOND_DECAY_IDLE_DAYS = 14
BOND_DECAY_AMOUNT = 3
# Reunion bonus when bonded kin who haven't crossed paths in a long while
# (proxy: bond strength already decayed at least once) socialize again.
KIN_REUNION_MOOD_BONUS = 6
KIN_REUNION_BOND_GAIN = 10
# Mate fidelity: mating with someone who isn't your bonded mate, while that
# mate bond is still strong, costs real bond strength instead of being pure
# flavor.
FIDELITY_BOND_LOSS = 10
FIDELITY_BOND_MIN_TO_CARE = 40
BONE_GIFT_COST = 3
BONE_GIFT_MOOD_GAIN = 5
# Jealousy: a bonded mate isn't present for /playpen socialize, but a "warm"
# outcome with someone else still costs them something real.
JEALOUSY_MOOD_PENALTY = 4
JEALOUSY_RIVALRY_GAIN = 5
# Personal standing drifts back toward neutral (0) for a wolf who's gone
# quiet a long while, instead of returning exactly as feared/trusted as
# when they left. Checked against the most recent of several common
# activity timestamps as a proxy for "last seen."
STANDING_DECAY_IDLE_DAYS = 20
STANDING_DECAY_AMOUNT = 1
# A rivalry bond that's stayed strong for a long time without ever being
# resolved (death, reconciliation) calcifies into permanent den legend
# instead of just quietly decaying away from neglect like ordinary bonds.
RIVALRY_LEGEND_STRENGTH_THRESHOLD = 70
RIVALRY_LEGEND_AGE_DAYS = 60
# Small chance a newborn pup starts with a one-rank head start in whichever
# skill a parent has earned the most experience in, instead of every litter
# beginning completely blank regardless of what the parents are good at.
PUP_TRAIT_INHERIT_CHANCE = 0.20
# A few sunrises of reduced cold resistance right after any season change,
# coat mid-cycle; even winter_survivor doesn't fully insulate during it.
SHEDDING_WINDOW_DAYS = 4
# Lower-stakes rank disputes between ordinary pack members (not alpha/advisor
#; that's the Rite of the Broken Canine's domain). Winner climbs, loser
# drops, breaking ties in den feed priority; once per sunrise per challenger.
RANK_DISPUTE_SHIFT = 1
RANK_DISPUTE_MIN = -10
RANK_DISPUTE_MAX = 10
# A wolf back after a long absence doesn't slot back into the den instantly
#; a brief "stranger scent" beat on their first socialize back.
STRANGER_SCENT_ABSENCE_DAYS = 15
STRANGER_SCENT_MOOD_PENALTY = 3
# A temporary injury left untreated long past its normal heal time doesn't
# just sit there forever; it ages into a permanent long-term injury instead.
CHRONIC_CONVERSION_MULTIPLIER = 3
# As spring (the only season pups can realistically be born by, given the
# 63-day gestation) nears, a den with too few breeding-age mated pairs feels
# real anxiety about its future and loses a touch of unity.
COURTSHIP_PRESSURE_MIN_PAIRS = 2
COURTSHIP_PRESSURE_UNITY_PENALTY = 2
# The smallest pup in a large litter starts at a real disadvantage, but
# whoever feeds them first while they're struggling tends to grow close.
RUNT_LITTER_MIN_SIZE = 4
RUNT_ATTR_PENALTY = 1
RUNT_FIRST_FEED_BOND_BONUS = 10
# An apprentice can't be taught by a mentor who isn't around; if the mentor
# (not the apprentice) goes idle long enough, the mentorship itself stalls.
MENTOR_STALL_IDLE_DAYS = 10
MENTOR_STALL_DECAY_AMOUNT = 3
# Grief scaled to bond strength: losing a wolf you weren't formally mated to
# (best friend, kin, secret romance, mentor) should still hit hard if the
# bond was real. Only bonds at/above this strength trigger anything; the
# mood hit and grief-disease chance both scale up to STRONG_BOND_GRIEF_CAP.
STRONG_BOND_GRIEF_THRESHOLD = 50
STRONG_BOND_GRIEF_MOOD_CAP = 25
STRONG_BOND_GRIEF_CHANCE_CAP = 0.7
# Pup training; `/pupcare action:train`; a deliberate, capped stat nudge
# distinct from feed/save/adopt. Once per sunrise per pup; lifetime-capped
# so it can't replace genetics/traits as a power source.
PUP_TRAIN_SUCCESS_DC = 12
PUP_TRAIN_MAX_LIFETIME_BONUS = 5
PUP_TRAIN_MOOD_CONSOLATION = 2
# Diminishing returns on repeat /sign mood payouts between the same pair (no
# cooldown, but signing the same partner over and over pays out less so it
# can't substitute for `/playpen action:play`/`action:groom`, which stay
# once-per-sunrise). Resets once SIGN_DIMINISH_WINDOW_MINUTES passes quiet.
SIGN_DIMINISH_WINDOW_MINUTES = 30
SIGN_DIMINISH_FACTOR = 0.5
SIGN_DIMINISH_FLOOR = 0.2
# A mute/silenced wolf's sign is their only voice, not a supplement to
# talking; it decays toward a much gentler floor on repeats.
SIGN_MUTE_DIMINISH_FLOOR = 0.6
# Reading/answering a denmate's signal (the back-and-forth half of the system).
SIGN_READ_MOOD = 4
SIGN_READ_RALLY_UNITY = 1
SIGN_READ_STANDING = 1

# Invite & server boost rewards (booster perks are personal only; not pack treasury)
INVITE_WELCOME_BONES = 25
INVITE_REFERRER_BONES = 40
INVITE_REFERRER_STANDING = 2
INVITE_REGISTER_WINDOW_DAYS = 7
INVITE_REFERRAL_ROLLOVERS = 3
INVITE_MAX_PAYOUTS_PER_MONTH = 3

BOOST_FIRST_BONES = 60
BOOST_FIRST_STANDING = 3
BOOST_FIRST_MOOD = 10
BOOST_SECOND_BONES = 40
BOOST_DAILY_BONUS = 5

# Kickstarter backer rewards (Tier 2 fulfillment)
KICKSTARTER_BACKER_LABEL = "Kickstarter Backer"
KICKSTARTER_TIER2_BONES = 75
KICKSTARTER_TIER2_BONUS_ITEMS = ("lucky_tooth", "den_charm", "herb_bundle")

# Ko-fi donations & redeem codes (personal rewards only; not pack treasury)
KOFI_VERIFICATION_TOKEN = os.getenv("KOFI_VERIFICATION_TOKEN", "")
KOFI_WEBHOOK_PORT = int(os.getenv("KOFI_WEBHOOK_PORT", "8080") or "8080")
DONOR_BONES_PER_DOLLAR = 15
DONOR_MONTHLY_BONE_CAP = 300
DONOR_LEGEND_DAILY_BONUS = 3
DONOR_LEGEND_SUPPORTER_DAYS = 30
DONOR_TIERS: dict[str, dict] = {
    "friend": {"min_cents": 500, "label": "Den Friend"},  # Ko-fi minimum is $5
    "benefactor": {"min_cents": 1000, "label": "Pack Benefactor"},
    "legend": {"min_cents": 2500, "label": "Legend of the Den"},
}
# Ko-fi membership tier names (substring match, first win) → in-game tier key
KOFI_TIER_NAME_MATCHES: tuple[tuple[str, str], ...] = (
    ("legend", "legend"),
    ("benefactor", "benefactor"),
    ("friend", "friend"),
)
# Perks granted on each membership renewal (bones still come from payment amount)
KOFI_MEMBERSHIP_PERKS: dict[str, dict] = {
    "friend": {"supporter_days": 0, "first_mood": 5, "first_standing": 0},
    "benefactor": {"supporter_days": 0, "first_mood": 8, "first_standing": 1},
    "legend": {
        "supporter_days": 35,
        "first_mood": 10,
        "first_standing": 2,
    },
}
KOFI_MEMBERSHIP_PERIOD_DAYS = 32

# Ko-fi Shop; direct_link_code from each product URL: ko-fi.com/s/{code}
KOFI_SHOP_CATALOG: dict[str, dict] = {
    "bone_pouch": {
        "label": "Bone Pouch",
        "price_cents": 500,
        "delivery": "instant",
        "bones": 75,
        "match_names": ("bone pouch",),
        "direct_link_codes": ("f5d07feec4",),
    },
    "bone_cache": {
        "label": "Bone Cache",
        "price_cents": 1000,
        "delivery": "instant",
        "bones": 150,
        "match_names": ("bone cache",),
        "direct_link_codes": ("86a62f713a",),
    },
    "gift_bone_pouch": {
        "label": "Gift a Bone Pouch",
        "price_cents": 500,
        "delivery": "code",
        "bones": 75,
        "match_names": ("gift", "bone pouch"),
        "direct_link_codes": ("79c40a6fa6",),
    },
    "supporter_badge": {
        "label": "Supporter Badge (Digital)",
        "price_cents": 500,
        "delivery": "manual",
        "sla_days": 7,
        "match_names": ("supporter badge",),
        "direct_link_codes": ("4bd6954008",),
    },
    "wallpaper_pack": {
        "label": "Den Wallpaper Pack",
        "price_cents": 800,
        "delivery": "manual",
        "sla_days": 3,
        "match_names": ("wallpaper",),
        "direct_link_codes": ("c862f55df1",),
    },
    "den_landmark": {
        "label": "Den Landmark Name",
        "price_cents": 2000,
        "delivery": "manual",
        "sla_days": 14,
        "match_names": ("landmark", "den landmark"),
        "direct_link_codes": ("5cb52af6e0",),
    },
    "quest_hook": {
        "label": "Quest Hook Commission",
        "price_cents": 3000,
        "delivery": "manual",
        "sla_days": 14,
        "match_names": ("quest hook", "quest commission"),
        "direct_link_codes": ("f565f7daee",),
    },
    "first_hunt_story": {
        "label": "First Hunt Story Snippet",
        "price_cents": 1000,
        "delivery": "manual",
        "sla_days": 7,
        "match_names": ("first hunt", "story snippet"),
        "direct_link_codes": ("bba5807b42",),
    },
    "wolf_portrait": {
        "label": "Wolf Portrait (Digital Commission)",
        "price_cents": 4000,
        "delivery": "manual",
        "sla_days": 21,
        "match_names": ("portrait", "commission"),
        "direct_link_codes": ("1acef91903",),
    },
    "custom_item_name": {
        "label": "Custom Item Name (Cosmetic)",
        "price_cents": 3500,
        "delivery": "manual",
        "sla_days": 14,
        "match_names": ("custom item", "item name"),
        "direct_link_codes": ("7293d845b2",),
    },
    "legend_gift_card": {
        "label": "Legend Gift Card (1 Month)",
        "price_cents": 2500,
        "delivery": "code",
        "bones": 225,
        "donor_tier": "legend",
        "supporter_days": 35,
        "mood": 10,
        "standing": 2,
        "match_names": ("legend gift", "gift card"),
        "direct_link_codes": ("ff775b47c9",),
    },
    "revive": {
        "label": "Revive",
        "price_cents": 3500,
        "delivery": "instant",
        "grant_item": "revive",
        "match_names": ("revive", "second chance", "bring back"),
        "direct_link_codes": ("75109e65b8",),
    },
    "reincarnation": {
        "label": "Reincarnation",
        "price_cents": 2800,
        "delivery": "instant",
        "grant_item": "reincarnation",
        "match_names": ("reincarnation", "new life", "new body"),
        "direct_link_codes": ("931aa27911",),
    },
}

WORK_BONES = (10, 28)
WORK_TEXT = [
    "You haul river-stones for the den's border markers; hard labor, honest bones.",
    "A half-day mending trails through the pines earns a modest share.",
    "You stand watch at the ravine crossing while hunters are out.",
    "Elders pay you to strip old prey-piles and drag scraps to the bone pit.",
]
CRIME_BONES = (18, 50)
CRIME_CATCH_CHANCE = 0.35
CRIME_CAUGHT_STANDING = -3
CROSS_PACK_STEAL_BONES = (12, 40)
CROSS_PACK_STEAL_CATCH_CHANCE = 0.40
CROSS_PACK_STEAL_STANDING = 2
CROSS_PACK_STEAL_CAUGHT_STANDING = -4
INDIVIDUAL_STEAL_PCT = (0.10, 0.25)
INDIVIDUAL_STEAL_CATCH_CHANCE = 0.45
INDIVIDUAL_STEAL_CAUGHT_STANDING = -4
INDIVIDUAL_STEAL_STANDING = 1
INDIVIDUAL_STEAL_RIVALRY_GAIN = 8
RAID_ALERT_SUNRISES = 5
RAID_PACK_MODIFIERS = {
    "greyspire": {"catch_bonus": 0.05, "steal_mult": 0.85},
    "thistlehide": {"catch_bonus": 0.10, "steal_mult": 1.0},
    "mistmoor": {"catch_bonus": -0.05, "steal_mult": 1.0},
    "silverrush": {"catch_bonus": 0.0, "steal_mult": 1.10},
}
RAID_SNIFF_ENCOUNTER_BONUS = 0.12
RAID_SURVEY_DC_RAIDER = 2
RAID_SURVEY_DC_VICTIM = -2
RAID_SURVEY_VICTIM_BONE_BONUS = 5
RAID_AUDIT_RECOVER_PCT = 0.40
RAID_ACCUSE_RECOVER_PCT = 0.30
# Trial by combat: whoever loses pays, win or lose as the accuser; makes a
# false accusation as risky as the thing it's accusing someone of.
TRIAL_BY_COMBAT_LOSER_STANDING = -4
# Crowd-sourced denouncement: one wolf's say-so isn't a verdict; the den has
# to actually agree.
DENOUNCEMENT_SECONDS_REQUIRED = 3
DENOUNCEMENT_STANDING_PENALTY = -3
# Hostage diplomacy: sending a wolf to live with a treaty partner as a
# good-faith guarantee. A small trust bonus for offering one, and a much
# bigger relations penalty if the host pack's own treaty later breaks while
# someone else's wolf is standing in their den.
HOSTAGE_TREATY_STANDING_BONUS = 1
HOSTAGE_BETRAYAL_STANDING_PENALTY = -4
# Espionage: a planted spy reporting back risks discovery every time, not
# just once; real ongoing risk for real ongoing intel.
SPY_REPORT_DISCOVERY_DC = 14
SPY_CAUGHT_STANDING = -4
SPY_CAUGHT_RELATION_PENALTY = -3
# Active political matchmaking: an alpha/diplomat formally sanctioning an
# existing bonded pair across pack lines as a deliberate alliance act; a
# one-time upfront bump on top of the passive marriage-alliance forge bonus.
POLITICAL_MATCH_STANDING_BONUS = 2
DEN_RHYTHM_MIN_WOLVES = 2
DEN_RHYTHM_ACTIVITY_RATIO = 0.5
DEN_RHYTHM_UNITY_GAIN = 1
BOND_RELATION_PRESSURE_INTERVAL = 7
BOND_RELATION_PRESSURE_DELTA = -1
BOND_RELATION_FRIENDLY_FLOOR = 8
BOND_SCANDAL_STRAIN_DELTA = -3
ROLE_SHIFT_HUNTER_MOOD = 3
ROLE_SHIFT_MEDIC_STANDING = 1
ROLE_SHIFT_SCOUT_MOOD = 5
COLLAB_RP_MOOD_BONUS = 5
PARANOIA_RAID_UNITY_RISK = 0.25
PARANOIA_RAID_UNITY_PENALTY = -1
CROSS_PACK_MATE_CATCH_CHANCE = 0.40
CROSS_PACK_MATE_CAUGHT_STANDING = -4
CROSS_PACK_STABILIZE_SUCCESS_STANDING = 3
CROSS_PACK_STABILIZE_FAIL_STANDING = -4
STABILIZE_MEDIC_SUCCESS_STANDING = 1
STABILIZE_MEDIC_FAIL_STANDING = -2
STABILIZE_LAY_SUCCESS_STANDING = 3
STABILIZE_LAY_FAIL_STANDING = -4
CRIME_TEXT = [
    "You slip through rival scent-lines and lift bones from an unguarded cache.",
    "Under moonhigh you raid a loner's forgotten stash near the quarry.",
    "You bluff your way past a patrol and fence stolen herbs in the deep woods.",
    "A reckless smash-and-grab at a trader's drop-off; high risk, heavy payout.",
]
CROSS_PACK_STEAL_TEXT = [
    "You ghost past **{pack}** sentries and drag bones from their den cache.",
    "Moonless night; you nose open **{pack}**'s treasury pit and vanish before the howl.",
    "A rival patrol turns the wrong ridge; you strip **{pack}**'s communal stash bare.",
    "You leave **{pack}**'s scent-line reeking of theft and your packmates grin.",
]
CROSS_PACK_STEAL_CAUGHT_TEXT = [
    "**{pack}** border wolves run you down; the stash drops from your jaws.",
    "A **{pack}** scout saw everything. Your Alpha will hear of this shame.",
    "**{pack}**'s sentries were waiting. Teeth close on your haunches at the treeline.",
    "You misjudged **{pack}**'s watch rotation; caught red-pawed at their treasury.",
]
CRIME_CAUGHT_TEXT = [
    "A patrol catches your scent; you're run down before you reach the treeline.",
    "Guards were waiting. You drop the stash and flee with teeth at your heels.",
    "A rival wolf saw everything. The Alpha will hear of this.",
    "You misjudged the moon; caught red-pawed at the cache.",
]
CROSS_PACK_MATE_CAUGHT_TEXT = [
    "Border patrol catches you together; forbidden scent on forbidden ground.",
    "A scout from your own pack finds you with a rival. Word will spread.",
    "The den smells outsider on your fur. Elders will not overlook this.",
    "Howls of outrage from the ridge; you were seen mating across pack lines.",
]
MEDIC_MATE_CATCH_CHANCE = 0.45
MEDIC_MATE_CAUGHT_STANDING = -3
YIELD_CATCH_CHANCE = 0.35
YIELD_CAUGHT_STANDING = -2
YIELD_CAUGHT_TEXT = [
    "A rival snaps at your heels as you turn; the den will hear you broke first.",
    "You scramble away, but not before the fight sees you quit the line.",
    "Your opponent howls your shame across the clearing. Word reaches the Alpha.",
    "Teeth graze your flank on the way out; fleeing is still losing face.",
]
MEDIC_MATE_CAUGHT_TEXT = [
    "Your neutral scent betrays you; a patrol recognizes the Medic's forbidden heat.",
    "Someone reports celibacy broken. The den will not trust your hands on their wounds.",
    "A pup sees what they should not. Word spreads: the pack's healer mated.",
    "The Alpha's nose finds lust where only herbs should be. This is exile talk.",
]
MENTOR_MATE_CATCH_CHANCE = 0.45
MENTOR_MATE_CAUGHT_STANDING = -3
MENTOR_MATE_CAUGHT_TEXT = [
    "Word spreads fast: a mentor's hands shouldn't wander to the wolf they're shaping.",
    "An apprentice elsewhere in the den lets it slip; the pack hears whose teacher this was.",
    "The den has a long memory for power taken advantage of. This will be remembered.",
    "Someone saw the lesson turn to something else. The Alpha will want a word.",
]
MEDIC_PUP_SCANDAL_STANDING = -5
MEDIC_NEUTRAL_STANDING = -3
MAW_MEDIC_CRIME_KARMA = 3
RESTRICTED_HERB_MISUSE_STANDING = -4
RESTRICTED_HERB_HOARD_STANDING = -3
RESTRICTED_HERB_HOARD_CATCH_CHANCE = 0.38
RESTRICTED_HERB_MEDIC_ROUNDS_CATCH_CHANCE = 0.52
RESTRICTED_HERB_SNIFF_CATCH_CHANCE = 0.42
RESTRICTED_HERB_GROOM_CATCH_CHANCE = 0.32
RESTRICTED_HERB_HOARD_WARN = (
    "_Poison plants belong in the healers' den, not your personal bag. "
    "Turn in to a **Medic** or `/herbs action:store mode:deposit` before a patrol catches the scent._"
)
RESTRICTED_HERB_HOARD_CAUGHT_TEXT = [
    "A **Medic** traces bitter poison-scent to your herb bag; the whole den heard the lecture.",
    "Apprentices were told never to touch what you hid; an elder found your stash at dawn.",
    "The healers' store is for poison herbs, not your pockets; **{herbs}** seized and your name dragged through the nursery.",
    "Someone saw you nosing a forbidden leaf; word reached the Alpha before you could bury it.",
    "Pack law is clear: only **Medics** carry death-berries. You are not one of them.",
    "A patrol wolf flattens their ears at the reek on your pelt; **{herbs}** in a hunter's bag is exile talk.",
]
RESTRICTED_HERB_SNIFF_CAUGHT_TEXT = [
    "You read the wind, but the wind reads **you**; poison-scent on your coat gives you away to a ridge patrol.",
    "A **Medic** on morning rounds catches the bitter undertone you tried to mask with pine.",
    "Your hoard taints every breath; a denmate on the same ridge backs away and howls for the healers.",
]
RESTRICTED_HERB_GROOM_CAUGHT_TEXT = [
    "**{groomer}** gags on the poison reek tangled in your fur; the whole den will know by sunset.",
    "A grooming tongue finds **{herbs}** residue on your shoulder; your packmate yelps and calls for a **Medic**.",
    "You asked for a lick and got a trial; **{groomer}** smelled **{herbs}** and reported you on the spot.",
]
RESTRICTED_HERB_TURNIN_STANDING = 1
RESTRICTED_HERB_TURNIN_BONES = 10
# UnbelievaBoat-style trading post payouts for foraged herb stacks (by compendium rarity)
HERB_FORAGE_SELL_BONES = {
    "common": 4,
    "uncommon": 6,
    "rare": 10,
    "very_rare": 16,
}
HUNTER_HEALER_TRIBUTE_STANDING = 1
WHISPERING_WEATHER = frozenset({"fog", "rain", "storm", "sleet"})
WHISPERING_SNIFF_ANXIETY_CHANCE = 0.14
WHISPERING_SPIRIT_LINES = [
    "The fog carries a voice that is not wind; something old whispers at the edge of hearing.",
    "Mistmoor mist parts for a heartbeat; you see eyes that are not wolf, not cat, not anything you can name.",
    "A chill runs your spine: the Whispering Wild remembers every oath you almost broke.",
    "Rot-scent and ancestor-breath mix on the ridge; you are being watched.",
    "For one moment the trees lean inward, as if the land itself is listening to your thoughts.",
]
MEDIC_PUP_SCANDAL_TEXT = [
    "The den howls scandal; a healer's pup cannot stay among the sick-waiting.",
    "Elders tear the nursery apart. Your oath is ash.",
    "Whispers of forbidden milk and mate-scent reach the Alpha before dawn.",
    "Apprentices look away as the litter is driven to the border.",
]

# Lone wolves; no Great Pack affiliation
LONER_KEY = "loner"
LONER_LABEL = "Loner"
LONER_DESCRIPTION = (
    "Walks apart from any pack, holding no fixed territory. "
    "Not a **Rogue**; rogues are hostile and respect no boundaries."
)
ROGUE_KEY = "rogue"
ROGUE_LABEL = "Rogue"
ROGUE_DESCRIPTION = (
    "Cast out or self-exiled; raids pack borders, steals kills, and respects no den law. "
    "Hostile loner; other wolves treat you as a trespasser."
)
UNAFFILIATED_KEYS = frozenset({LONER_KEY, ROGUE_KEY})

# The Four Great Packs; each is also the shared player pack (treasury, wars, unity)
GREAT_PACKS = {
    "greyspire": {
        "name": "Greyspire",
        "path": "Path of the Teeth",
        "motto": "Strength is truth. Blood is law.",
        "terrain": "Mountain",
        "starting_herbs": ("arnica", "coneflower", "prickly_ash", "edelweiss"),
        "pack_trait": (
            "Stone Endurance; once per long rest, reduce damage from a single "
            "source by 1d6 + Strength modifier."
        ),
    },
    "mistmoor": {
        "name": "Mistmoor",
        "path": "Path of the Belly",
        "motto": "The swamp remembers. The Maw chews.",
        "terrain": "Swamp",
        "starting_herbs": ("elderberry", "lizards_tail", "boneset", "swamp_milkweed"),
        "pack_trait": "Rot's Blessing; advantage on saving throws against poison and disease.",
    },
    "thistlehide": {
        "name": "Thistlehide",
        "path": "Path of the Fur",
        "motto": "The forest remembers the names of the dead.",
        "terrain": "Forest",
        "starting_herbs": ("comfrey", "plantain", "oak_bark", "slippery_elm"),
        "pack_trait": (
            "Whisper Tree; once per session, ask the GM one question about the "
            "past or present in the forest, answered by your ancestor-tree."
        ),
    },
    "silverrush": {
        "name": "Silverrush",
        "path": "Path of the Tears",
        "motto": "The river flows. The stones weep.",
        "terrain": "River",
        "starting_herbs": ("meadowsweet", "alder_bark", "cattail", "purple_loosestrife"),
        "pack_trait": (
            "Swift Current; +2 to Dexterity checks involving swimming or crossing water."
        ),
    },
}

# Alternate hunt activities (bones ranges: min, max)
SCAVENGE_BONES = (2, 8)
TRACK_BONES = (8, 28)

# Sniff; wind-read once per sunrise (Wolvden-style). Every flavor line carries
# its own mechanic (see engine.prey_items.SNIFF_FLAVORS "kind"): "gather"
# grants the hunt/track/scavenge/fish bonus below, "water" restores thirst,
# "alert" raises this sniff's encounter odds by SNIFF_ALERT_ENCOUNTER_BONUS.
SNIFF_HUNT_BONUS_PCT = 15
SNIFF_WOLF_ENCOUNTER_CHANCE = 0.15
SNIFF_WOLF_ENCOUNTER_MOOD = 4
SNIFF_ALERT_ENCOUNTER_BONUS = 0.20
# Border patrol; clan cat fight from /sniff (only if no wolf encounter that sniff)
SNIFF_CAT_ENCOUNTER_CHANCE = 0.12
BORDER_CAT_STANDING = 2
BORDER_CAT_MOOD = 5
BORDER_CAT_BONES = (3, 8)

# Cat clan pacts; pack treaties with forest cats (Warrior Cats-style diplomacy)
CAT_PACT_MAX_ACTIVE = 2
CAT_PACT_TRUCE_DAYS = 12
CAT_PACT_TRUCE_TRIBUTE = 30
CAT_PACT_TRUCE_DC = 14
CAT_PACT_TRUCE_UNITY = 1
CAT_PACT_ALLIANCE_DAYS = 18
CAT_PACT_ALLIANCE_TRIBUTE = 80
CAT_PACT_ALLIANCE_DC = 17
CAT_PACT_ALLIANCE_UNITY = 2
CAT_PACT_HUNTING_DAYS = 8
CAT_PACT_HUNTING_TRIBUTE = 15
CAT_PACT_HUNTING_PERSONAL = 10
CAT_PACT_HUNTING_DC = 12
CAT_PACT_DIPLOMAT_NEGOTIATE_BONUS = 2
CAT_PACT_FORGE_FAIL_COOLDOWN_DAYS = 3
# A wolf's own broken oaths follow them personally into future negotiations,
# on top of whatever cooldown/relation penalty their den already eats.
OATHBREAKER_FORGE_DC_PER_BREAK = 1
OATHBREAKER_FORGE_DC_CAP = 5
CAT_PACT_GIFT_TRIBUTE = 15
CAT_PACT_GIFT_TRUST = 8
CAT_PACT_DUP_TRUST_PER_ITEM = 2
CAT_PACT_DUP_TRUST_MAX = 14
CAT_PACT_BARTER_PER_DUPES = 2
CAT_PACT_BARTER_LOOT_MAX = 6
# Food barter: forest cats are OBLIGATE carnivores (taurine, vitamin A, etc. only
# from meat). They prize a carcass and have little use for plant food, taking
# fruit/berries/greens only to barter onward or line kit nests. So meat earns
# real trust/loot; forage earns a token amount.
CAT_PACT_FOOD_MEAT_TRUST_PER_BONE = 0.30
CAT_PACT_FOOD_FORAGE_TRUST_PER_USE = 1
CAT_PACT_FOOD_TRUST_MAX = 16
CAT_PACT_FOOD_LOOT_MAX = 6
CAT_PACT_RECEIVE_MIN_TRUST = 35
PACK_DUP_TRADE_MIN_RELATION = 5
PACK_DUP_TRADE_RELATION_GAIN = 1
CAT_PACT_TRUST_HIGH = 70
CAT_PACT_TRUST_LOW = 35
CAT_PACT_VIOLATION_TRUST = -30
CAT_PACT_VIOLATION_UNITY = -4
CAT_PACT_VIOLATION_STANDING = -3

# Wolf pack treaties (standing 0 to 10 scale)
WOLF_PACT_RECEIVE_MIN_STANDING = 7
WOLF_PACT_GIFT_STANDING = 1
WOLF_PACT_FOOD_STANDING_MAX = 2
WOLF_PACT_FOOD_MEAT_STANDING_PER_BONE = 0.15
WOLF_PACT_FOOD_FORAGE_STANDING_PER_USE = 0.25
WOLF_PACT_DUP_STANDING_MAX = 2

# Sniff the wind
SNIFF_THIRST_RESTORE = 10
CAT_PACT_PATROL_TEMPLATES = frozenset({"clan_warrior", "clan_deputy"})
# Seasonal Gathering (Warrior Cats Fourtrees truce)
CAT_GATHERING_UNITY = 2
CAT_GATHERING_STANDING = 1
CAT_GATHERING_MOOD = 3
# StarClan omens on high-trust clan receive
CAT_PACT_STARCLAN_RECEIVE_CHANCE = 0.18
CAT_PACT_STARCLAN_MOOD = 3
# Firepaw plot mechanics (Book One: The Blinking)
FIREPAW_PLOT_SNIFF_MOOD_EARLY = 2
FIREPAW_PLOT_SNIFF_MOOD_LATE = 1
FIREPAW_PLOT_SNIFF_STANDING = 1
FIREPAW_PLOT_TREAT_HEAL_BONUS = 2
FIREPAW_PLOT_TREAT_STANDING = 1
FIREPAW_PLOT_TREAT_MOOD_SELF = 2
FIREPAW_PLOT_OBSERVE_MOOD = 2
FIREPAW_PLOT_OBSERVE_STRAIN_RELIEF = 2
# Soot plot mechanics (Book One: The Blinking; Mistmoor rot-lung lane)
SOOT_PLOT_SNIFF_MOOD = 2
SOOT_PLOT_SNIFF_STANDING = 1
SOOT_PLOT_TREAT_HEAL_BONUS = 2
SOOT_PLOT_ROT_LUNG_HEAL_BONUS = 1
SOOT_PLOT_TREAT_STANDING = 1
SOOT_PLOT_TREAT_MOOD_SELF = 2
SOOT_PLOT_OBSERVE_MOOD = 2
SOOT_PLOT_OBSERVE_STRAIN_RELIEF = 2
# River'Shroud alpha plot (Book One; Thistlehide border)
RIVERSHROUD_PLOT_SNIFF_MOOD_EARLY = 1
RIVERSHROUD_PLOT_SNIFF_MOOD_LATE = 1
RIVERSHROUD_PLOT_SNIFF_STANDING = 2
RIVERSHROUD_PLOT_PATROL_STANDING = 1
RIVERSHROUD_PLOT_HOWL_UNITY = 1  # phases 9 to 11, stacks with Ash Naming unity
# Finnpelt hunter plot (Book One; Greyspire ridge)
FINNPELT_PLOT_SNIFF_MOOD = 2
FINNPELT_PLOT_SNIFF_STANDING = 1
FINNPELT_PLOT_PATROL_STANDING = 1
# MaggotBrain hunter plot (Book One; Mistmoor rot)
MAGGOTBRAIN_PLOT_SNIFF_MOOD = 2
MAGGOTBRAIN_PLOT_SNIFF_STANDING = 1
# Universal plot witness (once per sunrise, any wolf)
PLOT_WITNESS_MOOD = 1
# Generic "every canon wolf is part of the plot" rollover nudge (Book One, any phase)
NAMED_WOLF_BLINK_MOOD = 2
PLOT_GENERIC_HEALER_STANDING = 1
PLOT_GENERIC_HEALER_MOOD = 1
FISHING_BONES = (10, 22)
# Brackenpelt hunter plot (Book One; Thistlehide border)
BRACKENPELT_PLOT_PATROL_STANDING = 1
# Icefang Stoneguard plot (Book One; Greyspire border)
ICEFANG_PLOT_PATROL_STANDING = 1
# Book One healer treat-heal bonuses (phases 5 to 11)
HEMLOCK_PLOT_TREAT_HEAL_BONUS = 2   # greyspire medic
RIPPLE_PLOT_TREAT_HEAL_BONUS = 1    # silverrush healer
SYPHA_PLOT_TREAT_HEAL_BONUS = 2     # thistlehide healer
MIREWORT_PLOT_TREAT_HEAL_BONUS = 2  # mistmoor medic (bookone's mistmoor treat lane)
# extra heal when treating rot-lung specifically (rot-lung specialists)
RIPPLE_PLOT_ROT_LUNG_HEAL_BONUS = 1
MIREWORT_PLOT_ROT_LUNG_HEAL_BONUS = 2
# observe strain relief per healer (phases 5 to 11)
HEALER_PLOT_OBSERVE_STRAIN = {"Hemlock": 3, "Ripple": 2, "Mirewort": 3, "Sypha": 3, "Rotteddust": 1}
# Grim greyspire-alpha sniff omen (paranoia): chance for pack-wide standing
GRIM_PLOT_OMEN_CHANCE = 0.20
GRIM_PLOT_OMEN_STANDING = 2
# scout survey standing bonus (while plot active) — Stonepiercer, Raven, Ebb, Yarrow, Mossheart
STONEPIERCER_PLOT_SURVEY_STANDING = 1
PLOT_SURVEY_STANDING = 1
# thistlehide/mistmoor plot foragers scavenge mult
FORAGER_PLOT_SCAVENGE_MULT = 1.10
# Moth greyspire-lowbelly work payout multiplier (while plot active)
MOTH_PLOT_WORK_MULT = 2.0
# Sleet greyspire-diplomat: extra standing when approaching thorne lumber
SLEET_PLOT_FACTION_STANDING = 1
# Sleet softens her pack's paranoia cat-trust loss by this much (toward 0)
SLEET_PLOT_CAT_TRUST_RELIEF = 2
# Moth: extra standing on a rank-dispute win while the plot is active
MOTH_PLOT_RANK_STANDING = 3
# Gasp: extra standing when drawing a prophecy while the plot is active
GASP_PLOT_PROPHECY_STANDING = 1
# Pebble (silverrush) and Reedwhisper (mistmoor) diplomat faction-approach bonuses
PEBBLE_PLOT_FACTION_STANDING = 1
REEDWHISPER_PLOT_FACTION_STANDING = 2
# Ashbark (thistlehide hunter) patrol standing during paranoia
ASHBARK_PLOT_PATROL_STANDING = 1
# Cinder (silverrush driftwood) scavenge multiplier while plot active
CINDER_PLOT_SCAVENGE_MULT = 1.10
# Rotteddust (mistmoor healer apprentice) treat heal bonus (phases 5-11)
ROTTEDDUST_PLOT_TREAT_HEAL_BONUS = 1
# Rivenmaw (thistlehide hunter) hunt multiplier during paranoia
RIVENMAW_PLOT_HUNT_MULT = 1.10
# Scab (greyspire lowbelly) scavenge mult; Talus (greyspire hunter) hunt mult
SCAB_PLOT_SCAVENGE_MULT = 1.15
TALUS_PLOT_HUNT_MULT = 1.10
# Dusk (mistmoor beta) sunrise cache-find: chance and bones
DUSK_PLOT_CACHE_CHANCE = 0.20
DUSK_PLOT_CACHE_BONES = 3
# each named plot pup steadies a little each sunrise during the blinking
PLOT_PUP_MOOD = 1
# Aromis fishing plot (Book One; Silverrush, Warm Below)
AROMIS_PLOT_FISHING_MULT = 1.15
# Lucid tracking plot (Book One; Thistlehide border)
LUCID_PLOT_TRACK_MULT = 1.10
# Cloverfern scavenge plot (Book One; Thistlehide den)
CLOVERFERN_PLOT_SCAVENGE_MULT = 1.10
# Kanami and Skye border-sense plot (Book One; Thistlehide paranoia)
KANAMI_PLOT_BORDER_MULT = 0.75
SKYE_PLOT_BORDER_MULT = 0.75
# Book One payout lanes (batch): hunters, fishers, forager
IRONJAW_PLOT_HUNT_MULT = 1.15    # greyspire hunter; phases 3 & 9 (stacks with phase-3 pack bonus)
SLATE_PLOT_HUNT_MULT = 1.10      # greyspire hunter; phases 3 & 7
SLUDGE_PLOT_HUNT_MULT = 1.20     # mistmoor hunter; water hunts while plot active
CROAKER_PLOT_FISHING_MULT = 1.30  # silverrush fisher; phases 4 & 8
CURLGRIP_PLOT_FISHING_MULT = 1.20  # silverrush fisher; phases 4 & 8
MOSSGAZE_PLOT_SCAVENGE_MULT = 1.10  # thistlehide forager; while plot active

# Pack warfare
WAR_DURATION_DAYS = 2
NEUTRAL_CLAIM_SCORE = 12

# Pack unity (−5 to 10). At −5 the Great Pack fractures; all members become loners.
PACK_UNITY_MIN = -5
PACK_UNITY_MAX = 10
PACK_UNITY_DISSOLVE_THRESHOLD = -5

# Den upgrades; treasury-funded infrastructure that blunts bad-weather hunt
# penalties instead of treasury only ever being stipends and raids.
DEN_UPGRADE_MAX_LEVEL = 5
DEN_UPGRADE_BASE_COST = 300  # cost for level N = DEN_UPGRADE_BASE_COST * N
DEN_UPGRADE_WEATHER_MITIGATION_PCT = 3  # per level, off the magnitude of a negative weather modifier

# Personal standing within the pack. At −5 the wolf is cast out as a loner.
WOLF_STANDING_MIN = -10
WOLF_STANDING_KICK_THRESHOLD = -5
# A cast-out wolf can't simply pay the setfaction fee and walk back into the
# same den; exile has to mean something. The alpha of that pack can lift it
# early with `/pack pardon`.
EXILE_REJOIN_COOLDOWN_DAYS = 30
# A wolf this respected/feared in their own den is known beyond it too;
# crossing paths with one on friendly ground is worth a little extra to
# the wolf who isn't (yet) as notorious.
WOLF_NOTORIETY_STANDING_THRESHOLD = 20
WOLF_NOTORIETY_SNIFF_MOOD = 3
DEFAULT_TERRITORIES = (
    ("pine_ridge", "Pine Ridge", 5),
    ("river_crossing", "River Crossing", 8),
    ("old_quarry", "Old Quarry", 6),
    ("mistwood", "Mistwood", 7),
    ("stoneroot", "Stoneroot", 10),
    ("deepfurrow", "Deep Furrow", 9),
)

# Suggested /location set place: values; autocomplete only, free text always allowed.
# Grouped by Great Pack terrain, plus the contestable DEFAULT_TERRITORIES and a
# handful of shared/neutral spots referenced across pack lore and pack traits.
RP_LOCATIONS = (
    # Greyspire (Mountain); "the mouth of the world"
    "Greyspire Den",
    "Greyspire High Ridge",
    "The High Pass",
    "Stoneguard Watch",
    "The Ice Caves",
    "The Volcanic Vents",
    "The Narrow Passes",
    "The High Ledge",  # exile/death-by-cold site
    "The Miners' Camp",
    "The Screaming Earth",  # the blast zone
    # Silverrush (River); "the Maw's tears"
    "Silverrush Den",
    "The River's Edge",
    "The Sandbar",
    "The Deep Channels",
    "The Rapids",
    "The Shallows",  # where warriors fight
    "The Neutral Bend",
    "The Maw's Mouth",  # drown-rite pool
    "The Weep Stone",
    "The Dam",
    "Riverbank Dens",
    # Mistmoor (Swamp); "the Maw's belly"
    "Mistmoor Den",
    "The Belly-Rip",
    "The Rotting Mere",
    "The Bog",
    "Glow-Fungus Hollow",
    "The Sick Den",
    "The Sog Grave",
    "The Rot-Feast Grounds",
    "The Sinkholes",
    "The Half-Sunken Chapel",
    "The Collapsed Bridge",
    "The Brackish Reach",  # MaggotBrain's stretch of stagnant water and cypress
    # Thistlehide (Forest); "the Maw's fur"
    "Thistlehide Den",
    "The Whisper Tree",
    "The Thistle Thicket",
    "The Sparring Grounds",
    "The Thunderpath",  # logging-truck highway
    "The Pipeline Stakes",
    "The Bark-Burial Trees",
    "The High Valley",  # border dispute with Greyspire
    # Contestable territories (see DEFAULT_TERRITORIES)
    "Pine Ridge",
    "River Crossing",
    "Old Quarry",
    "Mistwood",
    "Stoneroot",
    "Deep Furrow",
    # Shared / neutral
    "The Borderlands",
    "Neutral Grounds",
    "The Fresh-Kill Pile",
    "The Nursery Den",
    "The Elder's Den",
    "Rogue Camp",
    "The Sundering Stone",  # prophecy stone; no pack dares enter
)

# Static quests: key, title, description, objective, count, reward, standing, type, difficulty
STATIC_QUESTS = (
    (
        "first_hunt",
        "First Blood",
        "Complete your first hunt and bring meat back to the den.",
        "hunt",
        1,
        50,
        5,
        "unique",
        "easy",
    ),
    (
        "den_patrol",
        "Border Patrol",
        "Walk the pack border and watch for rival scent.",
        "patrol",
        1,
        35,
        3,
        "static",
        "easy",
    ),
    (
        "river_fish",
        "River Rations",
        "Catch fish from the Silverrush shallows.",
        "fishing",
        1,
        40,
        3,
        "static",
        "easy",
    ),
    (
        "triple_tracker",
        "Master Tracker",
        "Follow three separate scent trails to their source.",
        "track",
        3,
        120,
        10,
        "static",
        "medium",
    ),
    (
        "den_gift",
        "Feed the Treasury",
        "Deposit 50 bones into your pack treasury.",
        "deposit",
        50,
        60,
        8,
        "static",
        "medium",
    ),
    (
        "biome_wander",
        "Range the Wild",
        "Venture beyond the den; dig, follow scent, or investigate the biome.",
        "explore",
        1,
        30,
        3,
        "static",
        "easy",
    ),
    (
        "trail_seeker",
        "Old Trails",
        "Explore the wild three separate sunrises.",
        "explore",
        3,
        90,
        8,
        "static",
        "medium",
    ),
    (
        "blink_border_patrol",
        "White Omen Patrol",
        "Walk the border while the moon is bitten; report what you scent.",
        "patrol",
        1,
        45,
        4,
        "static",
        "easy",
    ),
    (
        "blink_river_crisis",
        "Warm Shallows",
        "Fish the river twice while the water runs wrong.",
        "fishing",
        2,
        55,
        5,
        "static",
        "medium",
    ),
    (
        "blink_wind_witness",
        "Wind Witness",
        "Read the wind on a paranoid border sunrise.",
        "sniff",
        1,
        40,
        4,
        "static",
        "easy",
    ),
    (
        "blink_mill_scout",
        "Mill Scout",
        "Range the wild and investigate what sleeps under the mill road.",
        "explore",
        1,
        70,
        6,
        "static",
        "medium",
    ),
    (
        "blink_ash_naming",
        "Ash Naming Howl",
        "Sing the remembered name to the pack three sunrises.",
        "howl",
        3,
        80,
        8,
        "static",
        "medium",
    ),
    (
        "blink_rogue_ledger",
        "Edge Ledger",
        "Run two scores on the border while packs blame each other (rogues).",
        "crime",
        2,
        65,
        5,
        "static",
        "medium",
    ),
    (
        "blink_healer_listen",
        "Ear to the Wind",
        "Read the bitten moon by sound while The Blinking begins.",
        "sniff",
        1,
        40,
        4,
        "static",
        "easy",
    ),
    (
        "blink_healer_touch",
        "Healer's Touch",
        "Treat wounds twice while the den runs hot with injuries.",
        "treat",
        2,
        55,
        5,
        "static",
        "medium",
    ),
)

# Per-quest XP (account pool) and skill-rank rewards (active wolf).
# Skill rewards: quest_key -> (skill_key, rank_gain). Rank adds +SKILL_RANK_BONUS per rank on checks.
QUEST_XP_REWARDS: dict[str, int] = {
    # Static board
    "first_hunt": 2,
    "den_patrol": 1,
    "river_fish": 1,
    "triple_tracker": 2,
    "den_gift": 1,
    "biome_wander": 1,
    "trail_seeker": 2,
    "blink_border_patrol": 1,
    "blink_river_crisis": 1,
    "blink_wind_witness": 1,
    "blink_mill_scout": 2,
    "blink_ash_naming": 2,
    "blink_rogue_ledger": 2,
    "blink_healer_listen": 1,
    "blink_healer_touch": 2,
    # Role quests
    "hunter_first_blood": 2,
    "medic_healer_path": 2,
    "scout_border_eyes": 1,
    "scout_biome_eyes": 1,
    "scout_wind_survey": 2,
    "scout_trail_hunter": 2,
    "guard_den_watch": 1,
    "forager_root_seeker": 1,
    "diplomat_peace_talk": 2,
    "elder_memory_howl": 1,
    "caretaker_pup_watch": 1,
    "alpha_den_judgment": 3,
    "advisor_alpha_shadow": 2,
    "drown_belly_vigil": 2,
    "drown_moon_prophecy": 2,
    "drown_whisper_stone": 3,
    "pup_first_moon": 1,
    "pup_den_warmth": 1,
    "juvenile_blooding": 2,
    "juvenile_rank_patrol": 1,
    "juvenile_practice_hunt": 2,
    # Daily quests
    "daily_hunt": 1,
    "daily_scavenge": 1,
    "daily_track": 1,
    "daily_fish": 1,
    "daily_deep_scrape": 2,
    "daily_river_storm": 2,
}

QUEST_SKILL_REWARDS: dict[str, tuple[str, int]] = {
    # Static board
    "first_hunt": ("hunting", 1),
    "den_patrol": ("stealth", 1),
    "river_fish": ("survival", 1),
    "triple_tracker": ("tracking", 1),
    "biome_wander": ("survival", 1),
    "trail_seeker": ("tracking", 1),
    "den_gift": ("persuasion", 1),
    "blink_border_patrol": ("stealth", 1),
    "blink_river_crisis": ("survival", 1),
    "blink_wind_witness": ("tracking", 1),
    "blink_mill_scout": ("survival", 1),
    "blink_ash_naming": ("persuasion", 1),
    "blink_rogue_ledger": ("stealth", 1),
    "blink_healer_listen": ("medicine", 1),
    "blink_healer_touch": ("medicine", 1),
    # Role quests
    "hunter_first_blood": ("hunting", 1),
    "medic_healer_path": ("medicine", 1),
    "scout_border_eyes": ("stealth", 1),
    "scout_biome_eyes": ("tracking", 1),
    "scout_wind_survey": ("tracking", 1),
    "scout_trail_hunter": ("tracking", 1),
    "guard_den_watch": ("survival", 1),
    "forager_root_seeker": ("herblore", 1),
    "diplomat_peace_talk": ("persuasion", 1),
    "elder_memory_howl": ("medicine", 1),
    "caretaker_pup_watch": ("persuasion", 1),
    "alpha_den_judgment": ("intimidation", 1),
    "advisor_alpha_shadow": ("persuasion", 1),
    "drown_belly_vigil": ("stealth", 1),
    "drown_moon_prophecy": ("tracking", 1),
    "drown_whisper_stone": ("tracking", 1),
    "pup_first_moon": ("survival", 1),
    "pup_den_warmth": ("survival", 1),
    "juvenile_blooding": ("hunting", 1),
    "juvenile_rank_patrol": ("stealth", 1),
    "juvenile_practice_hunt": ("hunting", 1),
    # Daily quests
    "daily_hunt": ("hunting", 1),
    "daily_scavenge": ("survival", 1),
    "daily_track": ("tracking", 1),
    "daily_fish": ("survival", 1),
    "daily_deep_scrape": ("survival", 1),
    "daily_river_storm": ("survival", 1),
}

# Achievements; auto-granted to every wolf at registration (see
# database.ensure_achievement_quests), never expire, never accepted from a
# board. Reuses the same objective_type counters every other quest already
# increments, just at lifetime-milestone scale. Completion also writes a
# wolf journal entry (engine.wolf_journal.log_achievement).
ACHIEVEMENT_QUESTS = (
    (
        "trophy_hundred_hunts",
        "Hundred Hunts",
        "Bring down one hundred hunts over your lifetime.",
        "hunt",
        100,
        200,
        0,
        "achievement",
        "hard",
    ),
    (
        "trophy_healers_hands",
        "Healer's Hands",
        "Treat fifty wounds or illnesses over your lifetime.",
        "treat",
        50,
        150,
        0,
        "achievement",
        "hard",
    ),
    (
        "trophy_tireless_scavenger",
        "Tireless Scavenger",
        "Scavenge one hundred carcasses over your lifetime.",
        "scavenge",
        100,
        150,
        0,
        "achievement",
        "hard",
    ),
    (
        "trophy_rivers_friend",
        "River's Friend",
        "Catch fifty fish over your lifetime.",
        "fishing",
        50,
        150,
        0,
        "achievement",
        "hard",
    ),
    (
        "trophy_green_thumb",
        "Green Thumb",
        "Forage one hundred times over your lifetime.",
        "forage",
        100,
        150,
        0,
        "achievement",
        "hard",
    ),
)

# Role quests: key, title, desc, objective, count, reward, standing, type, difficulty, role[, pack]
ROLE_QUESTS = (
    (
        "hunter_first_blood",
        "Prove the Kill",
        "Bring down prey with your jaws alone; the pack watches hunters.",
        "hunt",
        2,
        70,
        5,
        "role",
        "easy",
        "hunter",
        None,
    ),
    (
        "medic_healer_path",
        "Poultice for the Den",
        "Tend the wounded; use `/medic action:treat` with a herb or `/medic action:stabilize` a dying packmate.",
        "treat",
        1,
        55,
        6,
        "role",
        "easy",
        "medic",
        None,
    ),
    (
        "scout_border_eyes",
        "Eyes on the Ridge",
        "Walk the border unseen. Report what moves in rival scent.",
        "patrol",
        2,
        65,
        5,
        "role",
        "medium",
        "scout",
        None,
    ),
    (
        "scout_biome_eyes",
        "Read the Land",
        "Rescout your biome after ranging out; read what the wild left behind.",
        "explore",
        2,
        55,
        5,
        "role",
        "easy",
        "scout",
        None,
    ),
    (
        "scout_wind_survey",
        "Wind on the Ridge",
        "Survey the border and report what moves; `/scout survey`.",
        "survey",
        3,
        65,
        6,
        "role",
        "medium",
        "scout",
        None,
    ),
    (
        "scout_trail_hunter",
        "Cold Trail",
        "Follow sign off the main paths; `/scout trail`.",
        "trail",
        3,
        70,
        5,
        "role",
        "medium",
        "scout",
        None,
    ),
    (
        "guard_den_watch",
        "Night at the Entrance",
        "Stand watch while the den sleeps.",
        "patrol",
        2,
        60,
        6,
        "role",
        "medium",
        "guard",
        None,
    ),
    (
        "forager_root_seeker",
        "Roots in the Rain",
        "Find what the forest offers after the storm.",
        "forage",
        2,
        50,
        4,
        "role",
        "easy",
        "forager",
        None,
    ),
    (
        "diplomat_peace_talk",
        "Words Before Teeth",
        "Mediate tension before it becomes blood.",
        "patrol",
        1,
        55,
        8,
        "role",
        "medium",
        "diplomat",
        None,
    ),
    (
        "elder_memory_howl",
        "Howl the Old Names",
        "Speak the names of wolves the land still remembers.",
        "patrol",
        1,
        45,
        7,
        "role",
        "easy",
        "elder",
        None,
    ),
    (
        "caretaker_pup_watch",
        "Pups in the Storm",
        "Keep the young ones calm through foul weather.",
        "patrol",
        1,
        40,
        6,
        "role",
        "easy",
        "caretaker",
        None,
    ),
    (
        "alpha_den_judgment",
        "Alpha's Judgment",
        "Settle a dispute before the den fractures.",
        "deposit",
        25,
        80,
        10,
        "role",
        "hard",
        "alpha",
        None,
    ),
    (
        "advisor_alpha_shadow",
        "Walk in the Alpha's Shadow",
        "Counsel the pack while the Alpha hunts.",
        "patrol",
        2,
        70,
        7,
        "role",
        "medium",
        "advisor",
        None,
    ),
    (
        "drown_belly_vigil",
        "Vigil at the Belly-Rip",
        "Sit at the dark water until the chewing speaks. Mistmoor tradition.",
        "patrol",
        1,
        75,
        10,
        "role",
        "medium",
        "drown_sick",
        "mistmoor",
    ),
    (
        "drown_moon_prophecy",
        "When the Eye Blinks",
        "Watch the Maw's moon until meaning finds you.",
        "patrol",
        1,
        90,
        12,
        "role",
        "hard",
        "drown_sick",
        "mistmoor",
    ),
    (
        "drown_whisper_stone",
        "The Sundering Stone",
        "Find the carved prophecy in neutral ground; if the land lets you.",
        "track",
        1,
        100,
        15,
        "unique",
        "hard",
        "drown_sick",
        None,
    ),
    (
        "pup_first_moon",
        "Survive the First Moon",
        "Live through the first moon unnamed; then earn your name at the ceremony.",
        "patrol",
        1,
        35,
        5,
        "role",
        "easy",
        "pup",
        None,
    ),
    (
        "pup_den_warmth",
        "Stay in the Nursery",
        "Rest close to caretakers while the adults hunt.",
        "patrol",
        2,
        30,
        4,
        "role",
        "easy",
        "pup",
        None,
    ),
    (
        "juvenile_blooding",
        "The Blooding",
        "Kill a rabbit or larger prey alone to prove you can earn an adult role.",
        "hunt",
        1,
        80,
        8,
        "role",
        "medium",
        "juvenile",
        None,
    ),
    (
        "juvenile_rank_patrol",
        "Border Yearling",
        "Walk the juvenile patrol route without crying a challenge howl.",
        "patrol",
        2,
        55,
        5,
        "role",
        "easy",
        "juvenile",
        None,
    ),
    (
        "juvenile_practice_hunt",
        "Practice Kill",
        "Complete hunts on live training prey assigned by the den.",
        "hunt",
        2,
        70,
        6,
        "role",
        "medium",
        "juvenile",
        None,
    ),
    # Pack-wide plot hooks; open to any role in the listed pack, so they sit
    # on the general board (quest_type "unique") rather than the per-role
    # list, which only ever shows rows with a required_role set.
    (
        "dam_sabotage_run",
        "The Dam Must Fall",
        "Scout the upstream dam for Silverrush; Thistlehide volunteers know explosives from the mining camp, "
        "Greyspire wants it gone too, and a Mistmoor spy is watching from the reeds. Almost certainly a death sentence.",
        "patrol",
        3,
        110,
        14,
        "unique",
        "hard",
        None,
        "silverrush",
    ),
    (
        "pipeline_survey_raid",
        "Stakes in the Dark",
        "Raid the Twoleg survey camps by night; steal stakes, leave mutilated dolls behind. Poison bait and "
        "leg-holds answer back, and a Thistlehide pup has already died to them.",
        "scavenge",
        3,
        90,
        10,
        "unique",
        "hard",
        None,
        "thistlehide",
    ),
    (
        "mining_camp_raid",
        "Screaming Earth",
        "Renegade young Greyspire wolves plan a raid on the miners' supply cache for explosives and guns. "
        "The elders forbid it; the Beta secretly backs it.",
        "scavenge",
        3,
        100,
        -3,
        "unique",
        "hard",
        None,
        "greyspire",
    ),
    (
        "rot_feast_envoy",
        "The Rot-Feast Invitation",
        "Once a year Mistmoor invites one wolf from another pack to witness a rot-feast; a test of diplomacy "
        "and stomach. The Maw accepts your offering, whether or not you keep it down.",
        "patrol",
        1,
        70,
        8,
        "unique",
        "medium",
        None,
        None,
    ),
)

# Daily quest templates by difficulty
DAILY_QUEST_TEMPLATES = {
    "easy": (
        ("daily_hunt", "Morning Hunt", "Complete a hunt.", "hunt", 1, 50),
        ("daily_scavenge", "Scrap Search", "Scavenge the trails.", "scavenge", 1, 45),
    ),
    "medium": (
        ("daily_track", "Scent Trail", "Track prey through the brush.", "track", 1, 100),
        ("daily_fish", "River Watch", "Fish the riverbank.", "fishing", 1, 95),
    ),
    "hard": (
        ("daily_deep_scrape", "Deep Den Dig", "Scour the oldest trails for hidden bone.", "scavenge", 1, 165),
        ("daily_river_storm", "Storm Fishing", "Fish the river despite foul weather.", "fishing", 1, 155),
    ),
}

SETFACTION_CHANGE_COST = 500

# Prestige tiers; account-wide, permanent bonuses (bone_bonus_pct stacks per tier reached)
PRESTIGE_TIERS = (
    {
        "tier": 0,
        "name": "The Unremembered",
        "lore": "Your name is mist on the wind. The Maw does not know you yet.",
        "legacy_req": 0,
        "quests_req": 0,
        "hunts_req": 0,
        "retirements_req": 0,
        "bone_bonus_pct": 0,
        "title": None,
    },
    {
        "tier": 1,
        "name": "The Named",
        "lore": "The pack knows your howl. The Maw has tasted your scent.",
        "legacy_req": 100,
        "quests_req": 3,
        "hunts_req": 0,
        "retirements_req": 0,
        "bone_bonus_pct": 5,
        "title": "The Named",
    },
    {
        "tier": 2,
        "name": "The Story-Weaver",
        "lore": "Your deeds are spoken around the den-fire.",
        "legacy_req": 500,
        "quests_req": 8,
        "hunts_req": 25,
        "retirements_req": 0,
        "bone_bonus_pct": 15,
        "title": "The Story-Weaver",
    },
    {
        "tier": 3,
        "name": "The Claimed",
        "lore": "The Maw has marked you. Your scent carries weight.",
        "legacy_req": 1500,
        "quests_req": 15,
        "hunts_req": 100,
        "retirements_req": 0,
        "bone_bonus_pct": 30,
        "title": "The Claimed",
    },
    {
        "tier": 4,
        "name": "The Bone-Weaver",
        "lore": "You have walked the Furrow. The Maw's eye lingers on you.",
        "legacy_req": 5000,
        "quests_req": 25,
        "hunts_req": 250,
        "retirements_req": 2,
        "bone_bonus_pct": 50,
        "title": "The Bone-Weaver",
    },
    {
        "tier": 5,
        "name": "The Fangborn",
        "lore": "Your lineage is older than the Sundering.",
        "legacy_req": 15000,
        "quests_req": 40,
        "hunts_req": 500,
        "retirements_req": 5,
        "bone_bonus_pct": 75,
        "title": "The Fangborn",
    },
    {
        "tier": 6,
        "name": "The Primordial",
        "lore": "You are the Maw's memory of a wolf.",
        "legacy_req": 50000,
        "quests_req": 60,
        "hunts_req": 1000,
        "retirements_req": 10,
        "bone_bonus_pct": 105,
        "title": "The Primordial",
    },
    {
        "tier": 7,
        "name": "The Sunderer",
        "lore": "You remember the split, and you remember why.",
        "legacy_req": 150000,
        "quests_req": 80,
        "hunts_req": 2500,
        "retirements_req": 20,
        "bone_bonus_pct": 145,
        "title": "The Sunderer",
    },
)

# Great Pack prestige path labels (future expansion)
GREAT_PACK_PATH_TIERS = {
    "greyspire": "Path of the Teeth",
    "mistmoor": "Path of the Belly",
    "thistlehide": "Path of the Fur",
    "silverrush": "Path of the Tears",
}
