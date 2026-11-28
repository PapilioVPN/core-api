"""OpenVPN management session count and its execution and observation time."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OpenVPNSessionCount:
    execution_id: str
    observed_at_unix_seconds: int
    session_count: int
