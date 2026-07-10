"""Wolf RP lexicon; pack terminology, seasons, measurements, insults."""
from __future__ import annotations

from config import BOT_DISPLAY_NAME

# Internal season keys → wolf-season names (game still uses spring/summer/autumn/winter in DB)
SEASON_WOLF_NAMES: dict[str, tuple[str, str]] = {'spring': ('newgrowth', 'plants begin to sprout and prey returns.'), 'summer': ('highsun', 'long days; prey is plentiful.'), 'autumn': ('leaf-drop', 'leaves fall and temperatures cool.'), 'winter': ('leaf-bare', 'snow covers the ground; prey is scarce.')}

TIME_WOLF_NAMES: dict[str, tuple[str, str]] = {
    "dawn": ('sunrise', 'the sun climbs above the horizon; a new day in wolf time.'),
    "day": ('sunhigh', 'the sun at its peak, like noon.'),
    "dusk": ('half-light', 'between sunhigh and moonrise; the den stirs for evening.'),
    "night": ('moonhigh', 'the moon highest in the sky, around midnight.'),
}

# One game rollover = one sunrise

LEXICON_CATEGORIES: dict[str, list[tuple[str, str]]] = {
    "basic": [
        ('whitecough', 'glossary alias for **green-cough (mild)**; the first warriors cough stage (`cough:mild`).'),
        ('blooding', "a juvenile's first successful hunt kill (6 to 24 moons); unlocks `/role action:event` (+8 mood, +1 standing)."),
        ('drown-sick', 'mistmoor wolves who hear the belly-rip; fog whispers hit harder and spirit curses are more likely.'),
        ('starclan', 'ancestor spirits; `/world action:omen` reads their signs once per sunrise (advantage/disadvantage or vision).'),
        ('spirit curse', 'a maw-shadow mark from belly whispers; −1 on spiritual checks until cleansed with herbs or `/skills`.'),
        ('carrion', 'a dead carcass that has begun to rot. also an insult for a wolf with no strength or honor.'),
        ('scat', 'feces.'),
        ('fresh-kill', 'recently killed prey brought to the pack. hunters and yearlings hunt it; it goes in the **fresh-kill cache**. elders, pups, den-keepers, and sick wolves eat first, then hunters and yearlings. leftovers are buried or left for scavengers.'),
        ('hearth-hound', 'a domesticated dog living with twolegs; seen as soft and foolish by wild wolves.'),
        ('loner', 'a wolf who lives apart from any pack and holds no fixed territory.'),
        ('marking scat', 'defecating to scent-mark territory boundaries.'),
        ('monster', 'a car or similar vehicle, especially near twolegs or the thunderpath.'),
        ('rend', 'a violent fight between wolves, often over a kill or boundary.'),
        ('rogue', 'a hostile wolf without a permanent home; roams pack lands and respects no boundaries.'),
        ('sharing tongues', 'grooming while trading gossip; one wolf talks while the other grooms and listens.'),
        ('she-wolf / he-wolf', 'a female wolf / a male wolf.'),
        ('pup', 'a wolf cub.'),
        ('sun-sink-place', 'the ocean to the west where the sun sinks into the water.'),
        ('tree-gulper', 'a bulldozer; a roaring monster that devours trees and tears up earth.'),
        ('thunderpath', 'a paved road with an acrid smell that monsters often cross.'),
        ('twoleg', 'a human being.'),
        ('twoleg pup', 'a human child.'),
        ('twoleg den', 'a human house.'),
        ('twolegplace', 'a town, city, or village where twolegs live.'),
    ],
    "seasons": [
        ('newgrowth', 'spring; plants sprout, prey returns.'),
        ('highsun', 'summer; long days, plentiful prey.'),
        ('leaf-drop', 'autumn; leaves fall, air cools.'),
        ('leaf-bare', 'winter; snow, scarce prey.'),
        ('moon', 'time between one full moon and the next (~thirty sunrises).'),
        ('moonhigh', 'when the moon is highest; around midnight.'),
        ('moonrise', 'when the moon rises above the horizon.'),
        ('half-moon', 'two weeks; half a month.'),
        ('quarter-moon', 'one week.'),
        ('sunhigh', 'noon; sun at its peak.'),
        ('sunrise', 'one day in wolf time (e.g. “two sunrises ago”).'),
        ('season', 'one quarter of a year; four seasons make a full cycle.'),
    ],
    "measurements": [
        ('wolf-claw', '~1.5 in (3.8 cm); length of a claw.'),
        ('deer-length', '~6 to 8 ft (1.8 to 2.4 m); nose to tail of a deer.'),
        ('frog-length', '~2 to 4 in (5 to 10 cm).'),
        ('pupstep', "~2 to 3 in (5 to 7.5 cm); a pup's step."),
        ('hare-hop', "~18 to 24 in (45 to 60 cm); a hare's jump."),
        ('reed-length', 'up to ~5 ft (1.5 m).'),
        ('vole-length', '~3 to 5 in (7.5 to 12.5 cm).'),
        ('snout-length', "~4 to 6 in (10 to 15 cm); a wolf's muzzle."),
        ('pawstep', "~12 to 18 in (30 to 45 cm); a grown wolf's step."),
        ('tail-length', '~15 to 20 in (38 to 50 cm).'),
        ('tree-length', '~40 to 60 ft (12 to 18 m).'),
    ],
    "insults": [
        ('deerheart', 'coward; flees like a startled deer.'),
        ('carrion-breath', 'breath stinks of rotten meat; lazy or eats spoiled kills.'),
        ('frog-gut', 'weak, no stamina.'),
        ('vole-snout', 'noses into gossip and unimportant matters.'),
        ('pup-brain', 'foolish, acts like a helpless pup.'),
        ('coyote', 'traitorous or untrustworthy.'),
        ('scat-licker', 'disgusting, no pride or cleanliness.'),
        ('mud-paw', "clumsy; can't hunt silently."),
        ('hollow-fang', "talks big, can't back it up."),
        ('snake', 'sneaky; twists words.'),
        ('oak-head', "stupid; doesn't learn."),
    ],
}



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
    """one rollover = one sunrise."""
    if day_number == 1:
        return "1 sunrise"
    return f"{day_number} sunrises"


def build_terms_embed(category: str) -> tuple[str, str]:
    """return (title, description) for a lexicon category."""
    if category == "overview":
        lines = [
            f"**{BOT_DISPLAY_NAME}** uses **wolf tongue** for seasons, time, and den life.",
            "",
            "**quick map**",
            "• game seasons → newgrowth, highsun, leaf-drop, leaf-bare",
            "• one `/rollover` = **one sunrise** (one day)",
            "• `/food` = your personal carcass hoard · `/preypile` = laying out **fresh-kill** at the cache",
            "• lone wolves register as **loners** (not rogues)",
            "• juveniles earn **blooding** on first hunt kill",
            "• **starclan** omens: `/world action:omen` once per sunrise",
            "",
            "use `/terms topic:` for full lists; basic, seasons, measurements, insults.",
        ]
        return "wolf tongue", "\n".join(lines)

    entries = LEXICON_CATEGORIES.get(category)
    if not entries:
        entries = LEXICON_CATEGORIES["basic"]
        category = "basic"

    title = {
        "basic": "basic terms",
        "seasons": "seasons & time",
        "measurements": "measurements",
        "insults": "insults",
    }.get(category, "terms")

    lines = [f"**{term}**; {defn}" for term, defn in entries]
    return title, "\n".join(lines)

