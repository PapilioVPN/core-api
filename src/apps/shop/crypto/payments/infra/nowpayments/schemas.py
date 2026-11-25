"""Validate NOWPayments invoice, IPN and authenticated status payloads."""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from .config import HTTPSURL

ProviderID = Annotated[str, Field(pattern=r"^[0-9]+$", max_length=64)]
PositiveAmount = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]
PaidAmount = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]


class InvoiceOut(BaseModel):
    model_config = ConfigDict(
        coerce_numbers_to_str=True, hide_input_in_errors=True
    )

    id: ProviderID
    order_id: str
    price_amount: PositiveAmount
    price_currency: str
    pay_currency: str | None = None
    invoice_url: HTTPSURL


class NoticeIn(BaseModel):
    model_config = ConfigDict(
        coerce_numbers_to_str=True, hide_input_in_errors=True
    )

    payment_id: ProviderID
    invoice_id: ProviderID | None = None
    payment_status: str


class PaymentOut(NoticeIn):
    order_id: str | None = None
    price_amount: PositiveAmount
    price_currency: str
    pay_amount: PositiveAmount
    pay_currency: str
    actually_paid: PaidAmount | None = None
