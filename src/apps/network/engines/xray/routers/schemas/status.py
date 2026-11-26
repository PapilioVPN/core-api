"""Panel output separating an engine state from a status-read outcome."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.status import XrayInstanceState, XrayStatusCode


class XrayInstanceObservationOutput(BaseOutput):
    state: XrayInstanceState
    xray_version: str | None
    node_version: str | None
    applied_config_sha256: str | None


class XrayStatusOutput(BaseOutput):
    node_id: int
    instance_id: str
    status: XrayStatusCode
    instance: XrayInstanceObservationOutput | None
    received_at: datetime | None
