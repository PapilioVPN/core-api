"""Local checksum validation for Iranian card numbers."""

from pydantic_core import PydanticCustomError


def validate_card_number(value: str) -> str:
    """Check the number's Luhn digit and reject repeated-digit inputs.

    Args:
        value: Card number already checked against 16 ASCII digits.

    Returns:
        The unchanged card number.

    Raises:
        PydanticCustomError: The checksum fails or every digit repeats.
    """
    if len(set(value)) == 1:
        raise PydanticCustomError(
            "invalid_card_number",
            "Card number cannot contain one repeated digit",
        )
    checksum = 0
    for index, character in enumerate(value):
        digit = int(character)
        if index % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    if checksum % 10 != 0:
        raise PydanticCustomError(
            "invalid_card_number_checksum", "Card number checksum is invalid"
        )
    return value
