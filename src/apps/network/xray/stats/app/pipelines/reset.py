"""Dispatch one claimed counter reset with no automatic repetition."""

from ..executions.reset import XrayResetExecution
from ..interfaces.reset import IXrayResetGateway


class XrayResetPipeline:
    def __init__(
        self, execution: XrayResetExecution, gateway: IXrayResetGateway
    ) -> None:
        self.execution = execution
        self.gateway = gateway

    async def run(self, id: int) -> None:
        """Perform the network call between the two short SQL phases."""
        target = await self.execution.claim(id)
        if target is not None:
            outcome = await self.gateway.reset(target)
            await self.execution.finish(id, outcome)
