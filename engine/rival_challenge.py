"""Spring mating-season rival challenges for receptive females."""

from __future__ import annotations

from engine.dice import format_contest_roll, roll_contest
from engine.character import parse_proficiencies
from rpg_rules import ROLE_PROFICIENCIES


def execute_rival_challenge(
    challenger,
    defender,
    *,
    mode: str,
    female_favors_challenger: bool = False,
    day: int,
) -> tuple[str, str | None]:
    """
    Resolve physical (Strength + Hunting) or vocal (Charisma + Intimidation) challenge.
    Returns (winner_name, narrative). Female is not forced to mate with winner.
    """
    favor_note = ""
    if female_favors_challenger:
        favor_note = "\n_The receptive female favors the challenger (+2)._"

    if mode == "vocal":
        att = roll_contest(
            challenger,
            attr_keys=("attr_cha",),
            skill_key="intimidation",
            skill_label="Charisma + Intimidation",
            game_day=day,
            flat_bonus=2 if female_favors_challenger else 0,
            proficient="intimidation" in parse_proficiencies(challenger["skill_proficiencies"])
            or challenger["wolf_role"] in ROLE_PROFICIENCIES,
        )
        defn = roll_contest(
            defender,
            attr_keys=("attr_cha",),
            skill_key="intimidation",
            skill_label="Charisma + Intimidation",
            game_day=day,
            proficient="intimidation" in parse_proficiencies(defender["skill_proficiencies"])
            or defender["wolf_role"] in ROLE_PROFICIENCIES,
        )
        body = (
            f"**Vocal challenge** (howling intimidation)\n"
            f"{format_contest_roll(challenger['wolf_name'], att)}\n"
            f"{format_contest_roll(defender['wolf_name'], defn)}"
            f"{favor_note}"
        )
        if att["contest_total"] > defn["contest_total"]:
            body += (
                f"\n**{challenger['wolf_name']}** dominates the song. "
                f"**{defender['wolf_name']}** cannot approach the female for the rest of this sunrise."
            )
            return challenger["wolf_name"], body
        if defn["contest_total"] > att["contest_total"]:
            body += f"\n**{defender['wolf_name']}** holds the den line."
            return defender["wolf_name"], body
        body += "\nStalemate; neither wolf yields cleanly."
        return challenger["wolf_name"], body

    att = roll_contest(
        challenger,
        attr_keys=("attr_str",),
        skill_key="hunting",
        skill_label="Strength + Hunting",
        game_day=day,
        flat_bonus=2 if female_favors_challenger else 0,
        proficient="hunting" in parse_proficiencies(challenger["skill_proficiencies"]),
    )
    defn = roll_contest(
        defender,
        attr_keys=("attr_str",),
        skill_key="hunting",
        skill_label="Strength + Hunting",
        game_day=day,
        proficient="hunting" in parse_proficiencies(defender["skill_proficiencies"]),
    )
    body = (
        f"**Physical challenge** (pin or submit)\n"
        f"{format_contest_roll(challenger['wolf_name'], att)}\n"
        f"{format_contest_roll(defender['wolf_name'], defn)}"
        f"{favor_note}"
    )
    if att["contest_total"] > defn["contest_total"]:
        body += (
            f"\n**{challenger['wolf_name']}** pins **{defender['wolf_name']}**. "
            "The loser must retreat or submit."
        )
        return challenger["wolf_name"], body
    if defn["contest_total"] > att["contest_total"]:
        body += f"\n**{defender['wolf_name']}** drives the challenger off."
        return defender["wolf_name"], body
    body += "\nNeither wolf gains a clean pin; stalemate."
    return challenger["wolf_name"], body
