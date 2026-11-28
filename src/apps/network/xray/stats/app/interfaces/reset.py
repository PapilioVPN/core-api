"""Contracts for technical reset admission, delivery and evidence."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from ...domain.models.reset import XrayTrafficResetModel
from ...domain.results.reset import ResetOutcome, ResetSelection, ResetTarget


class IXrayTrafficResets(Protocol):
    async def submit(
        self,
        node_id: int,
        instance_id: str,
        key: UUID,
        selection: ResetSelection,
    ) -> XrayTrafficResetModel: ...

    async def get(
        self, node_id: int, instance_id: str, id: int
    ) -> XrayTrafficResetModel: ...


class IXrayResetGateway(Protocol):
    async def reset(self, target: ResetTarget) -> ResetOutcome: ...


class IXrayResetRepository(Protocol):
    async def insert(
        self, operation: XrayTrafficResetModel
    ) -> XrayTrafficResetModel | None: ...

    async def find_request(
        self, node_id: int, instance_id: str, key: UUID
    ) -> XrayTrafficResetModel | None: ...

    async def find_operation(
        self, node_id: int, instance_id: str, id: int
    ) -> XrayTrafficResetModel | None: ...

    async def expire(
        self, node_id: int, instance_id: str, now: datetime
    ) -> None: ...

    async def claim(
        self, id: int, *, now: datetime, deadline: datetime
    ) -> XrayTrafficResetModel | None: ...

    async def finish(
        self, id: int, outcome: ResetOutcome, *, now: datetime
    ) -> None: ...
