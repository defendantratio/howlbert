"""Tests for herb preparation autocomplete, form-suffix parsing, and Row-safe field access."""

from __future__ import annotations

import sqlite3

from utils.herb_autocomplete import _split_herb_form


# ---- _split_herb_form ----

def test_split_raw_herb():
    assert _split_herb_form("herb_yarrow") == ("yarrow", None)


def test_split_poultice():
    assert _split_herb_form("herb_arnica_poultice") == ("arnica", "poultice")


def test_split_simmered_milk():
    # simmered_milk contains an underscore — must not be shadowed by shorter suffixes
    assert _split_herb_form("herb_adders_tongue_simmered_milk") == ("adders_tongue", "simmered_milk")


def test_split_multiword_herb_poultice():
    assert _split_herb_form("herb_belly_rip_fungus_poultice") == ("belly_rip_fungus", "poultice")


def test_split_dried():
    # yarrow is in HERBS; herb_yarrow_dried is a valid prepared-herb item key
    assert _split_herb_form("herb_yarrow_dried") == ("yarrow", "dried")


def test_split_non_herb_key():
    # stick and other non-herb keys should pass through unchanged
    assert _split_herb_form("stick") == ("stick", None)


def test_split_tea_suffix_not_shadowed_by_labrador_tea():
    # "herb_labrador_tea" with no form suffix → raw herb named labrador_tea
    assert _split_herb_form("herb_labrador_tea") == ("labrador_tea", None)


# ---- _derive_prep_methods ----

def test_knotgrass_has_explicit_prep_methods():
    from herbs import HERBS
    from engine.herb_guide import _derive_prep_methods
    methods = _derive_prep_methods("knotgrass", HERBS["knotgrass"])
    assert "poultice" in methods
    assert "tea" in methods


def test_arnica_is_poultice_only():
    from herbs import HERBS
    from engine.herb_guide import _derive_prep_methods
    methods = _derive_prep_methods("arnica", HERBS["arnica"])
    assert methods == ["poultice"]


def test_comfrey_includes_poultice_and_chewed():
    from herbs import HERBS
    from engine.herb_guide import _derive_prep_methods
    methods = _derive_prep_methods("comfrey", HERBS["comfrey"])
    assert "poultice" in methods
    assert "chewed" in methods


def test_labrador_tea_is_decoction():
    from herbs import HERBS
    from engine.herb_guide import _derive_prep_methods
    methods = _derive_prep_methods("labrador_tea", HERBS["labrador_tea"])
    assert methods == ["decoction"]


# ---- herb_admin DEFAULT_METHOD_REQS ----

def test_default_method_reqs_importable():
    from engine.herb_admin import DEFAULT_METHOD_REQS
    assert isinstance(DEFAULT_METHOD_REQS, dict)


def test_default_method_reqs_respiratory():
    from engine.herb_admin import DEFAULT_METHOD_REQS
    assert DEFAULT_METHOD_REQS["cough"] == "tea"
    assert DEFAULT_METHOD_REQS["leafbare_cough"] == "tea"
    assert DEFAULT_METHOD_REQS["rot_lung"] == "tea"


def test_default_method_reqs_wounds():
    from engine.herb_admin import DEFAULT_METHOD_REQS
    assert DEFAULT_METHOD_REQS["deep_gash"] == "poultice"
    assert DEFAULT_METHOD_REQS["infected_wound"] == "poultice"
    assert DEFAULT_METHOD_REQS["scorched_hide"] == "ointment"


def test_default_method_reqs_other():
    from engine.herb_admin import DEFAULT_METHOD_REQS
    assert DEFAULT_METHOD_REQS["fleas"] == "rub"
    assert DEFAULT_METHOD_REQS["poison_ivy"] == "sap"
    assert DEFAULT_METHOD_REQS["mild_poison"] == "juice"


# ---- sqlite3.Row field access (Row-safe pattern) ----

def test_sqlite_row_has_no_get():
    """Confirm sqlite3.Row lacks .get() — our fix is necessary."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE t (disease TEXT)")
    conn.execute("INSERT INTO t VALUES ('cough:wheeze')")
    row = conn.execute("SELECT * FROM t").fetchone()
    assert not hasattr(row, "get"), "sqlite3.Row should not have .get()"
    conn.close()


def test_row_safe_disease_access():
    """The Row-safe pattern we use in treat() returns the value correctly."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE t (disease TEXT)")
    conn.execute("INSERT INTO t VALUES ('rot_lung:fever')")
    row = conn.execute("SELECT * FROM t").fetchone()
    result = row["disease"] if "disease" in row.keys() else ""
    assert result == "rot_lung:fever"
    conn.close()


def test_row_safe_missing_column_defaults():
    """The Row-safe pattern falls back to default when column is absent."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE t (hp INTEGER)")
    conn.execute("INSERT INTO t VALUES (10)")
    row = conn.execute("SELECT * FROM t").fetchone()
    result = row["disease"] if "disease" in row.keys() else ""
    assert result == ""
    conn.close()


# ---- module-runner entry point ----

_TESTS = [
    test_split_raw_herb,
    test_split_poultice,
    test_split_simmered_milk,
    test_split_multiword_herb_poultice,
    test_split_dried,
    test_split_non_herb_key,
    test_split_tea_suffix_not_shadowed_by_labrador_tea,
    test_knotgrass_has_explicit_prep_methods,
    test_arnica_is_poultice_only,
    test_comfrey_includes_poultice_and_chewed,
    test_labrador_tea_is_decoction,
    test_default_method_reqs_importable,
    test_default_method_reqs_respiratory,
    test_default_method_reqs_wounds,
    test_default_method_reqs_other,
    test_sqlite_row_has_no_get,
    test_row_safe_disease_access,
    test_row_safe_missing_column_defaults,
]


def main() -> None:
    passed = failed = 0
    for fn in _TESTS:
        try:
            fn()
            print(f"  OK  {fn.__name__}")
            passed += 1
        except Exception as exc:
            print(f" FAIL {fn.__name__} — {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
