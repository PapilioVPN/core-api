"""The portion of a Plisio response needed for hosted payment."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class InvoiceData(BaseModel):
    txn_id: Annotated[
        str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    ]
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
