import re


def get_word_by_counter(
    counter: int, word_1: str, word_2: str, word_3: str
) -> str:
    """Returns the correct word form based on a numeric counter (for Russian pluralization)."""
    if not counter:
        return word_3
    val = counter % 100
    if 10 < val < 20:
        return word_3
    else:
        val = counter % 10
        if val == 1:
            return word_1
        elif 1 < val < 5:
            return word_2
        else:
            return word_3


def price_with_spaces(value: str | int) -> str:
    """Formats a number with spaces every three digits (e.g., 3000 → '3 000')."""
    orig = str(value)
    new = re.sub(r"^(-?\d+)(\d{3})", r"\g<1> \g<2>", orig)
    if orig == new:
        return new
    else:
        return price_with_spaces(new)


def clear_phone_string(value: str) -> str:
    """Removes all non-digit characters from a phone number string."""
    if isinstance(value, str):
        phone = [str(x) for x in value if x.isdigit()]
        return "".join(phone)
    else:
        return str(value)


def format_phone_number(phone_number: str) -> str:
    """Formats a phone number from '71111111111' to '+7 (111) 111-11-11'."""
    if len(phone_number) != 11 or not phone_number.isdigit():
        raise ValueError("Phone number must contain exactly 11 digits.")

    formatted_number = (
        f"+{phone_number[0]} ({phone_number[1:4]}) "
        f"{phone_number[4:7]}-{phone_number[7:9]}-{phone_number[9:]}"
    )
    return formatted_number
