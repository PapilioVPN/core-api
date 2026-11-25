"""A stored payment and its submitted bank receipt."""

from dataclasses import dataclass

from src.apps.shop.billing.receipts.domain.models.records import ReceiptModel

from ..models.records import PaymentModel


@dataclass(frozen=True, slots=True)
class PaymentDetail:
    payment: PaymentModel
    receipt: ReceiptModel | None
