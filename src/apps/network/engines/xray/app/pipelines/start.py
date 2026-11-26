"""Dispatch a committed start between short, independent SQL phases."""

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
            outcome = await self.gateway.start(target)
            await self.execution.finish(id, outcome)
