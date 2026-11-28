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


@dataclass(frozen=True, slots=True)
class XrayLogEvent:
    line: XrayLogLine | None = None
    end: XrayLogEnd | None = None


@dataclass(frozen=True, slots=True)
class XrayLogFeed:
    events: AsyncIterator[XrayLogEvent] | None = None
    end: XrayLogEnd | None = None
