"""Slash reply visibility (ephemeral vs channel-visible)."""

from __future__ import annotations

from config import PUBLIC_GAMEPLAY_MESSAGES


def reply_ephemeral(*, private: bool = False) -> bool:
    """
    Whether a slash reply should be ephemeral (only the clicker sees it).

    When PUBLIC_GAMEPLAY_MESSAGES is enabled (default), all replies; including
    profiles, balances, and errors; post to the channel.
  """
    return not PUBLIC_GAMEPLAY_MESSAGES
