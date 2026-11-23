"""Typed role and role-scope management contracts."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.core.roles.domain.dtos.records import (
    RoleBatchRead,
    RoleCreate,
    RoleList,
    RoleUpdate,
)
from src.apps.core.roles.domain.dtos.role_scopes import (
    RoleScopeCreate,
    RoleScopeList,
    RoleScopeUpdate,
)
from src.apps.core.roles.domain.models.records import (
    RoleModel,
    RoleScopeModel,
)


class IRoleService(Protocol):
    async def create(self, data: RoleCreate) -> RoleModel: ...
    async def get_by_id(self, id: int) -> RoleModel: ...
    async def find_by_id(self, id: int) -> RoleModel | None: ...
    async def find_by_key(self, key: str) -> RoleModel | None: ...
    async def get_by_ids(self, data: RoleBatchRead) -> Sequence[RoleModel]: ...
    async def list(self, query: RoleList) -> PagedType[RoleModel]: ...
    async def update(self, id: int, data: RoleUpdate) -> RoleModel: ...
    async def remove(self, id: int) -> RoleModel: ...


class IRoleScopeService(Protocol):
    async def create(
        self, role_id: int, data: RoleScopeCreate
    ) -> RoleScopeModel: ...
    async def get(self, role_id: int, scope_id: int) -> RoleScopeModel: ...
    async def find(
        self, role_id: int, scope_id: int
    ) -> RoleScopeModel | None: ...
    async def get_by_scope_ids(
        self, role_id: int, scope_ids: Sequence[int]
    ) -> Sequence[RoleScopeModel]: ...

    async def list(
        self, role_id: int, query: RoleScopeList
    ) -> PagedType[RoleScopeModel]: ...
    async def update(
        self, role_id: int, data: RoleScopeUpdate
    ) -> RoleScopeModel: ...
    async def remove(self, role_id: int, scope_id: int) -> RoleScopeModel: ...
    async def create_batch(
        self, role_id: int, items: Sequence[RoleScopeCreate]
    ) -> Sequence[RoleScopeModel]: ...
    async def update_batch(
        self, role_id: int, items: Sequence[RoleScopeUpdate]
    ) -> Sequence[RoleScopeModel]: ...
