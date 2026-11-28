"""Panel representation of a committed Xray Start operation."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.start import XrayStartReason, XrayStartState


class XrayStartOutput(BaseOutput):
    id: int
    node_id: int
    instance_id: str
    state: XrayStartState
    reason: XrayStartReason | None
    applied_config_sha256: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
