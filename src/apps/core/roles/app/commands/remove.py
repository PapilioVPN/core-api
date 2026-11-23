"""Coordinate role removal through authoritative role and user services."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.roles.app.interfaces.services import IRoleService
from src.apps.core.roles.app.validators.remove import (
    validate_role_removal,
)
from src.apps.core.roles.domain.models.records import RoleModel
from src.apps.core.users.app.interfaces.services import IUserService


class RoleRemoveCommand:
    def __init__(self, roles: IRoleService, users: IUserService) -> None:
        """Bind role mutations and the owning user-reference read contract.

        Args:
            roles: Role service on the current request's UoW.
            users: User existence contract on that same UoW.

        Returns:
            None.
        """
        self.roles = roles
        self.users = users

    @transactional
    async def remove(self, id: int) -> RoleModel:
        """Remove an existing role only when no account references it.

        Args:
            id: Stored role identity.

        Returns:
            The removed role; its scope assignments cascade natively.

        Raises:
            NotFoundException: The role does not exist.
            ValidationException: An active or inactive account has this role.
        """
        await self.roles.get_by_id(id)
        has_users = await self.users.exists_by_role_id(id)
        validate_role_removal(id, has_users)
        role = await self.roles.remove(id)
        return role
