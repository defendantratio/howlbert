"""Fix multiline function defs in care_handlers.py."""
from pathlib import Path
import re

text = Path("cogs/care_handlers.py").read_text(encoding="utf-8")
# Remove erroneous nested 'async def' + 'self,' patterns from bad extraction
text = re.sub(
    r"\n    async def (prepare_herb_inventory|treat|denstore|spirit_ritual|naming_ceremony|lay_to_rest)\(\n    self,?",
    lambda m: f"\nasync def {m.group(1)}(",
    text,
)
text = re.sub(r"\n    self,\n", "\n", text)
text = re.sub(r"async def (\w+)\( interaction", r"async def \1(interaction", text)
Path("cogs/care_handlers.py").write_text(text, encoding="utf-8")
print("fixed")
