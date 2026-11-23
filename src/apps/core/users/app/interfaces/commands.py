"""User write workflows consumed through explicit app contracts."""

from typing import Protocol

from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.users.domain.dtos.profile import UserProfileUpdate
from src.apps.core.users.domain.dtos.records import (
    UserCreate,
    UserPasswordUpdate,
    UserRoleUpdate,
)
from src.apps.core.users.domain.models.records import UserModel
from src.apps.core.users.domain.results.profile import UserProfileResult


class IUserCreateCommand(Protocol):
    async def create(
        self, data: UserCreate, *, super_admin: bool = False
    ) -> UserModel: ...


class IUserRoleCommand(Protocol):
    async def update(self, id: int, data: UserRoleUpdate) -> UserModel: ...


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
            identity: Verified token identity and role/scope snapshot. The
                caller cannot choose a different target account or claims.
            data: Name patch; omitted fields stay unchanged. Contact, password,
                role and account-activity changes have separate owners.

        Returns:
            Updated self-account view without raw or hashed credentials,
            preserving the role and scope masks captured in the access token.

        Raises:
            UnAuthorizedException: Account or assigned role is absent/inactive.
            ValidationException: No recognized profile fields were supplied.
        """
        ...
