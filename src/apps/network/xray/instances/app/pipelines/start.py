"""Dispatch a committed start between short, independent SQL phases."""

from papilio.errors.exceptions import NotFoundException

from src.apps.network.xray.revisions.domain.results.records import (
    XraySourceFailure,
)

from ...domain.enums.start import XrayStartReason, XrayStartState
from ...domain.results.start import XrayStartOutcome
from ..executions.start import XrayStartExecution
from ..interfaces.start import IXrayStartGateway


class XrayStartPipeline:
    def __init__(
        self, execution: XrayStartExecution, gateway: IXrayStartGateway
    ) -> None:
        self.execution = execution
        self.gateway = gateway

    async def run(self, id: int) -> None:
        """Execute the first delivered request for this operation identity.

        Args:
            id: Persisted operation identity.
        """
        target = await self.execution.claim(id)
        if target is not None:
            try:
                source = (
                    await self.execution.load_source(target.revision_id)
                    if target.revision_id is not None
                    else None
                )
            except NotFoundException:
                source = XraySourceFailure.UNAVAILABLE
            if isinstance(source, XraySourceFailure):
                outcome = XrayStartOutcome(
                    XrayStartState.FAILED, XrayStartReason.REVISION_UNAVAILABLE
                )
            else:
                outcome = await self.gateway.start(
                    target,
                    config_json=source.config_json
                    if source is not None
                    else None,
                )
                if source is not None:
                    outcome = outcome.for_digest(source.config_sha256)
            await self.execution.finish(id, outcome)
