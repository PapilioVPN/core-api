"""Discover hosted card payments through Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import UniqueConstraint

from ...domain.models.deliveries import DeliveryModel
from ...domain.models.records import PaymentModel


class CardGatewayPaymentTable(PaymentModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint(
            "gateway_id",
            "slug",
            name="tbl_card_gateway_payments_gateway_id_slug_key",
        ),
    )


class CardGatewayDeliveryTable(DeliveryModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint(
            "gateway_id",
            "delivery_id",
            name="tbl_card_gateway_deliveries_gateway_id_delivery_id_key",
        ),
    )
