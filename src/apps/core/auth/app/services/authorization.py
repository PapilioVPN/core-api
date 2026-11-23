"""Evaluate administrator permissions against current account eligibility."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.auth.app.validators.authorization import (
    validate_admin_permission,
)
from src.apps.core.auth.app.validators.password import (
    require_active_user,
)
from src.apps.core.auth.domain.enums.permissions import AdminPermission
from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.roles.app.interfaces.services import IRoleService
from src.apps.core.users.app.interfaces.services import IUserService
from src.apps.core.users.app.validators.profile import require_active_role


class AdminAuthorizationService:
    def __init__(self, users: IUserService, roles: IRoleService) -> None:
        """Bind authoritative account and role owners for this request.

        Args:
            users: Current account records through the owning app interface.
            roles: Assigned-role activity through the owning app interface.

        Returns:
            None.
        """
        self.users = users
        self.roles = roles

    @transactional
    async def check(
        self, identity: AdminIdentity, scope: str, permission: AdminPermission
    ) -> AdminIdentity:
        """Require current availability and the token's operation permission.

        Args:
            identity: Verified administrator access identity.
            scope: Exact server-selected group key.
            permission: Operation bits required by the caller.

        Returns:
            Original identity with its scope snapshot unchanged.

        Raises:
            UnAuthorizedException: Account or assigned role is unavailable.
            ForbiddenException: Scope or any required permission bit is absent.
            Exception: Backend failures and cancellation propagate unchanged.
        """
        user = require_active_user(
            await self.users.find_by_id(identity.user_id)
        )
        if not user.is_super_admin:
            require_active_role(await self.roles.find_by_id(user.role_id))
            validate_admin_permission(identity, scope, permission)
        return identity
