"""Provider invoice observations and prepared inputs for a payment check."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from src.apps.shop.crypto.gateways.domain.dtos.configs import PlisioConfig

from ..models.records import CryptoPaymentModel


@dataclass(frozen=True, slots=True)
class PlisioCheck:
    payment: CryptoPaymentModel
    invoice_id: str
    config: PlisioConfig = field(repr=False)


class OperationStatus(StrEnum):
    COMPLETED = "completed"
    REPLACED = "replaced"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Operation:
    id: str
    status: OperationStatus
    parent_id: str | None
    child_ids: tuple[str, ...]
    order_id: str | None
    quote_amount: Decimal | None
    quote_currency: str | None
    expected: Decimal | None
    received: Decimal | None


@dataclass(frozen=True, slots=True)
class RecheckStats:
    selected: int
    confirmed: int
    failed: int
