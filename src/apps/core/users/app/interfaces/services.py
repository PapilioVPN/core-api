"""Typed user account service contract for application collaborators."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.users.domain.dtos.profile import UserProfileUpdate
from src.apps.core.users.domain.dtos.records import (
    UserBatchRead,
    UserList,
    UserRoleUpdate,
    UserUpdate,
)
from src.apps.core.users.domain.models.records import UserModel
from src.apps.core.users.domain.results.profile import UserProfileResult


class IUserService(Protocol):
    async def create(self, data: UserModel) -> UserModel: ...
    async def get_by_id(self, id: int) -> UserModel: ...
    async def find_by_id(self, id: int) -> UserModel | None: ...
    async def find_by_mobile(self, mobile: str) -> UserModel | None: ...
    async def exists_by_role_id(self, role_id: int) -> bool: ...
    async def get_by_ids(self, data: UserBatchRead) -> Sequence[UserModel]: ...
    async def list(self, query: UserList) -> PagedType[UserModel]: ...
    async def update(
        self, id: int, data: UserUpdate | UserProfileUpdate
    ) -> UserModel: ...
    async def set_role(self, id: int, data: UserRoleUpdate) -> UserModel: ...
    async def set_mobile(self, id: int, mobile: str) -> UserModel: ...
    async def set_email(self, id: int, email: str | None) -> UserModel: ...
    async def replace_password_hash(
        self, id: int, current: str, replacement: str
    ) -> UserModel | None: ...

    async def set_password_hash(
        self, id: int, hashed_password: str | None
    ) -> UserModel: ...
    async def remove(self, id: int) -> UserModel: ...


class IUserProfileService(Protocol):
    async def get_me(self, identity: AdminIdentity) -> UserProfileResult:
        """Read the current profile with its verified token permissions.

        Args:
            identity: Verified account identity and payload role/scope claims,
                supplied by authentication, never by caller body or URL fields.

        Returns:
            Current profile with role ID and scopes from the token payload,
            preserving zero masks. Check current account/assigned-role
            availability through their owning interfaces.

        Raises:
            UnAuthorizedException: Account or assigned role is absent/inactive.
        """
        ...
