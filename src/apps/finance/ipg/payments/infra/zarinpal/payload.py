"""Parse the result of a ZarinPal v4 payment request."""

from typing import Annotated

from pydantic import BaseModel, Field, StrictInt, StringConstraints

type Authority = Annotated[
    str,
    StringConstraints(strict=True, pattern=r"^[A-Za-z0-9]{36}$"),
]


class LinkData(BaseModel):
    code: StrictInt
    authority: Authority | None = None


class ErrorData(BaseModel):
    code: StrictInt


type Empty = Annotated[list[object], Field(max_length=0)]


class LinkPayload(BaseModel):
    data: LinkData | Empty | None = None
    errors: ErrorData | Empty | None = None
