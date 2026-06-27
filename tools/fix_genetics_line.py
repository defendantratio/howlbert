"""One-off: decode corrupted genetics.py line 259."""
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "engine" / "genetics.py"
text = p.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)
bad = lines[258]
marker = "# Birth / register genetics that herbs must never remove"
idx = bad.find(marker)
if idx < 0:
    raise SystemExit(f"marker not found in line 259: {bad[:120]!r}")
head = bad[: idx + len(marker) + len(" (splints don't regrow limbs).")]
rest = bad[idx + len(head) :]
if rest.startswith("\\n"):
    rest = rest.replace("\\n", "\n")
fixed = head + "\n" + rest
if not fixed.endswith("\n"):
    fixed += "\n"
lines[258:] = [fixed]
p.write_text("".join(lines), encoding="utf-8")
print("fixed", p, "lines:", len(p.read_text().splitlines()))
