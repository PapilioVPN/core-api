"""Report the ordered steps and existing Restart evidence for the Panel."""

from datetime import datetime
from typing import Literal, Self

from papilio.schemas.outputs import BaseOutput
from papilio.utils.dates import utc_now

from ...domain.enums.rollout import RestartRolloutReason, RestartRolloutState
from ...domain.enums.start import XrayStartState
from ...domain.results.rollout import RestartRolloutSnapshot
from .restart import XrayRestartOutput


class RestartRolloutStepOutput(BaseOutput):
    position: int
    node_id: int
    instance_id: str
    state: XrayStartState | Literal["pending", "blocked"]
    operation: XrayRestartOutput | None


class RestartRolloutOutput(BaseOutput):
    id: int
    revision_id: int
    config_sha256: str
    position: int
    state: RestartRolloutState
    reason: RestartRolloutReason | None
    created_at: datetime | None
    finished_at: datetime | None
    steps: list[RestartRolloutStepOutput]

    @classmethod
    def from_snapshot(cls, snapshot: RestartRolloutSnapshot) -> Self:
        """Keep awaiting targets distinct from a dispatched or blocked step."""
        plan = snapshot.rollout
        now = utc_now()
        steps = []
        for row in snapshot.steps:
            target = row.target
            operation = (
                row.operation.observed_at(now)
                if row.operation is not None
                else None
            )
            if operation is not None:
                state = operation.state
            elif (
                target.position == plan.position
                and plan.state is RestartRolloutState.HALTED
            ):
                state = "blocked"
            else:
                state = "pending"
            steps.append(
                RestartRolloutStepOutput(
                    position=target.position,
                    node_id=target.node_id,
                    instance_id=target.instance_id,
                    state=state,
                    operation=XrayRestartOutput.from_obj(operation)
                    if operation is not None
                    else None,
                )
            )
        return cls(
            id=plan.id,
            revision_id=plan.revision_id,
            config_sha256=plan.config_sha256,
            position=plan.position,
            state=plan.state,
            reason=plan.reason,
            created_at=plan.created_at,
            finished_at=plan.finished_at,
            steps=steps,
        )
