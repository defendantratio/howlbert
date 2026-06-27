"""Grow-your-own herbs: seeds, planting, tending, and harvest.

Growing profiles are scaled from real horticultural data (light, water, days to
germinate/mature, frost tolerance) onto Howlbert's 6-sunrise seasons. Sources:
medicinal-herb growing guides for yarrow, calendula, chamomile, comfrey,
marshmallow, mint, sage, thyme, and stinging nettle.

The module is pure logic (no DB/Discord) so it can be unit-tested directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from config import SEASONS
from herbs import HERBS

# Light needs
FULL_SUN = "full_sun"
PARTIAL = "partial"
SHADE = "shade"

# Water needs
LOW = "low"      # drought-tolerant; rots if fussed over
MEDIUM = "medium"
HIGH = "high"    # must stay moist or it wilts fast

LIGHT_LABELS = {FULL_SUN: "full sun", PARTIAL: "partial shade", SHADE: "shade"}
WATER_LABELS = {LOW: "dry / well-drained", MEDIUM: "moderate", HIGH: "moist soil"}

# Herbs that are tree bark, nuts, fungus, cobwebs, sticks, or honey; gathered in
# the wild, not sown in a den garden.
NON_CULTIVABLE = frozenset(
    {
        "stick", "cobwebs", "honey", "oak_bark", "pine_bark", "pine_needle",
        "alder_bark", "slippery_elm", "wild_cherry_bark", "mountain_ash",
        "beech_leaves", "cobnuts", "holly_berries", "juniper_berry",
        "belly_rip_fungus", "willow_bark",
    }
)


@dataclass(frozen=True)
class GrowProfile:
    light: str
    water: str
    seasons: tuple[str, ...]   # best sowing seasons
    grow_days: int             # sunrises from sowing to harvest
    yield_min: int
    yield_max: int
    hardy: bool                # tolerates frost / winter growth


def _p(light, water, seasons, grow_days, yield_min=1, yield_max=2, hardy=False):
    return GrowProfile(light, water, tuple(seasons), grow_days, yield_min, yield_max, hardy)


_DEFAULT = _p(PARTIAL, MEDIUM, ("spring",), 4)

# Research-based profiles. grow_days scaled to the 6-day season cycle.
HERB_GROWING: dict[str, GrowProfile] = {
    # Mediterranean / dry, full-sun perennials
    "yarrow": _p(FULL_SUN, LOW, ("spring", "summer"), 6, 2, 3, hardy=True),
    "sage": _p(FULL_SUN, LOW, ("spring", "summer"), 5, 1, 2, hardy=True),
    "thyme": _p(FULL_SUN, LOW, ("spring", "summer"), 5, 1, 2, hardy=True),
    "rosemary": _p(FULL_SUN, LOW, ("spring", "summer"), 5, 1, 2, hardy=True),
    "lavender": _p(FULL_SUN, LOW, ("spring", "summer"), 5, 1, 2, hardy=True),
    "heather": _p(FULL_SUN, LOW, ("spring", "autumn"), 5, 1, 2, hardy=True),
    "feverfew": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 4, 1, 2),
    "tansy": _p(FULL_SUN, LOW, ("spring", "summer"), 3, 1, 2, hardy=True),
    "mugwort": _p(FULL_SUN, LOW, ("spring", "summer"), 3, 1, 2, hardy=True),
    "wild_garlic": _p(PARTIAL, MEDIUM, ("spring", "autumn"), 4, 1, 2, hardy=True),
    "purslane": _p(FULL_SUN, LOW, ("summer",), 2, 1, 3),
    "douglas_sagewort": _p(FULL_SUN, LOW, ("spring", "summer"), 3, 1, 2, hardy=True),

    # Full-sun, moderate-water annuals & flowers
    "chamomile": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 4, 2, 3),
    "borage": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 3, 2, 3),
    "fennel": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 4, 1, 2),
    "parsley": _p(FULL_SUN, MEDIUM, ("spring", "autumn"), 3, 2, 3),
    "chervil": _p(PARTIAL, MEDIUM, ("spring", "autumn"), 3, 2, 3),
    "daisy": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 3, 2, 3),
    "coneflower": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 5, 1, 2, hardy=True),
    "goldenrod": _p(FULL_SUN, MEDIUM, ("summer", "autumn"), 4, 1, 2, hardy=True),
    "sorrel": _p(FULL_SUN, MEDIUM, ("spring", "autumn"), 3, 2, 3, hardy=True),
    "chicory": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 3, 1, 2, hardy=True),
    "raspberry_leaves": _p(FULL_SUN, MEDIUM, ("spring",), 5, 1, 2, hardy=True),
    "catmint": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 3, 2, 3, hardy=True),
    "saffron": _p(FULL_SUN, LOW, ("autumn",), 5, 1, 1),
    "edelweiss": _p(FULL_SUN, LOW, ("spring", "summer"), 5, 1, 1, hardy=True),
    "elderberry": _p(FULL_SUN, MEDIUM, ("spring",), 6, 1, 2, hardy=True),
    "elder": _p(FULL_SUN, MEDIUM, ("spring",), 6, 1, 2, hardy=True),
    "coltsfoot": _p(FULL_SUN, MEDIUM, ("spring",), 3, 1, 2, hardy=True),
    "knotgrass": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 2, 2, 3),
    "ragweed": _p(FULL_SUN, MEDIUM, ("summer",), 2, 1, 2),
    "ragwort": _p(FULL_SUN, MEDIUM, ("summer",), 2, 1, 2),
    "wintergreen": _p(PARTIAL, MEDIUM, ("spring",), 5, 1, 2, hardy=True),
    "prickly_ash": _p(FULL_SUN, MEDIUM, ("spring",), 5, 1, 2, hardy=True),
    "burnet": _p(FULL_SUN, LOW, ("spring", "summer"), 3, 1, 2, hardy=True),
    "tormentil": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 3, 1, 2, hardy=True),
    "sticklewort": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 3, 1, 2, hardy=True),
    "lambs_ear": _p(FULL_SUN, LOW, ("spring", "summer"), 4, 1, 2, hardy=True),
    "labrador_tea": _p(PARTIAL, HIGH, ("spring",), 5, 1, 2, hardy=True),
    "passionflower": _p(FULL_SUN, MEDIUM, ("summer",), 5, 1, 2),
    "meadowsweet": _p(PARTIAL, HIGH, ("spring", "summer"), 4, 1, 2, hardy=True),

    # Fast self-seeding "weeds"
    "dandelion": _p(FULL_SUN, MEDIUM, ("spring", "summer", "autumn"), 2, 2, 3, hardy=True),
    "plantain": _p(FULL_SUN, MEDIUM, ("spring", "summer", "autumn"), 2, 2, 3, hardy=True),
    "chickweed": _p(PARTIAL, MEDIUM, ("spring", "autumn"), 2, 2, 3, hardy=True),
    "catchweed": _p(PARTIAL, MEDIUM, ("spring",), 2, 2, 3),

    # Moisture-loving / shade herbs
    "comfrey": _p(PARTIAL, HIGH, ("spring", "summer"), 6, 2, 3, hardy=True),
    "marsh_mallow": _p(PARTIAL, HIGH, ("spring",), 6, 1, 2, hardy=True),
    "stinging_nettle": _p(SHADE, HIGH, ("spring",), 3, 2, 3, hardy=True),
    "watermint": _p(PARTIAL, HIGH, ("spring", "summer"), 2, 2, 3, hardy=True),
    "garden_mint": _p(PARTIAL, HIGH, ("spring", "summer"), 2, 2, 3, hardy=True),
    "sweet_sedge": _p(PARTIAL, HIGH, ("spring", "summer"), 4, 1, 2, hardy=True),
    "cattail": _p(FULL_SUN, HIGH, ("spring", "summer"), 4, 1, 2, hardy=True),
    "rush_stalks": _p(FULL_SUN, HIGH, ("spring", "summer"), 3, 1, 2, hardy=True),
    "swamp_milkweed": _p(FULL_SUN, HIGH, ("spring", "summer"), 5, 1, 2, hardy=True),
    "skunk_cabbage": _p(SHADE, HIGH, ("spring",), 5, 1, 2, hardy=True),
    "lizards_tail": _p(PARTIAL, HIGH, ("spring", "summer"), 4, 1, 2, hardy=True),
    "purple_loosestrife": _p(FULL_SUN, HIGH, ("summer",), 4, 1, 2, hardy=True),
    "lungwort": _p(SHADE, HIGH, ("spring",), 4, 1, 2, hardy=True),
    "valerian": _p(PARTIAL, MEDIUM, ("spring", "summer"), 5, 1, 2, hardy=True),
    "jewelweed": _p(PARTIAL, HIGH, ("spring", "summer"), 3, 2, 3),
    "mullein": _p(FULL_SUN, LOW, ("spring", "summer"), 5, 1, 2, hardy=True),
    "horsetail": _p(PARTIAL, HIGH, ("spring", "summer"), 3, 1, 2, hardy=True),
    "boneset": _p(FULL_SUN, HIGH, ("summer",), 4, 1, 2, hardy=True),
    "blackberry": _p(FULL_SUN, MEDIUM, ("spring",), 5, 1, 2, hardy=True),
    "bindweed": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 2, 2, 3, hardy=True),
    "ivy_vines": _p(SHADE, MEDIUM, ("spring",), 4, 1, 2, hardy=True),
    "broom": _p(FULL_SUN, LOW, ("spring", "summer"), 5, 1, 2, hardy=True),
    "celandine": _p(PARTIAL, MEDIUM, ("spring",), 3, 1, 2, hardy=True),
    "adders_tongue": _p(SHADE, HIGH, ("spring",), 4, 1, 2, hardy=True),
    "snakeroot": _p(PARTIAL, MEDIUM, ("spring", "summer"), 4, 1, 2, hardy=True),
    "burdock_root": _p(FULL_SUN, MEDIUM, ("spring",), 6, 1, 2, hardy=True),
    "dock": _p(FULL_SUN, MEDIUM, ("spring", "summer"), 3, 2, 3, hardy=True),
    "poppy_seeds": _p(FULL_SUN, MEDIUM, ("spring",), 4, 1, 2),
}


def can_cultivate(herb_key: str) -> bool:
    """True if the herb can be sown in a den garden."""
    if herb_key in NON_CULTIVABLE:
        return False
    meta = HERBS.get(herb_key)
    if not meta:
        return False
    if meta.get("poison"):
        return False
    if meta.get("rarity") == "restricted":
        return False
    return True


def growing_profile(herb_key: str) -> GrowProfile:
    return HERB_GROWING.get(herb_key, _DEFAULT)


def cultivable_herbs() -> list[str]:
    return sorted(k for k in HERBS if can_cultivate(k))


def season_is_suitable(profile: GrowProfile, season: str) -> bool:
    if season in profile.seasons:
        return True
    # Hardy plants can be kept alive (slowly) outside their best season.
    return profile.hardy and season != "winter"


def effective_grow_days(profile: GrowProfile, season: str) -> int:
    """off-season sowings mature more slowly."""
    if season in profile.seasons:
        return profile.grow_days
    if profile.hardy:
        return profile.grow_days + (profile.grow_days + 1) // 2  # ~1.5x
    return profile.grow_days * 2


def watering_overdue_penalty(profile: GrowProfile, dry_days: int) -> int:
    """health lost from going `dry_days` sunrises without tending."""
    if dry_days <= 0:
        return 0
    if profile.water == HIGH:
        return 30 * dry_days
    if profile.water == MEDIUM:
        return 15 * max(0, dry_days - 1)
    return 0  # drought-tolerant


@dataclass
class GrowResult:
    stage: str          # seed | sprout | growing | mature | wilted | dead
    progress_pct: int
    health: int
    ready: bool
    dead: bool
    note: str


def evaluate_growth(
    *,
    herb_key: str,
    planted_day: int,
    last_tended_day: int,
    last_eval_day: int,
    health: int,
    season: str,
    current_day: int,
) -> tuple[GrowResult, dict]:
    """Pure growth tick.

    Returns the display result plus a dict of column updates to persist
    (``health``, ``last_eval_day``, ``dead``).
    """
    profile = growing_profile(herb_key)
    updates: dict = {}
    new_health = int(health)
    days_passed = current_day - last_eval_day

    if days_passed > 0 and new_health > 0:
        dry_days = max(0, current_day - last_tended_day)
        new_health -= watering_overdue_penalty(profile, dry_days)
        if season == "winter" and not profile.hardy:
            new_health -= 40 * days_passed
        new_health = max(0, min(100, new_health))
        updates["health"] = new_health
        updates["last_eval_day"] = current_day

    dead = new_health <= 0
    if dead:
        updates["dead"] = 1
        return (
            GrowResult("dead", 0, 0, False, True, _wilt_reason(profile, season)),
            updates,
        )

    eff = effective_grow_days(profile, season)
    elapsed = max(0, current_day - planted_day)
    progress = min(100, int(round(elapsed / eff * 100))) if eff > 0 else 100
    ready = elapsed >= eff

    if ready:
        stage = "mature"
    elif progress >= 60:
        stage = "growing"
    elif progress >= 25:
        stage = "sprout"
    else:
        stage = "seed"
    if new_health < 50 and not ready:
        stage = "wilted"

    note = _grow_note(profile, season, new_health, ready)
    return (
        GrowResult(stage, progress, new_health, ready, False, note),
        updates,
    )


def _wilt_reason(profile: GrowProfile, season: str) -> str:
    if season == "winter" and not profile.hardy:
        return "frost killed this tender planting."
    if profile.water == HIGH:
        return "dried out; this herb needs constant moisture."
    return "neglected too long and withered."


def _grow_note(profile: GrowProfile, season: str, health: int, ready: bool) -> str:
    if ready:
        return "ready to harvest."
    bits = []
    if season not in profile.seasons:
        if profile.hardy:
            bits.append("off-season; growing slowly")
        else:
            bits.append("wrong season; struggling")
    if profile.water == HIGH:
        bits.append("water every sunrise")
    elif profile.water == MEDIUM:
        bits.append("water often")
    else:
        bits.append("drought-hardy")
    if health < 50:
        bits.append("wilting; tend it")
    return "; ".join(bits).capitalize()


def harvest_yield(profile: GrowProfile, health: int, *, rng=None) -> int:
    """number of fresh herb stacks from a mature plant, scaled by health."""
    import random

    rng = rng or random
    base = rng.randint(profile.yield_min, profile.yield_max)
    if health >= 90:
        base += 1
    elif health < 50:
        base = max(1, base - 1)
    return max(1, base)


def growing_blurb(herb_key: str) -> str:
    """one-line growing summary for the guide/seed list."""
    p = growing_profile(herb_key)
    seasons = "/".join(s[:3] for s in p.seasons)
    hardy = " · frost-hardy" if p.hardy else ""
    return (
        f"{LIGHT_LABELS[p.light]} · {WATER_LABELS[p.water]} · "
        f"sow {seasons} · ~{p.grow_days} sunrises{hardy}"
    )
