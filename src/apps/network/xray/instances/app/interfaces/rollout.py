"""Storage, ordered rollout admission and durable progress contracts."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from ...domain.dtos.rollout import RestartRolloutInput
from ...domain.enums.rollout import RestartRolloutReason, RestartRolloutState
from ...domain.models.rollout import (
    XrayRestartRolloutModel,
    XrayRestartRolloutTargetModel,
)
from ...domain.models.start import XrayStartModel
from ...domain.results.rollout import (
    RestartRolloutDecision,
    RestartRolloutSnapshot,
)


class IRestartRolloutRepository(Protocol):
    async def find_request(
        self, key: UUID
    ) -> XrayRestartRolloutModel | None: ...

    async def insert(
        self, plan: XrayRestartRolloutModel
    ) -> XrayRestartRolloutModel | None: ...

    async def add_targets(
        self, targets: tuple[XrayRestartRolloutTargetModel, ...]
    ) -> None: ...

    async def lock(self, id: int) -> XrayRestartRolloutModel | None: ...

    async def target(
        self, id: int, position: int
    ) -> XrayRestartRolloutTargetModel | None: ...

    async def lock_operation(self, id: int) -> XrayStartModel | None: ...

    async def attach(self, target_id: int, operation_id: int) -> None: ...

    async def progress(
        self,
        id: int,
        *,
        position: int,
        state: RestartRolloutState,
        reason: RestartRolloutReason | None,
        finished_at: datetime | None,
    ) -> None: ...


class IRestartRolloutReader(Protocol):
    async def read(
        self, revision_id: int, id: int
    ) -> RestartRolloutSnapshot | None: ...


class IRestartRolloutQuery(Protocol):
    async def get(
        self, revision_id: int, id: int
    ) -> RestartRolloutSnapshot: ...


class IRestartRolloutAdmission(Protocol):
    async def submit(
        self, revision_id: int, request_key: UUID, data: RestartRolloutInput
    ) -> RestartRolloutSnapshot: ...


class IRestartRolloutProgress(Protocol):
    async def inspect(
        self, rollout_id: int, operation_id: int
    ) -> RestartRolloutDecision: ...
