"""Hunt flavor text matches prey size; run: python -m tests.test_hunt_flavor"""

from engine.hunt import GENERIC_HUNT_FLAVOR, hunt_flavor_for_prey

HEAVY_LINE = "You brought down heavy prey alone. Word will travel."


def test_grouse_never_heavy_flavor() -> None:
    for amount in (16, 27, 38, 45, 60):
        flavor = hunt_flavor_for_prey("grouse", amount)
        assert HEAVY_LINE not in flavor, f"grouse @ {amount} bones: {flavor!r}"
        assert flavor not in GENERIC_HUNT_FLAVOR["big"]
        assert flavor not in GENERIC_HUNT_FLAVOR["legendary"]


def test_deer_can_be_heavy() -> None:
    flavor = hunt_flavor_for_prey("deer", 45)
    assert flavor in (
        *GENERIC_HUNT_FLAVOR["big"],
        *(
            "A full deer share. Your jaws still ache from the haul.",
        ),
    ) or "deer" in flavor.lower() or "haul" in flavor.lower()


def test_prey_key_grouse_not_on_big_hunts() -> None:
    from engine.prey_items import prey_key_from_hunt_amount

    for amount in range(36, 61):
        key = prey_key_from_hunt_amount(amount)
        assert key not in ("grouse", "agouti", "hare", "vole"), amount
    for amount in range(29, 36):
        assert prey_key_from_hunt_amount(amount) == "beaver", amount


if __name__ == "__main__":
    test_grouse_never_heavy_flavor()
    test_deer_can_be_heavy()
    test_prey_key_grouse_not_on_big_hunts()
    print("OK")
