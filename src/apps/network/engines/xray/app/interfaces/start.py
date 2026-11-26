"""Typed admission, persistence and transport contracts for Xray Start."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from ...domain.models.start import XrayStartModel
from ...domain.results.start import XrayStartOutcome, XrayStartTarget


class IXrayStartGateway(Protocol):
    async def start(self, target: XrayStartTarget) -> XrayStartOutcome: ...


class IXrayStartRepository(Protocol):
    async def insert(
        self, operation: XrayStartModel
    ) -> XrayStartModel | None: ...

    async def find_request(
        self, node_id: int, instance_id: str, request_key: UUID
    ) -> XrayStartModel | None: ...

    async def find_operation(
        self, node_id: int, instance_id: str, id: int
    ) -> XrayStartModel | None: ...

    async def expire(
        self, node_id: int, instance_id: str, now: datetime
    ) -> None: ...

    async def claim(
        self, id: int, *, now: datetime, deadline: datetime
    ) -> XrayStartModel | None: ...

    async def finish(
        self, id: int, outcome: XrayStartOutcome, *, now: datetime
    ) -> None: ...


class IXrayStartCommand(Protocol):
    async def submit(
        self, node_id: int, instance_id: str, request_key: UUID
    ) -> XrayStartModel: ...


class IXrayStartQuery(Protocol):
    async def get(
        self, node_id: int, instance_id: str, id: int
    ) -> XrayStartModel: ...
