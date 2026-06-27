import re
import pathlib

from engine.character_lore import parse_character_lore
from engine.character_lore_data import CHARACTER_LORE_BY_NAME

docs: dict[str, str] = {}
for path in pathlib.Path("docs/characters").glob("*.md"):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\*\*Gender/Pronouns:\*\*\s*(.+)", text)
    if match:
        docs[path.stem] = match.group(1).strip()

she_pat = re.compile(r"\b[Ss]he\b|\b[Hh]er\b|\b[Hh]ers\b")
he_pat = re.compile(r"\b[Hh]e\b|\b[Hh]is\b|\b[Hh]im\b")
they_pat = re.compile(r"\b[Tt]hey\b|\b[Tt]heir\b|\b[Tt]hem\b")


def score(text: str) -> tuple[int, int, int]:
    if not text:
        return 0, 0, 0
    return (
        len(she_pat.findall(text)),
        len(he_pat.findall(text)),
        len(they_pat.findall(text)),
    )


def infer_pronouns(s: int, h: int, t: int) -> str | None:
    if max(s, h, t) == 0:
        return None
    if s > h and s >= t:
        return "she/her"
    if h > s and h >= t:
        return "he/him"
    if t >= s and t >= h:
        return "they/them"
    return None


def doc_pronouns(line: str | None) -> str | None:
    if not line:
        return None
    low = line.lower()
    if "she/her" in low or "she-wolf" in low:
        return "she/her"
    if "he/him" in low or low.startswith("male"):
        return "he/him"
    if "they/them" in low:
        return "they/them"
    return None


print("name\tlore\tshe\the\tthey\tdoc\tflag")
for name, raw in sorted(CHARACTER_LORE_BY_NAME.items(), key=lambda x: x[0].lower()):
    lore = parse_character_lore(raw) or {}
    blob = " ".join(lore.get(key, "") for key in ("personality", "backstory", "rp_sample", "family_ties"))
    s, h, t = score(blob)
    inferred = infer_pronouns(s, h, t)
    documented = doc_pronouns(docs.get(name))
    flag = ""
    if inferred and documented and inferred != documented:
        flag = "MISMATCH"
    print(
        f"{name}\t{inferred or '?'}\t{s}\t{h}\t{t}\t{documented or '-'}\t{flag}"
    )

print(f"\n{len(CHARACTER_LORE_BY_NAME)} lore sheets; {len(docs)} character docs with pronouns")
