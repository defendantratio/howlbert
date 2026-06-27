import random
from datetime import datetime

from config import ROLLOVER_TIMEZONE, SEASONS, TIMES_OF_DAY, WEATHER_TYPES
from engine.lexicon import season_description, season_display, time_description, time_display


def season_label(season: str) -> str:
    name = season_display(season)
    return f"{name} ({season})"


def time_label(time_of_day: str) -> str:
    return time_display(time_of_day)


def weather_label(weather: str) -> str:
    labels = {
        "storm": "storm; wind like monsters on the thunderpath",
        "thunderstorm": "Thunderstorm; monsters roaring along distant Thunderpaths",
        "fog": "Fog; scent swallowed within a pawstep",
        "snow": "Snow; Leaf-bare sky shedding white",
    }
    return labels.get(weather, weather.replace("_", " ").title())


def weather_footer_label(weather: str) -> str:
    """short weather label for activity footers."""
    labels = {
        "clear": "Clear",
        "storm": "Storm",
        "thunderstorm": "Thunderstorm",
        "fog": "Fog",
        "snow": "Snow",
        "rain": "Rain",
        "overcast": "Overcast",
        "heat": "Heat",
        "thick_fog": "Thick fog",
    }
    return labels.get(weather, weather.replace("_", " ").title())


def clock_time_of_day(now: datetime | None = None) -> str:
    """Map real clock (rollover timezone) to dawn/day/dusk/night."""
    from engine.lunar import rollover_now

    if now is None:
        now = rollover_now(ROLLOVER_TIMEZONE)
    hour = now.hour
    if 5 <= hour < 9:
        return "dawn"
    if 9 <= hour < 17:
        return "day"
    if 17 <= hour < 22:
        return "dusk"
    return "night"


def effective_time_of_day(world) -> str:
    """live sky time for footers and time-gated activities (not stale rollover dawn)."""
    return clock_time_of_day()


def conditions_snippet(time_of_day: str, weather: str) -> str:
    """compact time + weather for embed footers (no markdown italics)."""
    return f"{time_display(time_of_day)} · {weather_footer_label(weather)}"


def forecast_weather(current: str, count: int = 3) -> list[str]:
    pool = [w for w in WEATHER_TYPES if w != current]
    return random.sample(pool, min(count, len(pool)))


def season_blurb(season: str) -> str:
    desc = season_description(season)
    return desc or "seasons turn slowly across the territory."


def time_blurb(time_of_day: str) -> str:
    desc = time_description(time_of_day)
    return desc or "the den stirs. another stretch of the wild unfolds."
