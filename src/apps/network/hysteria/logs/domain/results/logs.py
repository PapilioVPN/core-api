"""Redacted Hysteria events for the selected execution."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HysteriaLogEvent:
    execution: int
    sequence: int
    received_unix_nano: int
    event: str
