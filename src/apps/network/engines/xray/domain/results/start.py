"""Materialized dispatch target and outcome of a single Start RPC."""

from dataclasses import dataclass
from datetime import datetime

from ..enums.start import XrayStartReason, XrayStartState


@dataclass(frozen=True, slots=True)
class XrayStartTarget:
    node_id: int
    instance_id: str
    address: str
    port: int
    deadline_at: datetime


@dataclass(frozen=True, slots=True)
class XrayStartOutcome:
    state: XrayStartState
    reason: XrayStartReason | None = None
    applied_config_sha256: str | None = None
