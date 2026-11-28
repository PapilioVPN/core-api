"""Typed admission, persistence and dispatch of Xray routing changes."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from ...domain.dtos.mutations import RoutingIntent
from ...domain.enums.operation import RoutingPayloadFailure
from ...domain.models.operation import XrayRoutingOperationModel
from ...domain.results.operation import (
    RoutingOutcome,
    RoutingPayload,
    RoutingTarget,
)


class IRoutingPayloadCodec(Protocol):
    async def seal(
        self, intent: RoutingIntent
    ) -> RoutingPayload | RoutingPayloadFailure: ...

    async def open(
        self, payload: RoutingPayload
    ) -> RoutingIntent | RoutingPayloadFailure: ...


class IXrayRoutingGateway(Protocol):
    async def mutate(
        self, target: RoutingTarget, intent: RoutingIntent
    ) -> RoutingOutcome: ...


class IXrayRoutingOperationRepository(Protocol):
    async def insert(
        self, operation: XrayRoutingOperationModel
    ) -> XrayRoutingOperationModel | None: ...

    async def find_request(
        self, node_id: int, instance_id: str, key: UUID
    ) -> XrayRoutingOperationModel | None: ...

    async def find_operation(
        self, node_id: int, instance_id: str, id: int
    ) -> XrayRoutingOperationModel | None: ...

    async def expire(
        self, node_id: int, instance_id: str, now: datetime
    ) -> None: ...

    async def claim(
        self, id: int, *, now: datetime, deadline: datetime
    ) -> XrayRoutingOperationModel | None: ...

    async def finish(
        self, id: int, outcome: RoutingOutcome, *, now: datetime
    ) -> None: ...


class IXrayRoutingOperations(Protocol):
    async def submit(
        self, node_id: int, instance_id: str, key: UUID, intent: RoutingIntent
    ) -> XrayRoutingOperationModel | RoutingPayloadFailure: ...

    async def get(
        self, node_id: int, instance_id: str, id: int
    ) -> XrayRoutingOperationModel: ...
