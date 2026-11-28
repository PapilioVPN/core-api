"""Dispatch the current Restart and reconcile it before acknowledging."""

from ..executions.rollout import RestartRolloutExecution
from .control import XrayControlPipeline


class RestartRolloutPipeline:
    def __init__(
        self, execution: RestartRolloutExecution, control: XrayControlPipeline
    ) -> None:
        self.execution = execution
        self.control = control

    async def run(self, rollout_id: int, operation_id: int) -> float | None:
        """Recover terminal evidence or execute a still-queued child once."""
        decision = await self.execution.inspect(rollout_id, operation_id)
        if decision.dispatch:
            await self.control.run(operation_id)
            decision = await self.execution.inspect(rollout_id, operation_id)
        retry_after = 1 if decision.dispatch else decision.retry_after
        return retry_after
