"""Validate an exact native Xray inbound tag without normalizing it."""

from typing import Annotated
from unicodedata import category

from pydantic import AfterValidator, StringConstraints


def _valid_tag(value: str) -> str:
    if len(value.encode()) > 1024 or any(
        category(char) == "Cc" for char in value
    ):
        raise ValueError(
            "An inbound tag must fit 1024 UTF-8 bytes without controls"
        )
    return value


type XrayInboundTag = Annotated[
    str,
    StringConstraints(min_length=1, max_length=1024),
    AfterValidator(_valid_tag),
]
