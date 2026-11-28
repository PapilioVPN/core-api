"""Persistence contract for the managed node registry."""

from collections.abc import Mapping
from typing import Any, Protocol

from papilio.schemas.results import PagedType

from ...domain.models.records import NodeModel


class INodeRepository(Protocol):
    async def create(self, data: NodeModel) -> NodeModel: ...

    async def get_by_id(self, id: int) -> NodeModel | None: ...

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None,
        is_enabled: bool | None,
    ) -> PagedType[NodeModel]: ...

    async def update_by_id(
        self, id: int, changes: Mapping[str, Any]
    ) -> NodeModel | None: ...

    async def lock_enabled(self, ids: tuple[int, ...]) -> dict[int, bool]: ...

    async def set_enabled(
        self, ids: tuple[int, ...], is_enabled: bool
    ) -> None: ...
