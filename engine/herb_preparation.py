# herb_preparation.py
"""Herb preparation; dry, poultice, tea, and more."""

from __future__ import annotations


import database as db
from config import HERB_PREP_DC
from engine.character import parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from engine.role_features import is_full_medic
from herbs import HERBS


# preparation methods a wolf can choose. each maps to the stored `form`, its
# herblore dc, which source forms it can be made from (the chaining), and a
# player-facing effect line. you can dry a fresh herb, then turn the dried herb
# into a tea, rub, juice, poultice, and so on; a tea or gargle can be sweetened.
PREP_METHODS: dict[str, dict] = {
    "dry":      {"form": "dried",         "dc": 8,  "from": ("fresh",),          "bonus": " Stores for months in your herb bag."},
    "poultice": {"form": "poultice",      "dc": 10, "from": ("fresh", "dried"),  "bonus": " Heals **1d4** on complex wounds (vs 1d2 raw)."},
    "juice":    {"form": "juice",         "dc": 11, "from": ("fresh", "dried"),  "bonus": " Pressed juice; fast into eyes and open wounds."},
    "raw":      {"form": "raw",           "dc": 6,  "from": ("fresh", "dried"),  "bonus": " Eaten raw; swallowed whole."},
    "tea":      {"form": "tea",           "dc": 10, "from": ("fresh", "dried"),  "bonus": " Steeped tea; a gentle internal draught."},
    "gargle":   {"form": "gargle",        "dc": 10, "from": ("fresh", "dried"),  "bonus": " A gargle for sore throat and mouth."},
    "sweeten":  {"form": "sweetened",     "dc": 8,  "from": ("tea", "gargle"),   "bonus": " Sweetened with honey; palatable to pups and the reluctant."},
    "ointment": {"form": "ointment",      "dc": 12, "from": ("fresh", "dried"),  "bonus": " A lasting salve; heals **1d4** on complex wounds."},
    "sap":      {"form": "sap",           "dc": 9,  "from": ("fresh",),          "bonus": " Pressed sap for stings and leaf-burn."},
    "rub":      {"form": "rub",           "dc": 9,  "from": ("fresh", "dried"),  "bonus": " A pelt rub; wards pests and soothes skin."},
    "cook":     {"form": "cooked",        "dc": 10, "from": ("fresh",),          "bonus": " Eaten cooked; cooking tames the raw bite."},
    "milk":     {"form": "simmered_milk", "dc": 12, "from": ("fresh", "dried"),  "bonus": " Simmered in milk; soothing for pups and sore eyes."},
}

PREP_FORMS = tuple(PREP_METHODS)

METHOD_LABELS = {
    "dry": "dry", "poultice": "poultice", "juice": "juice", "raw": "eaten raw",
    "tea": "tea", "gargle": "gargle", "sweeten": "sweeten", "ointment": "ointment",
    "sap": "sap", "rub": "rub", "cook": "eaten cooked", "milk": "simmered milk",
}

_METHOD_LIST_MSG = "use one of: **dry, poultice, juice, eaten raw, tea, gargle, sweeten, ointment, sap, rub, eaten cooked, simmered milk**."


def _herblore_proficient(user) -> bool:
    profs = parse_proficiencies(user["skill_proficiencies"])
    return "herblore" in profs or "medicine" in profs or is_full_medic(user)


def _prep_dc(method: str, user, herb_key: str) -> int:
    if method == "poultice" and is_full_medic(user):
        return HERB_PREP_DC["poultice_simple"]
    spec = PREP_METHODS.get(method)
    return spec["dc"] if spec else 10


def _target_form(method: str) -> str:
    return PREP_METHODS[method]["form"]


def _prep_transition(method: str, current_form: str) -> tuple[bool, str]:
    """Validate a prep on a stack in ``current_form``. Returns (ok, target_form)
    on success, or (False, error_message)."""
    from engine.herb_properties import form_label

    spec = PREP_METHODS.get(method)
    if not spec:
        return False, _METHOD_LIST_MSG
    if current_form == spec["form"]:
        return False, f"already prepared as **{form_label(spec['form'])}**."
    if current_form not in spec["from"]:
        allowed = " or ".join(form_label(f) for f in spec["from"])
        return False, (
            f"**{METHOD_LABELS.get(method, method)}** needs a **{allowed}** herb; "
            f"this one is **{form_label(current_form)}**."
        )
    return True, spec["form"]


