"""Role removal and scope assignment contracts."""

from typing import Protocol

from papilio.errors.exceptions import ValidationException
from papilio.schemas.results import BatchResultType

from src.apps.core.access.roles.domain.dtos.role_scopes import (
    RoleScopeBatchCreate,
    RoleScopeBatchUpdate,
    RoleScopeCreate,
    RoleScopeUpdate,
)
from src.apps.core.access.roles.domain.models.records import (
    RoleModel,
    RoleScopeModel,
)


class IRoleRemoveCommand(Protocol):
    async def remove(self, id: int) -> RoleModel: ...


class IRoleScopeCreateCommand(Protocol):
    async def create(
        self, role_id: int, data: RoleScopeCreate, *, actor_id: int
    ) -> RoleScopeModel: ...


class IRoleScopeUpdateCommand(Protocol):
    async def update(
        self, role_id: int, data: RoleScopeUpdate, *, actor_id: int
    ) -> RoleScopeModel: ...


class IRoleScopeRemoveCommand(Protocol):
    async def remove(
        self, role_id: int, scope_id: int, *, actor_id: int
    ) -> RoleScopeModel: ...


class IRoleScopeBatchCreateCommand(Protocol):
    async def create_batch(
        self, role_id: int, data: RoleScopeBatchCreate, *, actor_id: int
    ) -> BatchResultType[RoleScopeModel, ValidationException]: ...


class IRoleScopeBatchUpdateCommand(Protocol):
    async def update_batch(
        self, role_id: int, data: RoleScopeBatchUpdate, *, actor_id: int
    ) -> BatchResultType[RoleScopeModel, ValidationException]: ...
