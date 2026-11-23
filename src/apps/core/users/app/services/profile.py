"""Self-profile composition with current administrator permissions."""

from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.users.app.interfaces.services import IUserService
from src.apps.core.users.app.validators.profile import require_active_user
from src.apps.core.users.domain.results.profile import UserProfileResult


class UserProfileService:
    def __init__(self, users: IUserService) -> None:
        """Bind the current account reader.

        Args:
            users: Authoritative account service in the current request.

        Returns:
            None.
        """
        self.users = users

    async def get_me(self, identity: AdminIdentity) -> UserProfileResult:
        """Read the current account with its current role and permissions.

        Args:
            identity: Account and current role and scopes from authentication.

        Returns:
            Current profile with the role and scopes read at authentication.

        Raises:
            UnAuthorizedException: Account is absent or inactive.
            Exception: Backend failures and cancellation propagate unchanged.
        """
        user = require_active_user(
            await self.users.find_by_id(identity.user_id)
        )
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
