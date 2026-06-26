"""Strip OOC markers from proxied IC text."""

from __future__ import annotations

import re

_OOC_PAREN = re.compile(r"\(\((.*?)\)\)", re.DOTALL)


def split_ooc(text: str) -> tuple[str, str | None]:
    """Return (ic_text, ooc_combined). Supports `((ooc))` and lines starting with `//`."""
    if not text:
        return "", None
    ooc_chunks: list[str] = []

    def _paren(m: re.Match) -> str:
        bit = (m.group(1) or "").strip()
        if bit:
            ooc_chunks.append(bit)
        return ""

    stripped = _OOC_PAREN.sub(_paren, text)
    ic_lines: list[str] = []
    for line in stripped.splitlines():
        s = line.strip()
        if s.startswith("//"):
            bit = s[2:].strip()
            if bit:
                ooc_chunks.append(bit)
        else:
            ic_lines.append(line)
    ic = "\n".join(ic_lines).strip()
    ooc = "; ".join(c for c in ooc_chunks if c) or None
    return ic, ooc
