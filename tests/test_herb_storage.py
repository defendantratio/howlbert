"""Herb stack reference parsing."""

from engine.herb_storage import parse_herb_stack_id


def test_parse_herb_stack_id_accepts_stack_prefix():
    assert parse_herb_stack_id("stack:42") == 42
    assert parse_herb_stack_id("STACK:7") == 7


def test_parse_herb_stack_id_accepts_hash_and_plain():
    assert parse_herb_stack_id("#12") == 12
    assert parse_herb_stack_id("99") == 99


def test_parse_herb_stack_id_rejects_invalid():
    assert parse_herb_stack_id(None) is None
    assert parse_herb_stack_id("") is None
    assert parse_herb_stack_id("herb_yarrow") is None
    assert parse_herb_stack_id("stack:abc") is None
