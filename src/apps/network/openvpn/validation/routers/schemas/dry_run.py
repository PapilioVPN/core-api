"""Panel schema for OpenVPN validation evidence."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    NodeObservationOutput,
)

from ...domain.enums.dry_run import OpenVPNIssue


class OpenVPNValidationOutput(BaseOutput):
    valid: bool
    issue: OpenVPNIssue | None
    line: int | None


class OpenVPNValidationObservationOutput(NodeObservationOutput):
    instance_id: str
    validation: OpenVPNValidationOutput | None