def prepare_herb_stack(
    user,
    stack_id: int,
    method: str,
    *,
    day: int,
    at_den: bool = False,
) -> tuple[bool, str]:
    if method not in PREP_METHODS:
        return False, _METHOD_LIST_MSG
    stack = db.get_herb_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "that herb isn't in your forage bag."
    herb_key = stack["herb_key"]
    meta = HERBS.get(herb_key, {})
    ok, target = _prep_transition(method, stack["form"])
    if not ok:
        return False, target

    dc = _prep_dc(method, user, herb_key)
    result = resolve_check(
        user,
        attr_keys=("attr_int", "attr_wis"),
        skill="Herblore",
        dc=dc,
        proficient=_herblore_proficient(user),
        skill_key="herblore",
        game_day=day,
    )
    if result["outcome"] == "critical_failure":
        db.remove_herb_stack(stack_id)
        return (
            False,
            format_roll_result(result)
            + f"\n\n**{meta.get('name', herb_key)}** ruined; batch spoiled.",
        )
    if not result["success"]:
        if method == "dry":
            db.update_herb_stack(stack_id, potency=max(40, int(stack["potency"]) - 30))
            return (
                False,
                format_roll_result(result)
                + "\n\npoor drying; **reduced potency** (still usable).",
            )
        return False, format_roll_result(result) + "\n\npreparation failed; the herb keeps its form; try again."

    potency = 90 if (method == "dry" and result["outcome"] != "critical_success") else 100
    db.update_herb_stack(
        stack_id,
        form=target,
        acquired_day=day,
        potency=min(120, potency),
    )
    from engine.herb_properties import form_label

    bonus = PREP_METHODS[method]["bonus"]
    return (
        True,
        format_roll_result(result)
        + f"\n\n**{meta.get('name', herb_key)}** → **{form_label(target)}**.{bonus}",
    )


def prepare_pack_herb_stack(
    user,
    store_id: int,
    method: str,
    *,
    day: int,
    pack_id: int,
) -> tuple[bool, str]:
    """Dry (or prepare) one healers' den store stack; dryall uses this for fresh rows."""
    if method not in PREP_METHODS:
        return False, _METHOD_LIST_MSG
    stack = db.get_pack_herb_stack(store_id)
    if not stack or int(stack["pack_id"]) != pack_id:
        return False, "that stack isn't in your pack's herb store."
    herb_key = stack["herb_key"]
    meta = HERBS.get(herb_key, {})
    ok, target = _prep_transition(method, stack["form"])
    if not ok:
        return False, target

    dc = _prep_dc(method, user, herb_key)
    result = resolve_check(
        user,
        attr_keys=("attr_int", "attr_wis"),
        skill="Herblore",
        dc=dc,
        proficient=_herblore_proficient(user),
        skill_key="herblore",
        game_day=day,
    )
    name = meta.get("name", herb_key)
    qty = int(stack["quantity"])
    store_note = f" (den store ×**{qty}**)" if qty > 1 else " (den store)"

    if result["outcome"] == "critical_failure":
        db.remove_pack_herb_stack(store_id)
        return (
            False,
            format_roll_result(result)
            + f"\n\n**{name}**{store_note} ruined; batch spoiled.",
        )
    if not result["success"]:
        if method == "dry":
            db.update_pack_herb_stack(store_id, potency=max(40, int(stack["potency"]) - 30))
            return (
                False,
                format_roll_result(result)
                + f"\n\n**{name}**{store_note}: poor drying; **reduced potency** (still usable).",
            )
        return False, format_roll_result(result) + "\n\npreparation failed; try again."

    potency = 90 if (method == "dry" and result["outcome"] != "critical_success") else 100
    db.update_pack_herb_stack(
        store_id,
        form=target,
        acquired_day=day,
        potency=min(120, potency),
    )
    from engine.herb_properties import form_label

    bonus = " Stores for months in the healers' den." if method == "dry" else PREP_METHODS[method]["bonus"]
    return (
        True,
        format_roll_result(result)
        + f"\n\n**{name}**{store_note} → **{form_label(target)}**.{bonus}",
    )


