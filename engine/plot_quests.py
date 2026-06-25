"""Book One quest availability by plot phase."""

from __future__ import annotations

# quest_key -> (min_phase, max_phase or None)
PLOT_QUEST_PHASES: dict[str, tuple[int, int | None]] = {
    "blink_border_patrol": (2, None),
    "blink_river_crisis": (4, None),
    "blink_healer_listen": (1, 5),
    "blink_wind_witness": (6, None),
    "blink_mill_scout": (8, None),
    "blink_ash_naming": (11, None),
    "blink_rogue_ledger": (6, None),
    "blink_healer_touch": (5, None),
}


def plot_quest_available(quest_key: str, guild_id: int | None) -> bool:
    if not quest_key.startswith("blink_"):
        return True
    if not guild_id:
        return False
    from engine.plot_blinking import plot_phase

    phase = plot_phase(guild_id)
    if phase <= 0:
        return False
    bounds = PLOT_QUEST_PHASES.get(quest_key)
    if not bounds:
        return True
    min_p, max_p = bounds
    if phase < min_p:
        return False
    if max_p is not None and phase > max_p:
        return False
    return True


def plot_sniff_quest_keys(guild_id: int) -> tuple[str, ...]:
    from engine.plot_blinking import plot_phase

    phase = plot_phase(guild_id)
    if phase <= 0:
        return ()
    keys: list[str] = []
    if 1 <= phase <= 5:
        keys.append("blink_healer_listen")
    if phase >= 6:
        keys.append("blink_wind_witness")
    return tuple(keys)
