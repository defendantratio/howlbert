"""Lower-stakes subordinate rank disputes; the pecking order below alpha/advisor."""

from __future__ import annotations

import database as db
from config import RANK_DISPUTE_MAX, RANK_DISPUTE_MIN, RANK_DISPUTE_SHIFT
from engine.character import attr_modifier
from engine.dice import roll_d20


def _rank_roll(user) -> tuple[int, int]:
    die = roll_d20()
    mod = attr_modifier(int(user["attr_str"])) + attr_modifier(int(user["attr_cha"]))
    return die, die + mod


def is_eligible_for_rank_dispute(user) -> bool:
    role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
    return role not in ("alpha", "advisor", "pup")


def run_rank_dispute(challenger, defender, *, day: int) -> tuple[bool, str]:
    """
    A subordinate contests their place in the pecking order against another
    packmate; winner climbs, loser drops. Affects den feed priority, not
    leadership; that's the Rite of the Broken Canine's domain.
    """
    if challenger["id"] == defender["id"]:
        return False, "contest your place against someone else; not yourself."
    if not challenger["pack_id"] or challenger["pack_id"] != defender["pack_id"]:
        return False, "rank disputes are settled within your own den."
    if not is_eligible_for_rank_dispute(challenger):
        return False, "alphas, advisors, and pups don't contest pack rank this way."
    if not is_eligible_for_rank_dispute(defender):
        return False, f"**{defender['wolf_name']}** is outside the pecking order (alpha, advisor, or pup)."
    if int(defender["pack_rank"]) >= RANK_DISPUTE_MAX:
        return False, (
            f"**{defender['wolf_name']}** holds the omega position; the bottom of the line. "
            f"the pack doesn't kick down; they've yielded all there is to yield. "
            f"challenge someone above you instead."
        )
    from engine.diminishing import diminishing_note, next_use_multiplier

    dispute_mult, dispute_n = next_use_multiplier(challenger, "rank_dispute", day)

    db.update_user(challenger["discord_id"], wolf_id=challenger["id"], last_rank_dispute_day=day)

    rivalry = db.get_bond(challenger["id"], defender["id"], "rivalry")
    rivalry_mod = 0
    if rivalry:
        s = int(rivalry["strength"])
        if s >= 70:
            rivalry_mod = 2  # a long-stoked grudge sharpens every blow
        elif s >= 40:
            rivalry_mod = 1  # genuine competition; the challenger knows their teeth

    c_die, c_total = _rank_roll(challenger)
    d_die, d_total = _rank_roll(defender)
    c_total += rivalry_mod  # challenger pressed this dispute; the rivalry drives them
    if c_die == 20 and d_die != 20:
        challenger_wins, note = True, " (critical)"
    elif d_die == 20 and c_die != 20:
        challenger_wins, note = False, " (critical)"
    elif c_die == 1 and d_die != 1:
        challenger_wins, note = False, " (fumble)"
    elif d_die == 1 and c_die != 1:
        challenger_wins, note = True, " (fumble)"
    else:
        challenger_wins, note = c_total >= d_total, ""

    if challenger_wins:
        winner, loser = challenger, defender
    else:
        winner, loser = defender, challenger

    shift = max(1, int(RANK_DISPUTE_SHIFT * dispute_mult))
    new_winner_rank = max(RANK_DISPUTE_MIN, int(winner["pack_rank"]) - shift)
    new_loser_rank = min(RANK_DISPUTE_MAX, int(loser["pack_rank"]) + shift)
    db.update_user_by_id(winner["id"], pack_rank=new_winner_rank)
    db.update_user_by_id(loser["id"], pack_rank=new_loser_rank)

    rivalry_note = f" _(+{rivalry_mod} grudge)_" if rivalry_mod else ""
    dim = diminishing_note(dispute_n)
    dim_note = f"\n_{dim}_" if dim else ""
    line = (
        f"**{challenger['wolf_name']}** {c_total}{rivalry_note} vs **{defender['wolf_name']}** {d_total}{note}\n"
        f"**{winner['wolf_name']}** holds the better ground; **{loser['wolf_name']}** yields a step.\n"
        f"den feed priority shifts accordingly.{dim_note}"
    )
    return True, line
