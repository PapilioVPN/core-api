"""Select the most specific registered prefix in one indexed lookup."""

from sqlalchemy import ColumnElement, Select, func, select
from sqlmodel import col

from ..tables import CardPrefixTable


def match_prefix(
    short: str | ColumnElement[str], long: str | ColumnElement[str]
) -> Select[tuple[CardPrefixTable]]:
    """Build the match used for bank lookup and payment card selection.

    Args:
        short: Six-digit candidate.
        long: Up to eight digits, with the same starting six digits.

    Returns:
        A selection of at most one prefix, including inactive matches.
    """
    prefix = col(CardPrefixTable.prefix)
    stmt = (
        select(CardPrefixTable)
        .where(prefix.in_((short, long)))
        .order_by(func.length(prefix).desc())
        .limit(1)
    )
    return stmt
