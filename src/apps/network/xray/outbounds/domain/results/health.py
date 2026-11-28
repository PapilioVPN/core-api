"""Xray Observatory samples in native time units."""

from dataclasses import dataclass

from ..enums.health import XrayOutboundState


@dataclass(frozen=True, slots=True)
class XrayOutboundSample:
    tag: str
    status: XrayOutboundState
    delay_milliseconds: int | None
    last_seen_unix_seconds: int | None
    last_try_unix_seconds: int | None
