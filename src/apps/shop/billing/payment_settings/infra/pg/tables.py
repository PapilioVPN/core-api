"""The single Shop payment settings row."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, text

from ...domain.models.records import PaymentSettingsModel


class PaymentSettingsTable(PaymentSettingsModel, BaseTable, table=True):
    table_name = "tbl_payment_settings"
    __table_args__ = (
        Index("uq_payment_settings_singleton", text("(true)"), unique=True),
    )
