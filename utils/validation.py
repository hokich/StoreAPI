import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email


PASSWORD_REGEX = (
    r"^(?=.*[a-zA-Zа-яА-Я])(?=.*\d)"
    r"(?=.*[!@#$%^&*()_+=\-[\]{};':\"\\|,.<>\/?~])"
    r"[a-zA-Zа-яА-Я0-9!@#$%^&*()_+=\-[\]{};':\"\\|,.<>\/?~]{6,}$"
)


def is_phone_valid(value: str) -> bool:
    """Validates if a phone number matches the Russian format 7XXXXXXXXXX."""
    phone_pattern = re.compile(r"^7\d{10}$")
    return bool(phone_pattern.match(value))


def is_email_valid(value: str) -> bool:
    """Validates if an email address is correctly formatted using Django's built-in validator."""
    try:
        validate_email(value)
        return True
    except ValidationError:
        return False


def is_password_valid(value: str) -> bool:
    """Validates if a password meets security requirements (letters, digits, special characters)."""
    password_pattern = re.compile(PASSWORD_REGEX)
    return bool(password_pattern.match(value))
