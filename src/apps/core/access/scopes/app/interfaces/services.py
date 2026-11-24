"""Typed scope management capabilities."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.core.access.scopes.domain.dtos.records import (
    ScopeCreate,
    ScopeList,
    ScopeUpdate,
)
from src.apps.core.access.scopes.domain.models.records import ScopeModel


class IScopeService(Protocol):
    async def create(self, data: ScopeCreate) -> ScopeModel: ...

    async def get_by_id(self, id: int) -> ScopeModel: ...

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[ScopeModel]: ...

    async def find_by_id(self, id: int) -> ScopeModel | None: ...

    async def find_by_key(self, key: str) -> ScopeModel | None: ...

    async def list(self, query: ScopeList) -> PagedType[ScopeModel]: ...

    async def update(self, id: int, data: ScopeUpdate) -> ScopeModel: ...

    async def remove(self, id: int) -> ScopeModel: ...
