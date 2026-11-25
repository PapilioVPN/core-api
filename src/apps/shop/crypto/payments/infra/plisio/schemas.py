"""The portion of a Plisio response needed for hosted payment."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl, StrictInt, field_validator

type InvoiceID = Annotated[
    str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
]
type Amount = Annotated[Decimal, Field(allow_inf_nan=False)]


class InvoiceData(BaseModel):
    txn_id: InvoiceID
    invoice_url: HttpUrl

    @field_validator("invoice_url")
    @classmethod
    def hosted_url(cls, url: HttpUrl) -> HttpUrl:
        if (
            url.scheme != "https"
            or url.username is not None
            or url.password is not None
        ):
            raise ValueError(
                "Expected an HTTPS invoice URL without credentials"
            )
        return url


class InvoiceResponse(BaseModel):
    status: Literal["success"]
    data: InvoiceData


class OperationParams(BaseModel):
    order_number: str | StrictInt | None = None
    source_amount: Amount | None = None
    source_currency: str | None = None


class OperationData(BaseModel):
    id: InvoiceID
    type: Literal["invoice"]
    status: str
    parent_id: InvoiceID | None = None
    child_ids: tuple[InvoiceID, ...] | None = None
    params: OperationParams | None = None
    sum: Amount | None = None
    actual_sum: Amount | None = None


class OperationResponse(BaseModel):
    status: Literal["success"]
    data: OperationData
