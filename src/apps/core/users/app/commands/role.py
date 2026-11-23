"""Coordinate user role changes through the owning service contracts."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.roles.app.interfaces.services import IRoleService
from src.apps.core.users.app.interfaces.services import IUserService
from src.apps.core.users.domain.dtos.records import UserRoleUpdate
from src.apps.core.users.domain.models.records import UserModel


class UserRoleCommand:
    def __init__(self, users: IUserService, roles: IRoleService) -> None:
        """Bind account writes and authoritative role reads.

        Args:
            users: Owning user service on the current request's UoW.
            roles: Role existence contract on that same UoW.

        Returns:
            None.
        """
        self.users = users
        self.roles = roles

    @transactional
    async def update(self, id: int, data: UserRoleUpdate) -> UserModel:
        """Change a user's role after verifying the referenced role exists.

        Args:
            id: Stored user identity.
            data: Validated target role identity.

        Returns:
            The user with its new role; other account fields are preserved.

        Raises:
            NotFoundException: The role or user is absent.
        """
        await self.roles.get_by_id(data.role_id)
        user = await self.users.set_role(id, data)
        return user
