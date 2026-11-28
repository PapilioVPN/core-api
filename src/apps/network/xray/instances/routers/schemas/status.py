"""Panel output separating an engine state from a status-read outcome."""

from datetime import datetime
from typing import Self

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.status import XrayInstanceState, XrayStatusCode
from ...domain.results.status import XrayStatusResult


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

    @classmethod
    def from_result(
        cls, node_id: int, instance_id: str, result: XrayStatusResult
    ) -> Self:
        """Map one outcome consistently in both scalar and fleet views."""
        return cls(
            node_id=node_id,
            instance_id=instance_id,
            status=result.status,
            instance=(
                XrayInstanceObservationOutput.from_obj(result.instance)
                if result.instance is not None
                else None
            ),
            received_at=result.received_at,
        )
