"""An Xray observation distinct from inability to read the instance."""

from dataclasses import dataclass
from datetime import datetime

from ..enums.status import XrayInstanceState, XrayStatusCode


@dataclass(frozen=True, slots=True)
class XrayInstanceObservation:
    state: XrayInstanceState
    xray_version: str | None
    node_version: str | None
    applied_config_sha256: str | None


@dataclass(frozen=True, slots=True)
class XrayStatusResult:
    status: XrayStatusCode
    instance: XrayInstanceObservation | None = None
    received_at: datetime | None = None
