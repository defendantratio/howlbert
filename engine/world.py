import random



from config import SEASONS, TIMES_OF_DAY, WEATHER_TYPES

from engine.lexicon import season_description, season_display, time_description, time_display





def season_label(season: str) -> str:

    name = season_display(season)

    return f"{name} ({season})"





def time_label(time_of_day: str) -> str:

    return time_display(time_of_day)





def weather_label(weather: str) -> str:

    labels = {

        "storm": "Storm; wind like monsters on the Thunderpath",

        "thunderstorm": "Thunderstorm; monsters roaring along distant Thunderpaths",

        "fog": "Fog; scent swallowed within a pawstep",

        "snow": "Snow; Leaf-bare sky shedding white",

    }

    return labels.get(weather, weather.replace("_", " ").title())





def forecast_weather(current: str, count: int = 3) -> list[str]:

    pool = [w for w in WEATHER_TYPES if w != current]

    return random.sample(pool, min(count, len(pool)))





def season_blurb(season: str) -> str:

    desc = season_description(season)

    return desc or "Seasons turn slowly across the territory."





def time_blurb(time_of_day: str) -> str:

    desc = time_description(time_of_day)

    return desc or "The den stirs. Another stretch of the wild unfolds."

