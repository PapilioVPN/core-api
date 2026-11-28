"""Fence one rollout cursor and advance only on confirmed restart evidence."""

from datetime import datetime

from papilio.infra.db.tools.decorators import transactional
from papilio.utils.dates import utc_now

from ...domain.enums.rollout import (
    RestartRolloutDelivery,
    RestartRolloutReason,
    RestartRolloutState,
)
from ...domain.enums.start import (
    XrayExecutionAction,
    XrayStartReason,
    XrayStartState,
)
from ...domain.models.rollout import XrayRestartRolloutModel
from ...domain.models.start import XrayStartModel
from ...domain.results.rollout import (
    RestartRolloutDecision,
    RetryRestartRolloutDelivery,
)
from ..interfaces.rollout import IRestartRolloutRepository
from ..interfaces.start import IXrayStartRepository
from .rollout_schedule import RestartRolloutSchedule


class RestartRolloutProgress:
    def __init__(
        self,
        rollouts: IRestartRolloutRepository,
        starts: IXrayStartRepository,
        schedule: RestartRolloutSchedule,
    ) -> None:
        self.rollouts = rollouts
        self.starts = starts
        self.schedule = schedule

    @transactional
    async def inspect(
        self, rollout_id: int, operation_id: int
    ) -> RestartRolloutDecision:
        """Consult durable state before dispatch or acknowledgement."""
        plan = await self.rollouts.lock(rollout_id)
        decision: RestartRolloutDecision = RestartRolloutDelivery.SETTLED
        if plan is not None and plan.state is RestartRolloutState.RUNNING:
            target = await self.rollouts.target(plan.id, plan.position)
            if target is not None and target.operation_id == operation_id:
                operation = await self.rollouts.lock_operation(operation_id)
                if (
                    operation is not None
                    and operation.action is XrayExecutionAction.RESTART
                    and operation.revision_id == plan.revision_id
                    and (operation.node_id, operation.instance_id)
                    == (target.node_id, target.instance_id)
                ):
                    decision = await self._inspect_operation(
                        plan, operation, utc_now()
                    )
                else:
                    await self._halt(
                        plan, RestartRolloutReason.TARGET_UNKNOWN, utc_now()
                    )
        return decision

    async def _inspect_operation(
        self,
        plan: XrayRestartRolloutModel,
        operation: XrayStartModel,
        now: datetime,
    ) -> RestartRolloutDecision:
        decision: RestartRolloutDecision = RestartRolloutDelivery.SETTLED
        if operation.state is XrayStartState.QUEUED:
            decision = RestartRolloutDelivery.DISPATCH
        elif operation.state is XrayStartState.RUNNING:
            deadline = operation.deadline_at
            if deadline is not None and deadline > now:
                decision = RetryRestartRolloutDelivery(
                    (deadline - now).total_seconds()
                )
            else:
                # A lost reply is not authority to issue Stop again.
                await self.starts.expire(
                    operation.node_id, operation.instance_id, now
                )
                await self._halt(
                    plan, RestartRolloutReason.TARGET_UNKNOWN, now
                )
        elif (
            operation.state is XrayStartState.SUCCEEDED
            and operation.stopped_at is not None
            and operation.applied_config_sha256 == plan.config_sha256
        ):
            target = await self.rollouts.target(plan.id, plan.position + 1)
            if target is None:
                await self.rollouts.progress(
                    plan.id,
                    position=plan.position,
                    state=RestartRolloutState.SUCCEEDED,
                    reason=None,
                    finished_at=now,
                )
            else:
                await self.schedule.enqueue(plan, target, now)
        else:
            if operation.reason is XrayStartReason.DIGEST_MISMATCH or (
                operation.state is XrayStartState.SUCCEEDED
                and operation.applied_config_sha256 != plan.config_sha256
            ):
                reason = RestartRolloutReason.DIGEST_MISMATCH
            elif operation.state is XrayStartState.FAILED:
                reason = RestartRolloutReason.TARGET_FAILED
            else:
                reason = RestartRolloutReason.TARGET_UNKNOWN
            await self._halt(plan, reason, now)
        return decision

    async def _halt(
        self,
        plan: XrayRestartRolloutModel,
        reason: RestartRolloutReason,
        now: datetime,
    ) -> None:
        await self.rollouts.progress(
            plan.id,
            position=plan.position,
            state=RestartRolloutState.HALTED,
            reason=reason,
            finished_at=now,
        )
