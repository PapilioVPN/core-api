"""Native role-scope inputs with immutable assignment identities."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType
from pydantic import Field

from src.apps.core.roles.domain.types.permissions import PermissionsType


class RoleScopeCreate(BaseDTO):
    scope_id: IdType
    permissions: PermissionsType


class RoleScopeUpdate(BaseDTO):
    scope_id: IdType
    permissions: PermissionsType


class RoleScopeList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    scope_id: IdType | None = None


class RoleScopeBatchCreate(BaseDTO):
    items: list[RoleScopeCreate] = Field(min_length=1, max_length=100)


class RoleScopeBatchUpdate(BaseDTO):
    items: list[RoleScopeUpdate] = Field(min_length=1, max_length=100)