def prepare_herb_from_inventory(
    user,
    item_key: str,
    method: str,
    *,
    day: int,
    guild_id: int,
    at_den: bool = False,
) -> tuple[bool, str]:
    """Consume one inventory herb and prepare it (dry keeps in inventory; other forms → den store)."""
    key = item_key.strip().lower()
    if not key.startswith("herb_"):
        return False, "use an inventory herb key like **`herb_arnica`**."
    herb_key = key.replace("herb_", "", 1)
    if herb_key not in HERBS:
        return False, "that herb isn't in the compendium."
    item = db.get_item_by_key(key)
    if not item:
        return False, "unknown herb item."
    qty = db.get_inventory_quantity_for_wolf(user["id"], item["id"])
    if qty < 1:
        return False, f"you don't have **{item['name']}** in `/bones action:inventory`."
    if not db.consume_item_for_wolf(user["id"], item["id"], quantity=1):
        return False, "could not use herb from `/bones action:inventory`."

    meta = HERBS.get(herb_key, {})
    if method not in PREP_METHODS:
        db.grant_item_for_wolf(user["id"], item["id"], quantity=1)
        return False, _METHOD_LIST_MSG
    # inventory herbs are fresh; a method that must be built from a tea/gargle
    # (like sweeten) can't be run on a raw inventory herb.
    if "fresh" not in PREP_METHODS[method]["from"]:
        db.grant_item_for_wolf(user["id"], item["id"], quantity=1)
        allowed = " or ".join(PREP_METHODS[method]["from"])
        return False, f"**{METHOD_LABELS.get(method, method)}** needs a **{allowed}** herb; prepare that first from your forage bag."

    dc = _prep_dc(method, user, herb_key)
    result = resolve_check(
        user,
        attr_keys=("attr_int", "attr_wis"),
        skill="Herblore",
        dc=dc,
        proficient=_herblore_proficient(user),
        skill_key="herblore",
        game_day=day,
    )
    target = _target_form(method)
    name = meta.get("name", herb_key)

    if result["outcome"] == "critical_failure":
        return (
            False,
            format_roll_result(result) + f"\n\n**{name}** ruined; batch spoiled.",
        )
    if not result["success"]:
        db.grant_item_for_wolf(user["id"], item["id"], quantity=1)
        if method == "dry":
            return (
                False,
                format_roll_result(result)
                + "\n\npoor drying; herb kept but **reduced potency** (still usable).",
            )
        return False, format_roll_result(result) + "\n\npreparation failed; herb returned."

    from engine.herb_properties import form_label

    potency = 90 if (method == "dry" and result["outcome"] != "critical_success") else 100

    if method == "dry":
        db.grant_item_for_wolf(user["id"], item["id"], quantity=1)
        bonus = " Stores for months in `/bones action:inventory`."
        return (
            True,
            format_roll_result(result) + f"\n\n**{name}** → **{form_label(target)}**.{bonus}",
        )

    pack_id = int(user["pack_id"]) if user and user["pack_id"] else 0
    if not pack_id:
        db.grant_item_for_wolf(user["id"], item["id"], quantity=1)
        return (
            False,
            "join a pack to prepare non-dried forms into the healers' den store (or prepare from your `/food`/forage bag).",
        )
    db.add_pack_herb_stack(
        pack_id,
        herb_key,
        form=target,
        potency=min(120, potency),
        quantity=1,
        acquired_day=day,
        guild_id=guild_id,
        deposited_by=user["id"],
    )
    bonus = PREP_METHODS[method]["bonus"]
    return (
        True,
        format_roll_result(result)
        + f"\n\n**{name}** → **{form_label(target)}** in the healers' store (`/herbs action:store mode:list`).{bonus}",
    )


def dry_all_fresh_herbs(
    user,
    *,
    day: int,
    guild_id: int,
    at_den: bool = False,
) -> tuple[bool, str]:
    """Roll drying separately for each inventory herb and fresh den-store stack."""
    _ = at_den
    inventory_herbs = [
        (row["key"], row["name"], int(row["quantity"]))
        for row in db.get_inventory_for_wolf(user["id"])
        if row["key"].startswith("herb_")
    ]
    pack_id = int(user["pack_id"]) if user and user["pack_id"] else None
    pack_fresh_ids: list[int] = []
    if pack_id:
        pack_fresh_ids = [
            int(s["id"])
            for s in db.get_pack_herb_stacks(pack_id)
            if s["form"] == "fresh"
        ]
    if not inventory_herbs and not pack_fresh_ids:
        return (
            False,
            "no herbs to dry in **inventory** (`/bones action:inventory`) or "
            "**healers' den store** (`/herbs action:store mode:list`).",
        )

    dried = 0
    failed = 0
    ruined = 0
    lines: list[str] = []

    for item_key, name, qty in inventory_herbs:
        for _ in range(qty):
            ok, msg = prepare_herb_from_inventory(
                user,
                item_key,
                "dry",
                day=day,
                guild_id=guild_id,
                at_den=at_den,
            )
            if ok:
                dried += 1
                lines.append(f"**{name}** → dried")
            elif "ruined" in msg.lower() or "spoiled" in msg.lower():
                ruined += 1
                lines.append(f"**{name}**; ruined")
            else:
                failed += 1
                lines.append(f"**{name}**; failed")

    if pack_id:
        for store_id in pack_fresh_ids:
            stack = db.get_pack_herb_stack(store_id)
            if not stack or stack["form"] != "fresh":
                continue
            meta = HERBS.get(stack["herb_key"], {})
            name = meta.get("name", stack["herb_key"])
            qty = int(stack["quantity"])
            label = f"**{name}** (den store ×{qty})" if qty > 1 else f"**{name}** (den store)"
            ok, msg = prepare_pack_herb_stack(
                user, store_id, "dry", day=day, pack_id=pack_id
            )
            if ok:
                dried += 1
                lines.append(f"{label} → dried")
            elif "ruined" in msg.lower() or "spoiled" in msg.lower():
                ruined += 1
                lines.append(f"{label}; ruined")
            else:
                failed += 1
                lines.append(f"{label}; failed")

    if dried == 0:
        summary = "\n".join(lines[:10])
        return False, f"no herbs dried.\n{summary}"

    summary = "\n".join(lines[:12])
    if len(lines) > 12:
        summary += f"\n_…and {len(lines) - 12} more._"
    tail = f"\n\n**{dried}** dried"
    if failed:
        tail += f", **{failed}** failed"
    if ruined:
        tail += f", **{ruined}** ruined"
    return True, f"**dry all** complete.{tail}\n{summary}"