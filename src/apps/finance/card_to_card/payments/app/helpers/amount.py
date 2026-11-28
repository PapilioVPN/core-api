"""Find a free payable amount and derive its fixed-width code."""

from collections.abc import Set


def assign_amount(
    first: int, last: int, digits: int, reserved: Set[int]
) -> tuple[int, str] | None:
    """Return the lowest free amount in the inclusive range and its code."""
    amount = next(
        (value for value in range(first, last + 1) if value not in reserved),
        None,
    )
    return (
        (amount, str(amount).zfill(digits)[-digits:])
        if amount is not None
        else None
    )
