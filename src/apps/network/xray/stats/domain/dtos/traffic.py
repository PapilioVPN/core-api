"""Exact counter names accepted by the Node traffic contract."""

from typing import Annotated

from pydantic import AfterValidator, StringConstraints


def _limit_name_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > 4096:
        raise ValueError("A counter name must be at most 4096 UTF-8 bytes")
    return value


type XrayCounterName = Annotated[
    str,
    StringConstraints(min_length=1, max_length=4096),
    AfterValidator(_limit_name_bytes),
]
