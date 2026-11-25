"""Choose the nearest available automatic transfer amount in PostgreSQL."""

from papilio.types.constants import INT64_MAX
from sqlalchemy import BigInteger, exists, func, literal, select, union_all
from sqlmodel import col

from src.apps.shop.billing.deposits.infra.pg.tables import DepositTable

from ..tables import PaymentTable


def candidates(amount: int, digits: int):
    """Find free amounts beside the price or an already reserved amount."""
    transfer = col(PaymentTable.transfer_amount)
    span = 10**digits - 1
    lower = max(1, amount - span)
    upper = min(INT64_MAX, amount + span)
    deposits = col(DepositTable.amount)
    occupied = union_all(
        select(transfer.label("value")).where(transfer.between(lower, upper)),
        select(deposits).where(deposits.between(lower, upper)),
    ).cte()
    reserved = occupied.c.value
    edges = union_all(
        select(literal(amount - 1, type_=BigInteger).label("value")),
        select(
            literal(min(INT64_MAX, amount + 1), type_=BigInteger).label(
                "value"
            )
        ),
        select(reserved - 1).where(reserved > lower, reserved < amount),
        select(reserved + 1).where(reserved > amount, reserved < upper),
    ).subquery()
    value = edges.c.value
    used = exists(select(1).where(reserved == value))
    stmt = (
        select(value)
        .where(value.between(lower, upper), value != amount, ~used)
        .order_by(func.abs(value - amount), value)
        .limit(1)
    )
    return stmt
