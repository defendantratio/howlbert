"""Find likely semicolon-used-as-minus bugs in Python code."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAT = re.compile(r"(?<![\"'])\b\w+\s*=\s*\w+\s*;\s*\w+")
SKIP = ("return ", "import ", "from ", '"""', "'''", "#")


def main() -> int:
    for root in ("engine", "utils", "cogs"):
        for path in (ROOT / root).rglob("*.py"):
            if ".venv" in path.parts:
                continue
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                s = line.strip()
                if any(s.startswith(x) for x in SKIP):
                    continue
                if PAT.search(line):
                    print(f"{path.relative_to(ROOT)}:{i}: {s[:120]}")
    db = ROOT / "database.py"
    for i, line in enumerate(db.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if any(s.startswith(x) for x in SKIP):
            continue
        if PAT.search(line):
            print(f"database.py:{i}: {s[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
