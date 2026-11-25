"""Plisio hosted invoice, JSON callback and operation contracts."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from src.apps.shop.crypto.types import HTTPSURL

TxnID = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]+$", max_length=64)]
QuoteAmount = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]
ReceivedAmount = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]


class InvoiceOut(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    txn_id: TxnID
    invoice_url: HTTPSURL


class NoticeIn(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    txn_id: TxnID
    switch_id: TxnID | Literal[""] | None = None
    status: str


class OperationParams(BaseModel):
    model_config = ConfigDict(
        coerce_numbers_to_str=True, hide_input_in_errors=True
    )

    order_number: str
    source_amount: QuoteAmount
    source_currency: str


class OperationOut(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    type: Literal["invoice"]
    id: TxnID
    parent_id: TxnID | Literal[""] | None = None
    status: str
    psys_cid: str | None = None
    sum: QuoteAmount | None = None
    actual_sum: ReceivedAmount | None = None
    params: OperationParams | None = None
    child_ids: list[TxnID] = Field(default_factory=list)


class Success[T: BaseModel](BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    status: Literal["success"]
    data: T
