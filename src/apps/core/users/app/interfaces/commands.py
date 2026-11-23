"""User write workflows consumed through explicit app contracts."""

from typing import Protocol

from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.users.domain.dtos.password import UserPasswordUpdate
from src.apps.core.users.domain.dtos.profile import UserProfileUpdate
from src.apps.core.users.domain.dtos.records import (
    UserCreate,
    UserRoleUpdate,
)
from src.apps.core.users.domain.models.records import UserModel
from src.apps.core.users.domain.results.profile import UserProfileResult


class IUserCreateCommand(Protocol):
    async def create(
        self, data: UserCreate, *, super_admin: bool = False
    ) -> UserModel: ...


class IUserRoleCommand(Protocol):
    async def update(
        self, id: int, data: UserRoleUpdate, *, actor_id: int
    ) -> UserModel: ...


class IUserPasswordCommand(Protocol):
    async def update_me(
        self, identity: AdminIdentity, data: UserPasswordUpdate
    ) -> UserModel:
        """Change only the authenticated user's password.

        Args:
            identity: Verified current-account identity.
            data: Native validated current and new passwords.

        Returns:
            The stored user after current account/role checks and hashing;
            credential fields remain private at the output boundary.
        """
        ...


class IUserProfileCommand(Protocol):
    async def update(
        self, identity: AdminIdentity, data: UserProfileUpdate
    ) -> UserProfileResult:
        """Update the authenticated account's supplied profile names.

        Args:
            identity: Verified current account, role and scopes.
            data: Name patch; omitted fields stay unchanged. Contact, password,
                role and account-activity changes have separate owners.

        Returns:
            Updated self-account view without raw or hashed credentials,
            with the role and scopes resolved for this request.

        Raises:
            UnAuthorizedException: Account is absent or inactive.
            ValidationException: No recognized profile fields were supplied.
        """
        ...
