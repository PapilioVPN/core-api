"""Panel schema for Hysteria validation evidence."""

from typing import Literal

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.routers.schemas.observation import (
    NodeObservationOutput,
)

from ...domain.enums.dry_run import HysteriaIssue


class HysteriaValidationOutput(BaseOutput):
    valid: bool
    issue: HysteriaIssue | None
    scope: Literal["node_preflight"]


class HysteriaValidationObservationOutput(NodeObservationOutput):
    instance_id: str
    validation: HysteriaValidationOutput | None
