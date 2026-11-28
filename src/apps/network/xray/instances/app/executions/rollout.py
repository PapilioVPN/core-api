"""Bind each rollout inspection to its own native database scope."""

from dishka import AsyncContainer
from papilio.infra.scopes import Inject, request_scoped

from ...domain.results.rollout import RestartRolloutDecision
from ..interfaces.rollout import IRestartRolloutProgress


class RestartRolloutExecution:
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    @request_scoped
    async def inspect(
        self,
        rollout_id: int,
        operation_id: int,
        *,
        progress: IRestartRolloutProgress = Inject(),
    ) -> RestartRolloutDecision:
        decision = await progress.inspect(rollout_id, operation_id)
        return decision
