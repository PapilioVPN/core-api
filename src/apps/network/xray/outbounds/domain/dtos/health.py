"""Outbound tag selectors accepted by Node."""

from typing import Annotated

from pydantic import AfterValidator, StringConstraints


def _limit_tag_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > 4096:
        raise ValueError("An outbound tag must be at most 4096 UTF-8 bytes")
    return value


type XrayOutboundTag = Annotated[
    str,
    StringConstraints(min_length=1, max_length=4096),
    AfterValidator(_limit_tag_bytes),
]
