import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "fable.db"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
STATUS_CHANNEL_ID = os.getenv("STATUS_CHANNEL_ID")
BOT_DISPLAY_NAME = os.getenv("BOT_DISPLAY_NAME", "Howlbert")

# Auto rollover; one sunrise per IRL day at this clock time (server TZ)
AUTO_ROLLOVER_ENABLED = os.getenv("AUTO_ROLLOVER_ENABLED", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)
ROLLOVER_TIMEZONE = os.getenv("ROLLOVER_TIMEZONE", "UTC").strip() or "UTC"
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

# Currency; bones only
CURRENCY_EMOJI = "🦴"
CURRENCY_NAME = "Bones"
CURRENCY_LABEL = f"{CURRENCY_EMOJI} {CURRENCY_NAME}"

# Economy; sunrise stipend paid from pack treasury (see claim_daily_stipend)
DAILY_REWARD = 25
MAX_PACK_TAX_RATE = 25
MAX_WOLVES_PER_PLAYER = 3

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
        "Use `/use item:herb_bundle`; random common herbs (2-4) added to `/inventory`.",
        40,
        12,
    ),
    (
        "prey_bundle",
        "Prey Bundle",
        "Use `/use item:prey_bundle`; random carcasses (2-3) added to `/prey`.",
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
        "den_charm",
        "Den Charm",
        "Use `/use item:den_charm`; +1 pack unity once per rollover (must be in a pack).",
        100,
        30,
    ),
    (
        "rabbit_pelt",
        "Rabbit Pelt",
        "Use `/use item:rabbit_pelt recipient:@wolf`; trade for +2 standing; they gain 10 bones.",
        55,
        15,
    ),
    (
        "extra_paw",
        "An Extra Paw",
        "Add RP to `/work` or `/crime`: your own `scene:` text, or `staff:true` for admin-written flavor (uses one).",
        150,
        40,
    ),
    (
        "safe_roll",
        "Safe Roll",
        "🎲 `/roll use_safe_roll:true`; reroll a failed d20 once. **Cannot** be used in combat.",
        100,
        30,
    ),
    (
        "revive",
        "Revive",
        "Use `/use item:revive` when your active wolf is **dead**; same name & stats, back at 1 HP. "
        "Old-age deaths reset to 60 moons. **Ko-fi shop only**.",
        0,
        0,
    ),
    (
        "reincarnation",
        "Reincarnation",
        "Use `/use item:reincarnation new_name:<name>` when **dead**; new name & juvenile age (12 moons), "
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
HUNGER_MIN = 0
HUNGER_MAX = 100
HUNGER_DEFAULT = 80
HUNGER_ROLLOVER_DECAY = 12
HUNGER_LOW_THRESHOLD = 30
HUNGER_CRITICAL_THRESHOLD = 15
HUNGER_HUNT_PENALTY_PCT = 20
HUNGER_SICK_EXTRA_DECAY = 6

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
HUNT_WILD_ENCOUNTER_CHANCE = 8
EXPLORE_WILD_ENCOUNTER_CHANCE = 10
WILD_ENCOUNTER_COOLDOWN_MINUTES = 90
HUNTER_HUNTS_PER_SUNRISE = 3

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
# Poultice, tonic, and decoction spoil after this many sunrises (Basil: 4-5)
HERB_PREPARED_STORAGE_DAYS = 5
HERB_PREPARED_FORMS = ("poultice", "tonic", "decoction")
# Failed winter forage may spoil a random herb stack in the bag
WINTER_FORAGE_SPOIL_CHANCE = 0.35
# Bone splint rest after successful set_bone surgery (sunrises)
BONE_REST_DAYS = 7
HERB_PREP_DC = {
    "poultice": 10,
    "poultice_simple": 0,
    "tonic": 12,
    "decoction": 15,
    "dry": 8,
    "dry_storage": 10,
    "chew_poultice": 8,
    "preserve_rare": 15,
    "antidote": 18,
    "sedative": 8,
    "incomplete_antidote": 20,
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
SOCIALIZE_UNITY_AWKWARD = -1
SOCIALIZE_UNITY_SCRAP = -2
SOCIALIZE_STANDING_GOOD = 1
SOCIALIZE_STANDING_SCRAP = -1
RACCOON_DAILY_SELLS = 5
RACCOON_DAILY_BUYS = 3
RACCOON_BUNDLES = {
    "scrap": {"name": "Scrap Bundle", "price": 14, "toys": ("bone", "feather")},
    "plume": {"name": "Plume Bundle", "price": 22, "toys": ("feather", "shell", "feather")},
    "gnaw": {"name": "Gnaw Bundle", "price": 18, "toys": ("bone", "stick", "acorn")},
}
RACCOON_PREY_KEYS = frozenset({"vole", "rabbit", "hare", "fish"})

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
CROSS_PACK_MATE_CATCH_CHANCE = 0.40
CROSS_PACK_MATE_CAUGHT_STANDING = -4
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
MEDIC_PUP_SCANDAL_STANDING = -5
RESTRICTED_HERB_MISUSE_STANDING = -4
RESTRICTED_HERB_HOARD_STANDING = -3
RESTRICTED_HERB_HOARD_CATCH_CHANCE = 0.38
RESTRICTED_HERB_MEDIC_ROUNDS_CATCH_CHANCE = 0.52
RESTRICTED_HERB_SNIFF_CATCH_CHANCE = 0.42
RESTRICTED_HERB_GROOM_CATCH_CHANCE = 0.32
RESTRICTED_HERB_HOARD_WARN = (
    "_Poison plants belong in the healers' den, not your personal bag. "
    "Turn in to a **Medic** or `/vitals action:denstore mode:deposit` before a patrol catches the scent._"
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
            "Swift Current - +2 to Dexterity checks involving swimming or crossing water."
        ),
    },
}

