"""Password validation — extracted verbatim from RankKW's Zod schema (`lg`)."""
import re

_UPPER = re.compile(r"[A-Z]")
_DIGIT = re.compile(r"[0-9]")
_SPECIAL = re.compile(r"[^A-Za-z0-9]")


def validate_password(value: str) -> str:
    """Raises ValueError with the exact RankKW message on failure."""
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not _UPPER.search(value):
        raise ValueError("Must contain at least one uppercase letter")
    if not _DIGIT.search(value):
        raise ValueError("Must contain at least one number")
    if not _SPECIAL.search(value):
        raise ValueError("Must contain at least one special character")
    return value