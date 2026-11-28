"""Panel schema for one Xray Observatory snapshot."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    NodeObservationOutput,
)

from ...domain.enums.health import XrayOutboundState


class XrayOutboundSampleOutput(BaseOutput):
    tag: str
    status: XrayOutboundState
    delay_milliseconds: int | None
    last_seen_unix_seconds: int | None
    last_try_unix_seconds: int | None


class XrayOutboundObservationOutput(NodeObservationOutput):
    instance_id: str
    observations: list[XrayOutboundSampleOutput] | None