# Alternate hunt activities (bones ranges: min, max)
SCAVENGE_BONES = (2, 8)
TRACK_BONES = (8, 28)

# Sniff; wind-read once per sunrise (Wolvden-style)
SNIFF_HUNT_HINT_CHANCE = 0.22
SNIFF_HUNT_BONUS_PCT = 15
SNIFF_WOLF_ENCOUNTER_CHANCE = 0.15
SNIFF_WOLF_ENCOUNTER_MOOD = 4
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
CAT_PACT_GIFT_TRIBUTE = 15
CAT_PACT_GIFT_TRUST = 8
CAT_PACT_TRUST_HIGH = 70
CAT_PACT_TRUST_LOW = 35
CAT_PACT_VIOLATION_TRUST = -30
CAT_PACT_VIOLATION_UNITY = -4
CAT_PACT_VIOLATION_STANDING = -3
CAT_PACT_PATROL_TEMPLATES = frozenset({"clan_warrior", "clan_deputy"})
FISHING_BONES = (10, 22)

# Pack warfare
WAR_DURATION_DAYS = 2
NEUTRAL_CLAIM_SCORE = 12

# Pack unity (−5 to 10). At −5 the Great Pack fractures; all members become loners.
PACK_UNITY_MIN = -5
PACK_UNITY_MAX = 10
PACK_UNITY_DISSOLVE_THRESHOLD = -5

# Personal standing within the pack. At −5 the wolf is cast out as a loner.
WOLF_STANDING_MIN = -10
WOLF_STANDING_KICK_THRESHOLD = -5
DEFAULT_TERRITORIES = (
    ("pine_ridge", "Pine Ridge", 5),
    ("river_crossing", "River Crossing", 8),
    ("old_quarry", "Old Quarry", 6),
    ("mistwood", "Mistwood", 7),
    ("stoneroot", "Stoneroot", 10),
    ("deepfurrow", "Deep Furrow", 9),
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
        "Tend the wounded; use `/treat` with a herb or `/stabilize` a dying packmate.",
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
