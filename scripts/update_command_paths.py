"""Update command path strings after vitals/herbs/medic reorganization."""
from pathlib import Path

REPLACEMENTS = [
    ("/vitals action:denstore", "/herbs action:store"),
    ("/vitals action:herbbag", "/herbs action:bag"),
    ("/vitals action:herbs", "/herbs action:guide"),
    ("/vitals action:prepare", "/herbs action:prepare"),
    ("/vitals action:dryall", "/herbs action:dryall"),
    ("/vitals action:turnin", "/herbs action:turnin"),
    ("/vitals action:treat", "/medic action:treat"),
    ("/vitals action:sacred", "/medic action:sacred"),
    ("/vitals action:ritual", "/medic action:ritual"),
    ("/vitals action:naming", "/medic action:naming"),
    ("/vitals action:lay_to_rest", "/medic action:lay_to_rest"),
    ("/vitals action:swim", "/medic action:swim"),
    ("`/quarantine`", "`/medic action:quarantine`"),
    ("/quarantine;", "/medic action:quarantine;"),
]

root = Path(".")
count = 0
for path in list(root.rglob("*.py")) + list(root.rglob("*.md")):
    if "scripts" in path.parts or ".git" in path.parts:
        continue
    text = path.read_text(encoding="utf-8")
    orig = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        count += 1
        print(path)

print(f"updated {count} files")
