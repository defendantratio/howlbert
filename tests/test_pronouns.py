"""Lore and manual pronoun resolution."""

from engine.pronouns import canonical_pronouns_for_name, resolve_wolf_pronouns, wolf_pronouns


def test_canonical_neopronouns():
    assert canonical_pronouns_for_name("Rotteddust") == "ey/em"
    assert canonical_pronouns_for_name("Curlgrip") == "fae/faer"
    assert canonical_pronouns_for_name("Stonepiercer") == "xe/xir"
    assert canonical_pronouns_for_name("Ebb") == "ae/aer"


def test_explicit_override():
    assert (
        resolve_wolf_pronouns("Curlgrip", birth_sex="female", explicit="they/them")
        == "they/them"
    )


def test_lore_before_birth_sex():
    assert resolve_wolf_pronouns("Fernspot", birth_sex="male") == "she/her"


def test_birth_sex_fallback():
    assert resolve_wolf_pronouns("CustomWolf", birth_sex="male") == "he/him"


def test_wolf_pronouns_user_row():
    user = {"wolf_name": "Curlgrip", "birth_sex": "female", "pronouns": None}
    assert wolf_pronouns(user) == "fae/faer"


def test_barkhollow_he_she():
    assert canonical_pronouns_for_name("Barkhollow") == "he/she"
    user = {"wolf_name": "Barkhollow", "birth_sex": "intersex", "pronouns": None}
    assert wolf_pronouns(user) == "he/she"


def test_interchangeable_prose_inference():
    from engine.pronouns import _infer_pronouns_from_prose

    blob = "He bowed her head. She shuffled; his pouch. Mother expected her to die; he did not."
    assert _infer_pronouns_from_prose(blob) == "he/she"


def test_adapt_barkhollow_to_she():
    from engine.pronouns import adapt_prose_pronouns

    sample = "He did not pick yet; first bowed her head. He stood slowly."
    out = adapt_prose_pronouns(sample, "she/her", source="he/she")
    assert "She did not pick" in out
    assert "her head" in out
    assert "She stood" in out
    assert " He " not in out and " he " not in out


def test_adapt_rottedust_to_they():
    from engine.pronouns import adapt_prose_pronouns

    sample = "Ey did not look up. Em shuffled back with eir gourd."
    out = adapt_prose_pronouns(sample, "they/them", source="ey/em")
    assert "They did not look up" in out
    assert "them" in out.lower()
    assert "their" in out.lower()


def test_barkhollow_trait_blurbs_mixed():
    from engine.character_traits import _trait_blurb_for_display, canonical_traits_for_name

    canon = canonical_traits_for_name("Barkhollow")
    hollow = next(t for t in canon["weaknesses"] if t["name"] == "Hollow Chest")
    forget = next(t for t in canon["weaknesses"] if t["name"] == "Forgetful")
    slow = next(t for t in canon["weaknesses"] if t["name"] == "Slow")
    assert "her gasping" in hollow["blurb"]
    assert "remind him" in forget["blurb"]
    assert "her pace" in slow["blurb"]

    user = {"wolf_name": "Barkhollow", "birth_sex": "intersex", "pronouns": None}
    # Stale DB blurb would be all masculine; display should use live canon mix.
    stale = {"name": "Hollow Chest", "blurb": "a short sprint leaves him gasping."}
    out = _trait_blurb_for_display(user, stale)
    assert "her gasping" in out
    assert "him gasping" not in out


def test_adapt_text_for_user_explicit():
    from engine.pronouns import adapt_text_for_user

    user = {
        "wolf_name": "Barkhollow",
        "birth_sex": "intersex",
        "pronouns": "she/her",
    }
    text = "He stood slowly; his pouch was full."
    out = adapt_text_for_user(text, user)
    assert "She stood" in out
    assert "her pouch" in out
