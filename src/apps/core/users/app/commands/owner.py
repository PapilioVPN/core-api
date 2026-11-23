"""Create the first owner and its permissions in one native transaction."""

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional

from src.apps.core.auth.domain.enums.permissions import AdminPermission
from src.apps.core.roles.app.interfaces.services import (
    IRoleScopeService,
    IRoleService,
)
from src.apps.core.roles.domain.dtos.records import RoleCreate
from src.apps.core.roles.domain.dtos.role_scopes import RoleScopeCreate
from src.apps.core.scopes.app.interfaces.services import IScopeService
from src.apps.core.scopes.domain.dtos.records import ScopeCreate
from src.apps.core.users.app.interfaces.commands import IUserCreateCommand
from src.apps.core.users.domain.dtos.owner import OwnerCreate
from src.apps.core.users.domain.dtos.records import UserCreate
from src.apps.core.users.domain.models.records import UserModel


class OwnerCommand:
    def __init__(
        self,
        roles: IRoleService,
        scopes: IScopeService,
        grants: IRoleScopeService,
        users: IUserCreateCommand,
    ) -> None:
        """Bind the actual access and user owners in the same request."""
        self.roles = roles
        self.scopes = scopes
        self.grants = grants
        self.users = users

    @transactional
    async def create(self, data: OwnerCreate) -> UserModel:
        """Install the first owner's account, role and initial grants.

        Args:
            data: Validated local setup input with a private password.

        Returns:
            The saved owner account. Concurrent setup shares the role key's
            uniqueness constraint and the same rollback boundary.
        """
        if await self.roles.find_by_key("owner") is not None:
            raise ConflictException(
                "Owner already initialized", "owner_exists", {"key": "owner"}
            )
        role = await self.roles.create(
            RoleCreate(key="owner", title="Super Admin")
        )
        access = await self.scopes.create(
            ScopeCreate(key="access", title="Access")
        )
        system = await self.scopes.create(
            ScopeCreate(key="system", title="System")
        )
        permissions = (
            AdminPermission.READ
            | AdminPermission.CREATE
            | AdminPermission.UPDATE
            | AdminPermission.DELETE
        )
        await self.grants.create(
            role.id,
            RoleScopeCreate(scope_id=access.id, permissions=int(permissions)),
        )
        await self.grants.create(
            role.id,
            RoleScopeCreate(
                scope_id=system.id, permissions=AdminPermission.READ
            ),
        )
        user = await self.users.create(
            UserCreate(
                first_name=data.first_name,
                last_name=data.last_name,
                mobile=data.mobile,
                password=data.password,
                role_id=role.id,
            ),
            super_admin=True,
        )
        return user
