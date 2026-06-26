"""Pack leadership checks; role only (no separate rank)."""

from config import GREAT_PACKS
from engine.apprentice_roles import matches_parent_role

PACK_OFFICER_ROLES = frozenset({"alpha", "advisor"})
BETA_ROLE = "advisor"  # Beta wolves use the Advisor role


def wolf_role_key(user) -> str:
    if not user:
        return "hunter"
    return user["wolf_role"] if "wolf_role" in user.keys() else "hunter"


def _pack_key(pack) -> str | None:
    if not pack:
        return None
    if "key" in pack.keys() and pack["key"]:
        return pack["key"]
    return None


def is_great_pack_row(pack) -> bool:
    key = _pack_key(pack)
    return bool(key and key in GREAT_PACKS)


def is_pack_alpha(user, pack) -> bool:
    """Pack leader: Alpha role in-pack; Great Packs use role, player packs use alpha_id seat."""
    if not user or not pack:
        return False
    if user["pack_id"] != pack["id"]:
        return False
    if wolf_role_key(user) != "alpha":
        return False
    if is_great_pack_row(pack):
        return True
    return pack["alpha_id"] == user["discord_id"]


def can_act_as_pack_alpha(user, pack, *, discord_admin: bool = False) -> bool:
    """Alpha commands (tax, territory, bulk den); server admins bypass."""
    if discord_admin:
        return True
    return is_pack_alpha(user, pack)


def can_run_pack_bulk_action(user, pack, *, discord_admin: bool = False) -> bool:
    """Alpha-led den commands (playall, feedall, drinkall); server admins bypass."""
    return can_act_as_pack_alpha(user, pack, discord_admin=discord_admin)


PACK_BULK_ALPHA_ONLY_MSG = (
    "Only the pack **Alpha** may lead pack-wide den commands "
    "(server **admins** may override)."
)


def is_pack_officer(user, pack) -> bool:
    """Alpha (pack leader) or Advisor in the same pack."""
    if not user or not pack or user["pack_id"] != pack["id"]:
        return False
    role = wolf_role_key(user)
    if role == "advisor":
        return True
    return is_pack_alpha(user, pack)


def can_act_as_pack_officer(user, pack, *, discord_admin: bool = False) -> bool:
    if discord_admin:
        return True
    return is_pack_officer(user, pack)


def is_pack_beta(user, pack) -> bool:
    """Second-in-command (Beta); Advisor role in the same pack."""
    if not user or not pack or user["pack_id"] != pack["id"]:
        return False
    return wolf_role_key(user) == BETA_ROLE


def can_forge_cat_pact(user, pack) -> bool:
    """Alpha or Diplomat (incl. apprentice) in the same pack."""
    if not user or not pack or user["pack_id"] != pack["id"]:
        return False
    if matches_parent_role(wolf_role_key(user), "diplomat"):
        return True
    return is_pack_alpha(user, pack)


def can_resolve_war(user, pack, *, discord_admin: bool = False) -> bool:
    """Alpha (pack leader) or Diplomat in a pack that is fighting the active war."""
    if discord_admin:
        return True
    if not user or not pack or user["pack_id"] != pack["id"]:
        return False
    if matches_parent_role(wolf_role_key(user), "diplomat"):
        return True
    return is_pack_alpha(user, pack)
