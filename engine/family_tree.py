"""Render a wolf's family / relationship web as a mermaid diagram image.

uses the public mermaid.ink render service (no local image dependencies). the
diagram source is packed exactly like the mermaid live editor (`pako:` state)
so the get url returns a png that discord can embed.
"""

from __future__ import annotations

import base64
import json
import zlib

import database as db

_max_children = 8


def _safe_label(name: str | None) -> str:
    if not name:
        return "unknown"
    # mermaid labels are wrapped in quotes; neutralize quotes/newlines.
    return name.replace('"', "'").replace("\n", " ").strip()[:32] or "unknown"


def build_family_mermaid(wolf) -> tuple[str, int]:
    """Return (mermaid_source, relationship_count) for a wolf's family web."""
    lines = ["graph td"]
    rel = 0
    node_ids: dict[int, str] = {}
    counter = 0

    def node(wolf_id: int | None, name: str | None, *, focus: bool = False) -> str | None:
        nonlocal counter
        if not wolf_id and not name:
            return None
        key = wolf_id if wolf_id else -(counter + 1)
        if key in node_ids:
            return node_ids[key]
        nid = f"n{counter}"
        counter += 1
        node_ids[key] = nid
        label = _safe_label(name)
        if focus:
            lines.append(f'{nid}["★ {label}"]:::focus')
        else:
            lines.append(f'{nid}["{label}"]')
        return nid

    def name_of(wolf_id) -> str | None:
        return db.wolf_display_name(wolf_id) if wolf_id else None

    focus_id = node(wolf["id"], wolf["wolf_name"], focus=True)

    def col(key):
        return wolf[key] if key in wolf.keys() else None

    # Biological parents (solid), adoptive parents (dashed).
    for pkey in ("bio_parent_1_id", "bio_parent_2_id"):
        pid = col(pkey)
        if pid:
            pn = node(pid, name_of(pid))
            if pn:
                lines.append(f"{pn} --> {focus_id}")
                rel += 1
    for pkey in ("adopt_parent_1_id", "adopt_parent_2_id"):
        pid = col(pkey)
        if pid:
            pn = node(pid, name_of(pid))
            if pn:
                lines.append(f"{pn} -.adopted.-> {focus_id}")
                rel += 1

    # Mate.
    mate_id = col("bonded_mate_id") or col("mate_id")
    if mate_id:
        mn = node(mate_id, name_of(mate_id))
        if mn:
            lines.append(f"{focus_id} ---|mate| {mn}")
            rel += 1

    # Offspring.
    children = db.get_lineage_children_for_wolf(wolf["id"], limit=_MAX_CHILDREN)
    for child in children:
        cn = node(child["id"], child["wolf_name"])
        if cn:
            lines.append(f"{focus_id} --> {cn}")
            rel += 1

    lines.append("classdef focus fill:#5b3a86,stroke:#d9c2ff,color:#fff,stroke-width:2px;")
    return "\n".join(lines), rel


def mermaid_image_url(code: str, *, theme: str = "dark") -> str:
    """pack mermaid source into a mermaid.ink png url (live-editor `pako:` format)."""
    state = {
        "code": code,
        "mermaid": json.dumps({"theme": theme}),
        "autoSync": True,
        "updateDiagram": True,
    }
    raw = json.dumps(state).encode("utf-8")
    compressed = zlib.compress(raw, 9)
    packed = base64.urlsafe_b64encode(compressed).decode("ascii")
    return f"https://mermaid.ink/img/pako:{packed}?type=png"


def family_tree_image_url(wolf) -> tuple[str | None, int]:
    """Build the family-tree image URL for a wolf; (url, relationship_count)."""
    code, rel = build_family_mermaid(wolf)
    if rel == 0:
        return None, 0
    return mermaid_image_url(code), rel
