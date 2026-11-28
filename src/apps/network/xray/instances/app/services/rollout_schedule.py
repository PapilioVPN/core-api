"""Create one normal Restart operation and wake only that rollout target."""

from datetime import datetime
from uuid import uuid4

from papilio_tasks.apps.outbox import OutboxWriter

from ...domain.enums.rollout import RestartRolloutReason, RestartRolloutState
from ...domain.enums.start import XrayExecutionAction
from ...domain.events.rollout import XrayRestartRolloutRequested
from ...domain.models.rollout import (
    XrayRestartRolloutModel,
    XrayRestartRolloutTargetModel,
)
from ...domain.models.start import XrayStartModel
from ...infra.broker.publishers import rollout_requested
from ..interfaces.rollout import IRestartRolloutRepository
from ..interfaces.start import IXrayStartRepository


class RestartRolloutSchedule:
    def __init__(
        self,
        rollouts: IRestartRolloutRepository,
        starts: IXrayStartRepository,
        outbox: OutboxWriter,
    ) -> None:
        self.rollouts = rollouts
        self.starts = starts
        self.outbox = outbox

    async def enqueue(
        self,
        plan: XrayRestartRolloutModel,
        target: XrayRestartRolloutTargetModel,
        now: datetime,
    ) -> None:
        """Link one accepted target and its event in the caller's commit."""
        await self.starts.expire(target.node_id, target.instance_id, now)
        operation = await self.starts.insert(
            XrayStartModel(
                node_id=target.node_id,
                instance_id=target.instance_id,
                request_key=uuid4(),
                address=target.address,
                port=target.port,
                revision_id=plan.revision_id,
                action=XrayExecutionAction.RESTART,
            )
        )
        if operation is None:
            await self.rollouts.progress(
                plan.id,
                position=target.position,
                state=RestartRolloutState.HALTED,
                reason=RestartRolloutReason.ACTIVE_OPERATION,
                finished_at=now,
            )
        else:
            await self.rollouts.attach(target.id, operation.id)
            await self.rollouts.progress(
                plan.id,
                position=target.position,
                state=RestartRolloutState.RUNNING,
                reason=None,
                finished_at=None,
            )
            await self.outbox.append(
                rollout_requested,
                XrayRestartRolloutRequested(
                    rollout_id=plan.id,
                    operation_id=operation.id,
                ),
            )
