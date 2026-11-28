"""Typed admission, persistence and transport contracts for Xray Start."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from ...domain.dtos.identity import (
    XrayExecutionKey,
    XrayExecutionRequestKey,
    XrayExecutionTrackingKey,
)
from ...domain.enums.start import XrayExecutionAction
from ...domain.models.start import XrayStartModel
from ...domain.results.start import XrayStartOutcome, XrayStartTarget


class IXrayStartGateway(Protocol):
    async def start(
        self, target: XrayStartTarget, config_json: bytes | None = None
    ) -> XrayStartOutcome: ...

    async def stop(self, target: XrayStartTarget) -> XrayStartOutcome: ...


class IXrayStartRepository(Protocol):
    async def insert(
        self, operation: XrayStartModel
    ) -> XrayStartModel | None: ...

    async def insert_many(
        self, operations: tuple[XrayStartModel, ...]
    ) -> tuple[XrayStartModel, ...]: ...

    async def find_request(
        self, node_id: int, instance_id: str, request_key: UUID
    ) -> XrayStartModel | None: ...

    async def find_requests(
        self, keys: tuple[XrayExecutionRequestKey, ...]
    ) -> tuple[XrayStartModel, ...]: ...

    async def find_operation(
        self,
        node_id: int,
        instance_id: str,
        id: int,
        *,
        revision_id: int | None,
        action: XrayExecutionAction,
    ) -> XrayStartModel | None: ...

    async def find_operations(
        self,
        keys: tuple[XrayExecutionTrackingKey, ...],
        *,
        action: XrayExecutionAction,
        revision_id: int | None,
    ) -> tuple[XrayStartModel, ...]: ...

    async def expire(
        self, node_id: int, instance_id: str, now: datetime
    ) -> None: ...

    async def expire_many(
        self, keys: tuple[XrayExecutionKey, ...], now: datetime
    ) -> None: ...

    async def claim(
        self,
        id: int,
        *,
        now: datetime,
        deadline: datetime,
        actions: tuple[XrayExecutionAction, ...],
    ) -> XrayStartModel | None: ...

    async def record_stop(self, id: int, *, now: datetime) -> bool: ...

    async def finish(
        self, id: int, outcome: XrayStartOutcome, *, now: datetime
    ) -> None: ...


class IXrayStartAdmission(Protocol):
    async def submit(
        self,
        node_id: int,
        instance_id: str,
        request_key: UUID,
        *,
        revision_id: int | None = None,
        action: XrayExecutionAction = XrayExecutionAction.START,
    ) -> XrayStartModel: ...


class IXrayStartQuery(Protocol):
    async def get(
        self,
        node_id: int,
        instance_id: str,
        id: int,
        *,
        revision_id: int | None = None,
        action: XrayExecutionAction = XrayExecutionAction.START,
    ) -> XrayStartModel: ...
