"""Materialized live-log observations independent of the wire format."""

from dataclasses import dataclass

from ..enums.live import XrayLogSource


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
