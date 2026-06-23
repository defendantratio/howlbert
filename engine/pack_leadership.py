"""Pack leadership checks; role only (no separate rank)."""

PACK_OFFICER_ROLES = frozenset({"alpha", "advisor"})
BETA_ROLE = "advisor"  # Beta wolves use the Advisor role


def wolf_role_key(user) -> str:
    if not user:
        return "hunter"
    return user["wolf_role"] if "wolf_role" in user.keys() else "hunter"


def is_pack_alpha(user, pack) -> bool:
    """Pack leader: designated alpha_id and active wolf has the Alpha role."""
    if not user or not pack:
        return False
    if pack["alpha_id"] != user["discord_id"]:
        return False
    return wolf_role_key(user) == "alpha"


def is_pack_officer(user, pack) -> bool:
    """Alpha (pack leader) or Advisor in the same pack."""
    if not user or not pack or user["pack_id"] != pack["id"]:
        return False
    role = wolf_role_key(user)
    if role == "advisor":
        return True
    return is_pack_alpha(user, pack)


def is_pack_beta(user, pack) -> bool:
    """Second-in-command (Beta); Advisor role in the same pack."""
    if not user or not pack or user["pack_id"] != pack["id"]:
        return False
    return wolf_role_key(user) == BETA_ROLE


def can_forge_cat_pact(user, pack) -> bool:
    """Alpha or Diplomat in the same pack."""
    if not user or not pack or user["pack_id"] != pack["id"]:
        return False
    role = wolf_role_key(user)
    if role == "diplomat":
        return True
    return is_pack_alpha(user, pack)


def can_resolve_war(user, pack) -> bool:
    """Alpha (pack leader) or Diplomat in a pack that is fighting the active war."""
    if not user or not pack or user["pack_id"] != pack["id"]:
        return False
    if wolf_role_key(user) == "diplomat":
        return True
    return is_pack_alpha(user, pack)
