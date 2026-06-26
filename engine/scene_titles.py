"""Thread title formatting for `/scene start`."""

from __future__ import annotations

DISCORD_THREAD_NAME_MAX = 100


def build_scene_thread_title(
    opener_name: str,
    *,
    partner_name: str | None = None,
    location: str | None = None,
    max_len: int = DISCORD_THREAD_NAME_MAX,
) -> str:
    """
  Build a thread name like ``Mirewort + Puddlebane — Greyspire ridge``.

  Location is omitted when unset; a solo scene is just the wolf name.
  """
    opener = (opener_name or "Scene").strip()
    partner = (partner_name or "").strip()
    loc = (location or "").strip()

    if partner and partner.lower() != opener.lower():
        cast = f"{opener} + {partner}"
    else:
        cast = opener

    if loc:
        title = f"{cast} — {loc}"
    else:
        title = cast

    if len(title) <= max_len:
        return title
    if loc and len(loc) + 3 < max_len:
        keep = max_len - len(loc) - 3
        return f"{cast[:keep].rstrip()} — {loc}"
    return title[: max_len - 1].rstrip() + "…"
