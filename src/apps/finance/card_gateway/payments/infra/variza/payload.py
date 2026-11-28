"""Decode Variza's v1 payment-link response."""

from pydantic import AwareDatetime, BaseModel, Field, HttpUrl, StrictInt

RIALS_PER_TOMAN = 10


class LinkPayload(BaseModel):
    slug: str = Field(min_length=1)
    pay_url: HttpUrl
    amount: StrictInt
    expires_at: AwareDatetime | None
