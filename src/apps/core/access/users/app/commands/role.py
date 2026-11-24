"""Coordinate user role changes through the owning service contracts."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.access.audit.app.interfaces.records import IAuditWriter
from src.apps.core.access.audit.domain.dtos.event import AuditEvent
from src.apps.core.access.audit.domain.enums.actions import AuditAction
from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.users.app.interfaces.services import IUserService
from src.apps.core.access.users.domain.dtos.records import UserRoleUpdate
from src.apps.core.access.users.domain.models.records import UserModel


class UserRoleCommand:
    def __init__(
        self, users: IUserService, roles: IRoleService, audit: IAuditWriter
    ) -> None:
        """Bind account writes and authoritative role reads.

        Args:
            users: Owning user service on the current request's UoW.
            roles: Role existence contract on that same UoW.
            audit: Audit writer on the same transaction.

        Returns:
            None.
        """
        self.users = users
        self.roles = roles
        self.audit = audit

    @transactional
    async def update(
        self, id: int, data: UserRoleUpdate, *, actor_id: int
    ) -> UserModel:
        """Change a user's role after verifying the referenced role exists.

        Args:
            id: Stored user identity.
            data: Validated target role identity.
            actor_id: Verified operator making the change.

        Returns:
            The user with its new role; other account fields are preserved.

        Raises:
            NotFoundException: The role or user is absent.
        """
        await self.roles.get_by_id(data.role_id)
        user = await self.users.set_role(id, data)
        await self.audit.record(
            actor_id,
            AuditEvent(
                AuditAction.USER_ROLE_UPDATE, user.id, role_id=user.role_id
            ),
        )
        return user
