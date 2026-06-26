"""Wolf RP lexicon; pack terminology, seasons, measurements, insults."""

from __future__ import annotations

from config import BOT_DISPLAY_NAME

# Internal season keys → wolf-season names (game still uses spring/summer/autumn/winter in DB)
SEASON_WOLF_NAMES: dict[str, tuple[str, str]] = {
    "spring": ("Newgrowth", "Plants begin to sprout and prey returns."),
    "summer": ("Highsun", "Long days; prey is plentiful."),
    "autumn": ("Leaf-drop", "Leaves fall and temperatures cool."),
    "winter": ("Leaf-bare", "Snow covers the ground; prey is scarce."),
}

TIME_WOLF_NAMES: dict[str, tuple[str, str]] = {
    "dawn": ("Sunrise", "The sun climbs above the horizon; a new day in wolf time."),
    "day": ("Sunhigh", "The sun at its peak, like noon."),
    "dusk": ("Half-light", "Between sunhigh and moonrise; the den stirs for evening."),
    "night": ("Moonhigh", "The moon highest in the sky, around midnight."),
}

# One game rollover = one sunrise
SUNRISE_LABEL = "sunrise"
MOON_LABEL = "moon"  # ~30 sunrises between full moons

LEXICON_CATEGORIES: dict[str, list[tuple[str, str]]] = {
    "basic": [
        ("Whitecough", "Glossary alias for **Green-cough (Mild)**; the first Warriors cough stage (`cough:mild`)."),
        (
            "Blooding",
            "A juvenile's first successful hunt kill (6–24 moons); unlocks `/role action:event` (+8 mood, +1 standing).",
        ),
        (
            "Drown-Sick",
            "Mistmoor wolves who hear the Belly-Rip; fog whispers hit harder and spirit curses are more likely.",
        ),
        (
            "StarClan",
            "Ancestor spirits; `/world action:omen` reads their signs once per sunrise (advantage/disadvantage or vision).",
        ),
        (
            "Spirit curse",
            "A Maw-shadow mark from Belly whispers; −1 on spiritual checks until cleansed with herbs or `/skills`.",
        ),
        ("Carrion", "A dead carcass that has begun to rot. Also an insult for a wolf with no strength or honor."),
        ("Scat", "Feces."),
        (
            "Fresh-kill",
            "Recently killed prey brought to the pack. Hunters and yearlings hunt it; it goes in the "
            "**fresh-kill cache**. Elders, pups, den-keepers, and sick wolves eat first, then hunters and "
            "yearlings. Leftovers are buried or left for scavengers.",
        ),
        ("Hearth-hound", "A domesticated dog living with Twolegs; seen as soft and foolish by wild wolves."),
        ("Loner", "A wolf who lives apart from any pack and holds no fixed territory."),
        ("Marking scat", "Defecating to scent-mark territory boundaries."),
        ("Monster", "A car or similar vehicle, especially near Twolegs or the Thunderpath."),
        ("Rend", "A violent fight between wolves, often over a kill or boundary."),
        ("Rogue", "A hostile wolf without a permanent home; roams pack lands and respects no boundaries."),
        ("Sharing tongues", "Grooming while trading gossip; one wolf talks while the other grooms and listens."),
        ("She-wolf / He-wolf", "A female wolf / a male wolf."),
        ("Pup", "A wolf cub."),
        ("Sun-sink-place", "The ocean to the west where the sun sinks into the water."),
        ("Tree-gulper", "A bulldozer; a roaring monster that devours trees and tears up earth."),
        ("Thunderpath", "A paved road with an acrid smell that monsters often cross."),
        ("Twoleg", "A human being."),
        ("Twoleg pup", "A human child."),
        ("Twoleg den", "A human house."),
        ("Twolegplace", "A town, city, or village where Twolegs live."),
    ],
    "seasons": [
        ("Newgrowth", "Spring; plants sprout, prey returns."),
        ("Highsun", "Summer; long days, plentiful prey."),
        ("Leaf-drop", "Autumn; leaves fall, air cools."),
        ("Leaf-bare", "Winter; snow, scarce prey."),
        ("Moon", "Time between one full moon and the next (~thirty sunrises)."),
        ("Moonhigh", "When the moon is highest; around midnight."),
        ("Moonrise", "When the moon rises above the horizon."),
        ("Half-moon", "Two weeks; half a month."),
        ("Quarter-moon", "One week."),
        ("Sunhigh", "Noon; sun at its peak."),
        ("Sunrise", "One day in wolf time (e.g. “two sunrises ago”)."),
        ("Season", "One quarter of a year; four seasons make a full cycle."),
    ],
    "measurements": [
        ("Wolf-claw", "~1.5 in (3.8 cm); length of a claw."),
        ("Deer-length", "~6-8 ft (1.8-2.4 m); nose to tail of a deer."),
        ("Frog-length", "~2-4 in (5-10 cm)."),
        ("Pupstep", "~2-3 in (5-7.5 cm); a pup's step."),
        ("Hare-hop", "~18-24 in (45-60 cm); a hare's jump."),
        ("Reed-length", "Up to ~5 ft (1.5 m)."),
        ("Vole-length", "~3-5 in (7.5-12.5 cm)."),
        ("Snout-length", "~4-6 in (10-15 cm); a wolf's muzzle."),
        ("Pawstep", "~12-18 in (30-45 cm); a grown wolf's step."),
        ("Tail-length", "~15-20 in (38-50 cm)."),
        ("Tree-length", "~40-60 ft (12-18 m)."),
    ],
    "insults": [
        ("Deerheart", "Coward; flees like a startled deer."),
        ("Carrion-breath", "Breath stinks of rotten meat; lazy or eats spoiled kills."),
        ("Frog-gut", "Weak, no stamina."),
        ("Vole-snout", "Noses into gossip and unimportant matters."),
        ("Pup-brain", "Foolish, acts like a helpless pup."),
        ("Coyote", "Traitorous or untrustworthy."),
        ("Scat-licker", "Disgusting, no pride or cleanliness."),
        ("Mud-paw", "Clumsy; can't hunt silently."),
        ("Hollow-fang", "Talks big, can't back it up."),
        ("Snake", "Sneaky; twists words."),
        ("Oak-head", "Stupid; doesn't learn."),
    ],
}

