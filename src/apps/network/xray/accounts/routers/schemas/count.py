"""Expose aggregate evidence without account names or credentials."""

from src.apps.network.nodes.observations.routers.schemas.observation import (
    NodeObservationOutput,
)


class XrayVlessCountOutput(NodeObservationOutput):
    instance_id: str
    inbound_tag: str
    count: int | None
