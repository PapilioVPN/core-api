"""Text selectors in the pinned routing contract."""

from typing import Annotated

from pydantic import AfterValidator, StringConstraints


def _limit_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > 4096:
        raise ValueError("Routing text must be at most 4096 UTF-8 bytes")
    return value


type RoutingText = Annotated[
    str, StringConstraints(max_length=4096), AfterValidator(_limit_bytes)
]
type RoutingTag = Annotated[RoutingText, StringConstraints(min_length=1)]
