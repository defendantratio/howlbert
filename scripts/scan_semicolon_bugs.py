"""Find lines where '; ' likely replaced ' - ' in code."""
from __future__ import annotations

import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CODE_HINT = re.compile(
    r"(return |[=+\-*/%(,] |\bif |\belif |\bwhile |\bmax\(|\bmin\(|\babs\()"
)
SUSPECT = re.compile(r"[a-zA-Z0-9_\)\]]; [a-zA-Z0-9_\[\(]")


def main() -> None:
    hits: list[str] = []
    for p in list(ROOT.rglob("*.py")):
        if ".venv" in p.parts or "scan_semicolon" in p.name:
            continue
        text = p.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if not SUSPECT.search(line):
                continue
            if not CODE_HINT.search(line):
                continue
            if line.strip().startswith("#"):
                continue
            hits.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()[:120]}")
    for h in sorted(hits):
        print(h)
    print(f"TOTAL {len(hits)}")


if __name__ == "__main__":
    main()
