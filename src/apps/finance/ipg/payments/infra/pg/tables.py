"""Discover IPG payments through Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import UniqueConstraint

from ...domain.models.records import PaymentModel


class IPGPaymentTable(PaymentModel, BaseTable, table=True):
    __table_args__ = (UniqueConstraint("gateway_id", "reference"),)
