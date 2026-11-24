"""Self-profile edits through the existing user write operation."""

from dataclasses import replace

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.users.app.interfaces.services import (
    IUserProfileService,
    IUserService,
)
from src.apps.core.access.users.domain.dtos.profile import UserProfileUpdate
from src.apps.core.access.users.domain.results.profile import UserProfileResult


class UserProfileCommand:
    def __init__(
        self, users: IUserService, profiles: IUserProfileService
    ) -> None:
        """Bind profile eligibility and the existing account write owner.

        Args:
            users: User service on the current request's SQL UoW.
            profiles: Current profile and role reader on the same request.

        Returns:
            None.
        """
        self.users = users
        self.profiles = profiles

    @transactional
    async def update(
        self, identity: AdminIdentity, data: UserProfileUpdate
    ) -> UserProfileResult:
        """Update supplied names after checking account and role availability.

        Args:
            identity: Account and permission snapshot from a verified token.
            data: Restricted name patch; omitted fields remain unchanged.

        Returns:
            The checked profile snapshot with names returned by the write.
            Permissions are reused from that snapshot without a second read.

        Raises:
            UnAuthorizedException: Account or assigned role is unavailable.
            ValidationException: Native user update rejects an empty patch.
            Exception: Write/commit failures and cancellation propagate;
                the owning native transaction rolls back unsuccessful work.
        """
        profile = await self.profiles.get_me(identity)
        user = await self.users.update(
            identity.user_id,
            data,
        )
        result = replace(
            profile, first_name=user.first_name, last_name=user.last_name
        )
        return result
