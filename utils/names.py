def validate_display_name(name: str, *, label: str = "Name") -> tuple[str | None, str | None]:
    cleaned = name.strip()
    if len(cleaned) < 2 or len(cleaned) > 32:
        return None, f"{label} must be between 2 and 32 characters."
    return cleaned, None
