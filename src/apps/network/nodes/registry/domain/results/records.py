"""Materialized registry data needed to select management connections."""

from dataclasses import dataclass, field

from ..dtos.records import DEFAULT_TIMEOUT
from ..enums.state import NodeStateStatus


@dataclass(frozen=True, slots=True)
class NodeEndpoint:
    id: int
    address: str
    port: int
    is_enabled: bool
    connection_revision: int = 1
    api_key_ciphertext: str | None = field(default=None, repr=False)
    ca_pem: str | None = field(default=None, repr=False)
    default_timeout: int = DEFAULT_TIMEOUT


@dataclass(frozen=True, slots=True)
class NodeChoice:
    id: int
    name: str
    is_enabled: bool


@dataclass(frozen=True, slots=True)
class NodeSelection:
    items: tuple[NodeChoice, ...]
    next_before_id: int | None


@dataclass(frozen=True, slots=True)
class NodeStateResult:
    node_id: int
    status: NodeStateStatus
    is_enabled: bool | None
