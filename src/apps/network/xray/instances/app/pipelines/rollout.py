"""Dispatch the current Restart and reconcile it before acknowledging."""

from ...domain.enums.rollout import RestartRolloutDelivery
from ...domain.results.rollout import RetryRestartRolloutDelivery
from ..executions.rollout import RestartRolloutExecution
from .control import XrayControlPipeline


class RestartRolloutPipeline:
    def __init__(
        self, execution: RestartRolloutExecution, control: XrayControlPipeline
    ) -> None:
        self.execution = execution
        self.control = control

    async def run(
        self, rollout_id: int, operation_id: int
    ) -> RetryRestartRolloutDelivery | None:
        """Recover terminal evidence or execute a still-queued child once."""
        decision = await self.execution.inspect(rollout_id, operation_id)
        if decision is RestartRolloutDelivery.DISPATCH:
            await self.control.run(operation_id)
            decision = await self.execution.inspect(rollout_id, operation_id)
        retry = None
        if isinstance(decision, RetryRestartRolloutDelivery):
            retry = decision
        elif decision is RestartRolloutDelivery.DISPATCH:
            retry = RetryRestartRolloutDelivery(1)
        return retry
