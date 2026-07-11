"""In-character obituary lines; a wolf's death, plus one real highlight from
their journal, formatted for a den announcement (and easy to screenshot for
social media — see docs/GROWTH_IDEAS.md section 41)."""

from __future__ import annotations

import database as db

# journal event keys worth surfacing as a wolf's "one highlight"; roughly in
# order of how memorable they read out of context. "died" itself is excluded
# since the obituary already states the cause separately.
_HIGHLIGHT_PRIORITY = (
    "achievement",
    "raid_success",
    "quest_complete",
    "rivalry_milestone",
    "blooded",
    "trained",
    "bonded",
    "pack_change",
    "cast_out",
    "born",
    "registered",
)


def _pick_highlight(wolf_id: int) -> str | None:
    entries = db.list_wolf_journal(wolf_id, limit=200)
    by_key: dict[str, str] = {}
    for row in entries:
        key = str(row["event_key"])
        if key not in by_key:
            by_key[key] = str(row["summary"])
    for key in _HIGHLIGHT_PRIORITY:
        if key in by_key:
            return by_key[key]
    return None


def format_obituary_line(wolf_id: int, wolf_name: str, cause: str) -> str:
    """A single den-news line: cause of death plus one real highlight from the
    wolf's own journal, if one exists. Falls back to a plain line if the
    wolf's journal has nothing else worth surfacing (a very young death)."""
    highlight = _pick_highlight(wolf_id)
    if highlight:
        return f"**{wolf_name}**; died of {cause}. remembered: {highlight}"
    return f"**{wolf_name}**; died of {cause}."
