"""Typed role reads including their stored scope permissions."""

from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.core.roles.domain.dtos.records import (
    RoleBatchRead,
    RoleList,
)
from src.apps.core.roles.domain.results.records import (
    RoleAccess,
    RoleDetailsResult,
)


class IRoleQuery(Protocol):
    async def get_by_id(self, id: int) -> RoleDetailsResult: ...
    async def find_access(self, id: int) -> RoleAccess | None: ...
    async def get_by_ids(
        self, data: RoleBatchRead
    ) -> list[RoleDetailsResult]: ...
    async def list(self, query: RoleList) -> PagedType[RoleDetailsResult]: ...
