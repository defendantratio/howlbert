"""Prayer before the hunt; once per rollover, +1 maw_favor, hunt roll bonus."""
from __future__ import annotations

import discord
import database as db
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed

_PRAY_FLAVOR: dict[str, str] = {
    "orthodox": (
        "You lower your muzzle, eyes half-closed. "
        "*The hunger moves through me. Let it be clean.* "
        "The Maw receives this."
    ),
    "orthodox_pragmatic": (
        "A quick dip of the head before the kill-ground. "
        "No ceremony needed; the Maw knows efficiency when it sees it."
    ),
    "zealot": (
        "You invoke each tooth by name. The illness of hunger sharpens into purpose. "
        "Your paws already know where to go."
    ),
    "doubter": (
        "You try it anyway. You feel something; maybe just the cold; "
        "but you say the words and mean them for a moment."
    ),
    "agnostic": (
        "You don't pray, exactly. You stand still and let the forest settle around you. "
        "If something is there, it knows."
    ),
    "atheist": (
        "You don't pray. But you breathe deliberately, count the wind, "
        "listen to what the pines carry. It sharpens you."
    ),
    "heretic": (
        "You speak quietly to the Maw as if it can hear every word; "
        "because you believe it can, and that it enjoys the watching."
    ),
}

_DEFAULT_FLAVOR = "You pause at the forest's edge. A breath before the blood."

HUNT_PRAYER_BONE_BONUS = 2


def try_hunt_prayer(discord_id: int, user, day: int) -> discord.Embed:
    """
    Attempt to pray before the hunt. Grants +1 maw_favor and a hunt bonus for the day.
    Returns an embed. Idempotent guard: once per world day.
    """
    def _get(key, default=None):
        return user[key] if hasattr(user, "keys") and key in user.keys() else default

    if _get("hunt_prayer_day", 0) == day:
        embed = howlbert_embed(
            "Already Prayed",
            "You have already offered this sunrise's prayer. The Maw heard you the first time.",
            color=ERROR_COLOR,
        )
        embed.set_footer(text="hunt prayer resets each sunrise")
        return embed

    if _get("condition") in ("dead", "dying"):
        embed = howlbert_embed(
            "Cannot Pray",
            "The Maw does not hear the prayers of the fallen.",
            color=ERROR_COLOR,
        )
        return embed

    belief = (_get("maw_belief") or "agnostic").lower()
    flavor = _PRAY_FLAVOR.get(belief, _DEFAULT_FLAVOR)

    new_favor = db.adjust_maw_favor(discord_id, 1)
    db.set_hunt_prayer_day(discord_id, day)

    embed = howlbert_embed("Hunt Prayer", flavor, color=SUCCESS_COLOR)
    embed.add_field(name="Maw Favor", value=f"+1 → {new_favor}", inline=True)
    embed.set_footer(
        text=f"blessed for today's hunts · +{HUNT_PRAYER_BONE_BONUS} bone roll active · resets at sunrise"
    )
    return embed
