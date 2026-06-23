"""Birth sex, sexuality, and attraction for courtship / mating."""

BIRTH_SEX_LABELS = {
    "female": "Female",
    "male": "Male",
    "intersex": "Intersex",
    "nonbinary": "Nonbinary",
}

PUP_SEXUALITY = "too_young"

SEXUALITY_OPTIONS_ADULT: tuple[tuple[str, str], ...] = (
    ("Heterosexual", "heterosexual"),
    ("Homosexual", "homosexual"),
    ("Bisexual", "bisexual"),
    ("Pansexual", "pansexual"),
    ("Asexual", "asexual"),
    ("Demisexual", "demisexual"),
    ("Demiromantic", "demiromantic"),
)
SEXUALITY_OPTIONS: tuple[tuple[str, str], ...] = (
    ("Too young / none", PUP_SEXUALITY),
) + SEXUALITY_OPTIONS_ADULT
SEXUALITY_LABELS = {value: label for label, value in SEXUALITY_OPTIONS}
VALID_SEXUALITIES = frozenset(SEXUALITY_LABELS)
ADULT_SEXUALITIES = frozenset(value for _, value in SEXUALITY_OPTIONS_ADULT)
BOND_FIRST_SEXUALITIES = frozenset({"demisexual", "demiromantic"})


def is_pup_age(age_moons: int) -> bool:
    from engine.aging import stage_for_age

    return stage_for_age(age_moons) == "pup"


def is_too_young_for_sexuality(age_moons: int) -> bool:
    from engine.aging import stage_for_age

    return stage_for_age(age_moons) in ("pup", "juvenile")


def resolve_register_sexuality(age_months: int, sexuality: str | None) -> str:
    if is_too_young_for_sexuality(age_months):
        return PUP_SEXUALITY
    if sexuality in ADULT_SEXUALITIES:
        return sexuality
    return "bisexual"


def validate_set_sexuality(user, sexuality: str) -> tuple[str | None, str | None]:
    """Return (stored_value, error_message)."""
    if sexuality not in VALID_SEXUALITIES:
        return None, "Unknown sexuality."
    age = int(user["age_months"]) if "age_months" in user.keys() else 24
    if is_too_young_for_sexuality(age):
        if sexuality != PUP_SEXUALITY:
            from config import JUVENILE_MAX_MOONS

            return None, (
                f"Wolves under **{JUVENILE_MAX_MOONS} moons** stay **Too young / none**. "
                "Pick an attraction after aging up with `/setsexuality`."
            )
        return PUP_SEXUALITY, None
    if sexuality == PUP_SEXUALITY:
        from config import JUVENILE_MAX_MOONS

        return None, f"**Too young / none** only applies to wolves under **{JUVENILE_MAX_MOONS} moons**."
    return sexuality, None


def get_birth_sex(user) -> str | None:
    if "birth_sex" in user.keys() and user["birth_sex"]:
        return user["birth_sex"]
    if "gender" in user.keys() and user["gender"]:
        return user["gender"]
    return None


def get_sexuality(user) -> str:
    if "sexuality" in user.keys() and user["sexuality"]:
        return user["sexuality"]
    return "bisexual"


def is_attracted_to(sexuality: str, my_birth_sex: str, their_birth_sex: str) -> bool:
    if not their_birth_sex:
        return True
    if sexuality in ("bisexual", "pansexual", "demisexual", "demiromantic"):
        return True
    if sexuality in ("asexual", PUP_SEXUALITY):
        return False
    if sexuality == "heterosexual":
        return my_birth_sex != their_birth_sex
    if sexuality == "homosexual":
        return my_birth_sex == their_birth_sex
    return True


def mate_pairing(user, partner) -> tuple[str, str | None]:
    """
    Returns (mode, error_message).
    mode: conception | bond | error
    """
    u_sex = get_birth_sex(user)
    p_sex = get_birth_sex(partner)
    if not u_sex or not p_sex:
        return "error", "Both wolves need a birth sex on file (`/setbirthsex` or re-register)."

    u_orient = get_sexuality(user)
    p_orient = get_sexuality(partner)

    if u_orient == PUP_SEXUALITY or p_orient == PUP_SEXUALITY:
        return "error", "This wolf is too young for mating or courtship."

    if not is_attracted_to(u_orient, u_sex, p_sex):
        return "error", "You are not attracted to this wolf's birth sex."
    if not is_attracted_to(p_orient, p_sex, u_sex):
        return "error", "They are not attracted to your birth sex."

    if u_orient in BOND_FIRST_SEXUALITIES or p_orient in BOND_FIRST_SEXUALITIES:
        if not are_bonded_mates(user, partner):
            return "bond", None

    if u_orient == "asexual" or p_orient == "asexual":
        return "bond", None
    if (u_sex == "female" and p_sex == "male") or (u_sex == "male" and p_sex == "female"):
        return "conception", None
    return "bond", None


def conception_parents(user, partner):
    """Return (female_row, male_row) or (None, None) if not a biological pair."""
    u_sex = get_birth_sex(user)
    p_sex = get_birth_sex(partner)
    if u_sex == "female" and p_sex == "male":
        return user, partner
    if p_sex == "female" and u_sex == "male":
        return partner, user
    return None, None


def court_attraction_allowed(courter, target) -> tuple[bool, str | None]:
    """Whether courter may attempt courtship with target."""
    u_sex = get_birth_sex(courter)
    t_sex = get_birth_sex(target)
    if not u_sex or not t_sex:
        return True, None

    u_orient = get_sexuality(courter)
    t_orient = get_sexuality(target)

    if u_orient == PUP_SEXUALITY:
        return False, "You are too young for courtship."
    if t_orient == PUP_SEXUALITY:
        return False, "They are too young for courtship."

    if u_orient not in ("asexual", *BOND_FIRST_SEXUALITIES) and not is_attracted_to(u_orient, u_sex, t_sex):
        return False, "You are not attracted to that birth sex."
    if t_orient not in ("asexual", *BOND_FIRST_SEXUALITIES) and not is_attracted_to(t_orient, t_sex, u_sex):
        return False, "They are not attracted to your birth sex."
    return True, None


def are_bonded_mates(user, partner) -> bool:
    if "bonded_mate_id" not in user.keys() or "bonded_mate_id" not in partner.keys():
        return False
    if not user["bonded_mate_id"] or not partner["bonded_mate_id"]:
        return False
    return (
        user["bonded_mate_id"] == partner["id"]
        and partner["bonded_mate_id"] == user["id"]
    )
