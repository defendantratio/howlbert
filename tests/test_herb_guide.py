"""Herb guide tests; run: python -m tests.test_herb_guide"""

from __future__ import annotations

from engine.herb_guide import _usage_hint, build_herb_guide_embed, list_herb_keys, total_pages
from engine.herb_habitat import herbs_for_verge
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
    keys = list_herb_keys("all")
    check("herb list non-empty", len(keys) > 80, str(len(keys)))
    check("pages for all", total_pages("all") > 15, str(total_pages("all")))
    roadside = list_herb_keys("roadside")
    check("roadside filter", "chicory" in roadside and "comfrey" not in roadside)
    check("new mallow roadside", "common_mallow" in herbs_for_verge("roadside"))

    title, body = build_herb_guide_embed(page=0)
    check("overview page", "gathering" in body and title.lower().startswith("herb guide"))
    title2, body2 = build_herb_guide_embed(page=1, filter_key="roadside")
    check("content page", "herb_" in body2 or "Herb Guide" in title2)

    for key in keys:
        hint = _usage_hint(key, HERBS[key])
        check(
            f"mechanical hint {key}",
            "Flavor effect" not in hint
            and "Cures listed ailments" not in hint
            and "Special effect on" not in hint,
            hint[:80],
        )
    check("bindweed splint text", "7 days" in _usage_hint("bindweed", HERBS["bindweed"]))
    check("beech ward text", "infection ward" in _usage_hint("beech_leaves", HERBS["beech_leaves"]).lower())

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
