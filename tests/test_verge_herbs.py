"""Verge herb habitat tests; run: python -m tests.test_verge_herbs"""

from __future__ import annotations

from engine.herb_habitat import herbs_for_verge, is_wild_territory_herb
from herbs import HERBS

_pass = 0
_fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  OK  {name}")
    else:
        _fail += 1
        print(f" FAIL {name}" + (f" - {detail}" if detail else ""))


def main() -> None:
    roadside = set(herbs_for_verge("roadside"))
    compound = set(herbs_for_verge("compound"))
    check("purslane roadside", "purslane" in roadside)
    check("lavender compound only", "lavender" in compound and "lavender" not in roadside)
    check("plantain not wild territory", not is_wild_territory_herb(HERBS["plantain"]))
    check("comfrey still wild", is_wild_territory_herb(HERBS["comfrey"]))
    check("chicory roadside", "chicory" in roadside)
    check("garden mint compound", "garden_mint" in compound)
    overlap = roadside & compound
    check("some herbs on both verges", "dandelion" in overlap, str(overlap))

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