INSULTS_FLAT = [term for term, _ in LEXICON_CATEGORIES["insults"]]


def season_display(season: str) -> str:
    name, _ = SEASON_WOLF_NAMES.get(season, (season.replace("_", " ").title(), ""))
    return name


def season_description(season: str) -> str:
    _, desc = SEASON_WOLF_NAMES.get(season, ("", ""))
    return desc


def time_display(time_of_day: str) -> str:
    name, _ = TIME_WOLF_NAMES.get(time_of_day, (time_of_day.replace("_", " ").title(), ""))
    return name


def time_description(time_of_day: str) -> str:
    _, desc = TIME_WOLF_NAMES.get(time_of_day, ("", ""))
    return desc


def format_sunrise(day_number: int) -> str:
    """One rollover = one sunrise."""
    if day_number == 1:
        return "1 sunrise"
    return f"{day_number} sunrises"


def build_terms_embed(category: str) -> tuple[str, str]:
    """Return (title, description) for a lexicon category."""
    if category == "overview":
        lines = [
            f"**{BOT_DISPLAY_NAME}** uses **wolf tongue** for seasons, time, and den life.",
            "",
            "**Quick map**",
            "• Game seasons → Newgrowth, Highsun, Leaf-drop, Leaf-bare",
            "• One `/rollover` = **one sunrise** (one day)",
            "• `/preypile` = laying out **fresh-kill** at the cache",
            "• Lone wolves register as **Loners** (not Rogues)",
            "• Juveniles earn **blooding** on first hunt kill",
            "• **StarClan** omens: `/world action:omen` once per sunrise",
            "",
            "Use `/terms topic:` for full lists; basic, seasons, measurements, insults.",
        ]
        return "Wolf Tongue", "\n".join(lines)

    entries = LEXICON_CATEGORIES.get(category)
    if not entries:
        entries = LEXICON_CATEGORIES["basic"]
        category = "basic"

    title = {
        "basic": "Basic Terms",
        "seasons": "Seasons & Time",
        "measurements": "Measurements",
        "insults": "Insults",
    }.get(category, "Terms")

    lines = [f"**{term}**; {defn}" for term, defn in entries]
    return title, "\n".join(lines)
