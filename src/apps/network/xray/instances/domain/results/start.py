"""Materialized dispatch target and outcome of a single Start RPC."""

from dataclasses import dataclass
from datetime import datetime

from ..enums.start import XrayExecutionAction, XrayStartReason, XrayStartState


@dataclass(frozen=True, slots=True)
class XrayStartTarget:
    node_id: int
    instance_id: str
    address: str
    port: int
    deadline_at: datetime
    revision_id: int | None = None
    action: XrayExecutionAction = XrayExecutionAction.START


@dataclass(frozen=True, slots=True)
class XrayStartOutcome:
    state: XrayStartState
    reason: XrayStartReason | None = None
    applied_config_sha256: str | None = None

    def for_digest(self, expected: str) -> "XrayStartOutcome":
        """Preserve a different observed digest as unconfirmed application."""
        outcome = self
        if self.state is XrayStartState.SUCCEEDED and (
            self.applied_config_sha256 != expected
        ):
            outcome = XrayStartOutcome(
                XrayStartState.UNKNOWN,
                XrayStartReason.DIGEST_MISMATCH,
                self.applied_config_sha256,
            )
        return outcome
