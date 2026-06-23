from config import CURRENCY_EMOJI


def format_bones(amount: int, *, signed: bool = False) -> str:
    prefix = "+" if signed and amount > 0 else ""
    return f"{prefix}{CURRENCY_EMOJI} {amount}"
