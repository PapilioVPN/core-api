"""Current-account password changes using Papilio password verification."""

from papilio.infra.db.tools.decorators import transactional
from papilio.security.passwords import PasswordHasher

from src.apps.core.auth.app.validators.password import (
    require_active_user,
    require_password_hash,
    validate_password_match,
)
from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.users.app.interfaces.services import (
    IUserProfileService,
    IUserService,
)
from src.apps.core.users.domain.dtos.password import UserPasswordUpdate
from src.apps.core.users.domain.models.records import UserModel


class UserPasswordCommand:
    def __init__(
        self,
        users: IUserService,
        hasher: PasswordHasher,
        profiles: IUserProfileService,
    ) -> None:
        """Bind the account, its eligibility check and the native hasher."""
        self.users = users
        self.hasher = hasher
        self.profiles = profiles

    @transactional
    async def update_me(
        self, identity: AdminIdentity, data: UserPasswordUpdate
    ) -> UserModel:
        """Verify the current password and atomically replace its stored hash.

        Args:
            identity: Signed-in administrator identity.
            data: Validated current and replacement passwords.

        Returns:
            Updated account with its new hash stored by the owning repository.
        """
        await self.profiles.get_me(identity)
        user = await self.users.get_by_id(identity.user_id)
        current = require_password_hash(user.hashed_password)
        matches = await self.hasher.verify(data.current_password, current)
        validate_password_match(matches)
        replacement = await self.hasher.hash(data.password)
        updated = await self.users.replace_password_hash(
            user.id, current, replacement
        )
        return require_active_user(updated)
