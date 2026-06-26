"""Hunt/track/fish payout helpers; flavor tier vs canonical carcass value."""

from __future__ import annotations

from engine.hunt import hunt_flavor_for_prey
from engine.prey_items import canonical_prey_bones, prey_key_from_hunt_amount, prey_meta


def prey_key_for_payout(payout: int, user=None, *, season: str | None = None) -> str:
    """Map post-modifier bone payout to a carcass type."""
    if payout <= 0:
        return "vole"
    gp = None
    if user is not None:
        if hasattr(user, "keys") and "great_pack" in user.keys():
            gp = user["great_pack"]
        elif isinstance(user, dict):
            gp = user.get("great_pack")
    return prey_key_from_hunt_amount(payout, great_pack=gp, season=season)


def hunt_flavor_for_payout(payout: int, prey_key: str | None = None, user=None, *, season: str | None = None) -> str:
    key = prey_key or prey_key_for_payout(payout, user=user, season=season)
    return hunt_flavor_for_prey(key, payout)


def grant_prey_carcass_canonical(
    wolf_id: int,
    *,
    guild_id: int,
    day: int,
    prey_key: str,
) -> str:
    """Add prey to hoard using catalog bone value (not hunt roll). Returns display name."""
    from engine.prey_storage import grant_prey_from_hunt

    _, name = grant_prey_from_hunt(
        wolf_id,
        guild_id=guild_id,
        day=day,
        bone_value=canonical_prey_bones(prey_key),
        prey_key=prey_key,
    )
    return name
