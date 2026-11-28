"""Materialized registry data needed to select management connections."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NodeEndpoint:
    id: int
    address: str
    port: int
    is_enabled: bool
