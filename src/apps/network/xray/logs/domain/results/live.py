"""Materialized live-log observations independent of the wire format."""

from collections.abc import AsyncIterator
from dataclasses import dataclass

from ..enums.live import XrayLogEnd, XrayLogSource


@dataclass(frozen=True, slots=True)
class XrayLogLine:
    execution: int
    sequence: int
    received_unix_nano: int
    source: XrayLogSource
    message: str
    truncated: bool
    encoding_replaced: bool
    missed_before: int | None


type XrayLogFeed = AsyncIterator[XrayLogLine | XrayLogEnd]
