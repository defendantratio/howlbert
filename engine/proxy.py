"""Tupperbox-style message proxying; parse tags, import exports, post via webhook."""

from __future__ import annotations

import json
import re

import discord

# Discord rejects webhook usernames containing these (case-insensitive) or >80 chars.
_BANNED_NAME_BITS = ("discord", "clyde")
_WEBHOOK_NAME = "Howlbert Proxy"


def parse_bracket_string(raw: str) -> tuple[str | None, str | None]:
    """Turn a single tag template like 'H:text' or '[text]' into (prefix, suffix)."""
    if not raw:
        return None, None
    raw = raw.strip()
    if "text" in raw:
        prefix, _, suffix = raw.partition("text")
        return (prefix or None), (suffix or None)
    # No placeholder; treat the whole thing as a prefix tag.
    return raw, None


def split_prefix_suffix(brackets) -> tuple[str | None, str | None]:
    """accept tupperbox 'brackets' ([prefix, suffix]) or a template string."""
    if isinstance(brackets, (list, tuple)):
        if len(brackets) >= 2:
            return (brackets[0] or None), (brackets[1] or None)
        if len(brackets) == 1:
            return parse_bracket_string(str(brackets[0]))
        return None, None
    if isinstance(brackets, str):
        return parse_bracket_string(brackets)
    return None, None


def sanitize_webhook_name(name: str) -> str:
    name = (name or "wolf").strip()
    lowered = name.lower()
    for bad in _BANNED_NAME_BITS:
        if bad in lowered:
            name = re.sub(re.escape(bad), "w" + bad[1:], name, flags=re.IGNORECASE)
            lowered = name.lower()
    name = name[:80].strip()
    return name or "wolf"


def parse_tupperbox_export(raw: str) -> list[dict]:
    """return a normalized list of proxies from a tupperbox or pluralkit export.

    each item: {name, avatar_url, prefix, suffix, bio, birthday}.
    """
    data = json.loads(raw)
    out: list[dict] = []

    # Tupperbox: {"tuppers": [...]}
    tuppers = data.get("tuppers") if isinstance(data, dict) else None
    if isinstance(tuppers, list):
        for t in tuppers:
            if not isinstance(t, dict):
                continue
            prefix, suffix = split_prefix_suffix(t.get("brackets"))
            out.append(
                {
                    "name": str(t.get("name") or "").strip(),
                    "avatar_url": (t.get("avatar_url") or None),
                    "prefix": prefix,
                    "suffix": suffix,
                    "bio": (t.get("description") or None),
                    "birthday": (t.get("birthday") or None),
                }
            )
        return [m for m in out if m["name"]]

    # PluralKit: {"members": [{"name", "avatar_url", "proxy_tags":[{"prefix","suffix"}], ...}]}
    members = data.get("members") if isinstance(data, dict) else None
    if isinstance(members, list):
        for m in members:
            if not isinstance(m, dict):
                continue
            tags = m.get("proxy_tags") or []
            prefix = suffix = None
            if tags and isinstance(tags[0], dict):
                prefix = tags[0].get("prefix") or None
                suffix = tags[0].get("suffix") or None
            out.append(
                {
                    "name": str(m.get("name") or "").strip(),
                    "avatar_url": (m.get("avatar_url") or None),
                    "prefix": prefix,
                    "suffix": suffix,
                    "bio": (m.get("description") or None),
                    "birthday": (m.get("birthday") or None),
                }
            )
        return [m for m in out if m["name"]]

    raise ValueError("unrecognized export; expected a tupperbox or pluralkit json file.")


async def get_proxy_webhook(channel: discord.TextChannel) -> discord.Webhook | None:
    """Find or create the reusable proxy webhook on a text channel."""
    try:
        hooks = await channel.webhooks()
    except (discord.Forbidden, discord.HTTPException):
        return None
    for hook in hooks:
        if hook.name == _WEBHOOK_NAME and hook.token:
            return hook
    try:
        return await channel.create_webhook(name=_WEBHOOK_NAME)
    except (discord.Forbidden, discord.HTTPException):
        return None
