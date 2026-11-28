"""Discover the card payment table through Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ExcludeConstraint

from ...domain.models.records import CardPaymentModel

AMOUNT_CONSTRAINT = "excl_card_payments_amount"


class CardPaymentTable(CardPaymentModel, BaseTable, table=True):
    __table_args__ = (
        ExcludeConstraint(
            (text("numrange(payable_amount, payable_amount, '[]')"), "="),
            (text("tstzrange(created_at, expires_at, '[)')"), "&&"),
            name=AMOUNT_CONSTRAINT,
            using="gist",
            where=text(
                "mode = 'auto' AND payable_amount IS NOT NULL "
                "AND expires_at IS NOT NULL"
            ),
        ),
    )
