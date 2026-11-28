"""Panel evidence for live Xray traffic by scope."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.routers.schemas.observation import (
    NodeObservationOutput,
)

from ...domain.enums.traffic import XrayTrafficScope


class XrayTrafficOutput(BaseOutput):
    name: str
    uplink_bytes: int | None
    downlink_bytes: int | None


class XrayTrafficCounterOutput(NodeObservationOutput):
    instance_id: str
    scope: XrayTrafficScope
    counter: XrayTrafficOutput | None


class XrayTrafficListOutput(NodeObservationOutput):
    instance_id: str
    scope: XrayTrafficScope
    entries: list[XrayTrafficOutput] | None
