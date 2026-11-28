"""Panel schema for WireGuard validation evidence."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    NodeObservationOutput,
)

from ...domain.enums.dry_run import WireGuardIssue


class WireGuardValidationOutput(BaseOutput):
    valid: bool
    issue: WireGuardIssue | None


class WireGuardValidationObservationOutput(NodeObservationOutput):
    name: str
    validation: WireGuardValidationOutput | None
