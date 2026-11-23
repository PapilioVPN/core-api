"""Self-profile composition through the owning account and role contracts."""

from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.roles.app.interfaces.services import IRoleService
from src.apps.core.users.app.interfaces.services import IUserService
from src.apps.core.users.app.validators.profile import (
    require_active_role,
    require_active_user,
)
from src.apps.core.users.domain.results.profile import UserProfileResult


class UserProfileService:
    def __init__(self, users: IUserService, roles: IRoleService) -> None:
        """Bind current account and role readers.

        Args:
            users: Authoritative account service in the current request.
            roles: Current role availability reader in that same request.

        Returns:
            None.
        """
        self.users = users
        self.roles = roles

    async def get_me(self, identity: AdminIdentity) -> UserProfileResult:
        """Read the current account with its verified token permissions.

        Args:
            identity: User/role IDs and scopes from verified admin access.

        Returns:
            Current profile with role/scopes exactly as captured in the token.
            Current account and assigned-role availability are still checked.

        Raises:
            UnAuthorizedException: Account or assigned role is absent/inactive.
            Exception: Backend failures and cancellation propagate unchanged.
        """
        user = await self.users.find_by_id(identity.user_id)
        user = require_active_user(user)
        role = await self.roles.find_by_id(user.role_id)
        require_active_role(role, super_admin=user.is_super_admin)
        result = UserProfileResult(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            mobile=user.mobile,
            email=user.email,
            role_id=identity.role_id,
            is_super_admin=user.is_super_admin,
            scopes=identity.scopes,
        )
        return result
