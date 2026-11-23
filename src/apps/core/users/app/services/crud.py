"""User account operations through one native repository."""

from collections.abc import Sequence

from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.core.users.app.validators.profile import protect_owner
from src.apps.core.users.domain.dtos.profile import UserProfileUpdate
from src.apps.core.users.domain.dtos.records import (
    UserBatchRead,
    UserList,
    UserRoleUpdate,
    UserUpdate,
)
from src.apps.core.users.domain.models.records import UserModel
from src.apps.core.users.domain.results.access import UserAccess
from src.apps.core.users.infra.pg.repositories.crud import (
    UserRepository,
)


class UserService(IDChecks[UserModel]):
    entity = "User"

    def __init__(self, repo: UserRepository) -> None:
        """Bind the current request's user repository.

        Args:
            repo: Native PostgreSQL repository on the owning request's UoW.

        Returns:
            None.
        """
        self.repo = repo

    async def find_access(self, id: int) -> UserAccess | None:
        """Read live account eligibility facts for authentication.

        Args:
            id: Stored account identity.

        Returns:
            Current account flags and assigned role, or None when absent.
        """
        access = await self.repo.find_access(id)
        return access

    @handle_conflicts(entity="User")
    @transactional
    async def create(self, data: UserModel) -> UserModel:
        """Store a user after command-owned role and password preparation.

        Args:
            data: Prepared account record with a verified role identity and
                optional precomputed hash; no plaintext password is accepted.

        Returns:
            The stored user with database identity and timestamps.

        Raises:
            ConflictException: Another account has this mobile.
        """
        user = await self.repo.create(data)
        return user

    async def get_by_id(self, id: int) -> UserModel:
        """Read a user whose identity must exist.

        Args:
            id: Stored user identity.

        Returns:
            The stored user, including inactive accounts.

        Raises:
            NotFoundException: The identity is absent.
        """
        user = await self.repo.get_by_id(id)
        user = self._check_for_id_existence(id, user)
        return user

    async def find_by_id(self, id: int) -> UserModel | None:
        """Look up a user without requiring its existence.

        Args:
            id: Stored user identity.

        Returns:
            The user, including inactive accounts; None when absent.
        """
        user = await self.repo.get_by_id(id)
        return user

    async def find_by_mobile(self, mobile: str) -> UserModel | None:
        """Look up a user by exact mobile without requiring its existence.

        Args:
            mobile: Exact stored mobile supplied by the caller.

        Returns:
            The user, including inactive accounts; None when absent.
        """
        user = await self.repo.find_by_mobile(mobile)
        return user

    async def exists_by_role_id(self, role_id: int) -> bool:
        """Expose whether any account still references a role.

        Args:
            role_id: Stored role identity requested by an app collaborator.

        Returns:
            True when an active or inactive user has this role;
            otherwise False.
        """
        exists = await self.repo.exists_by_role_id(role_id)
        return exists

    async def get_by_ids(self, data: UserBatchRead) -> Sequence[UserModel]:
        """Read a bounded set of user identities through one native query.

        Args:
            data: One to 100 validated IDs; duplicates request one record.

        Returns:
            Found users, including inactive accounts, with missing IDs omitted.
            Result order is unspecified.
        """
        users = await self.repo.get_by_ids(data.ids)
        return users

    async def list(self, query: UserList) -> PagedType[UserModel]:
        """List users using application-owned pagination.

        Args:
            query: Native page/per_page and optional name/mobile, role and
                account-state filters.

        Returns:
            An ID-ordered page and its filtered total before pagination.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            q=query.q,
            role_id=query.role_id,
            is_active=query.is_active,
        )
        return page

    @handle_conflicts(entity="User")
    @transactional
    async def update(
        self, id: int, data: UserUpdate | UserProfileUpdate
    ) -> UserModel:
        """Apply supplied profile fields without changing role or password.

        Args:
            id: Stored user identity.
            data: Validated patch; email may be cleared with None.

        Returns:
            The updated user, preserving all omitted fields.

        Raises:
            ValidationException: No recognized profile fields were supplied.
            NotFoundException: The identity is absent.
            ConflictException: Another account has the supplied mobile.
        """
        changes = self._check_not_empty_dict(data.to_row())
        if changes.get("is_active") is False:
            protect_owner(await self.get_by_id(id))
        user = await self.repo.update_by_id(id, changes)
        user = self._check_for_id_existence(id, user)
        return user

    @transactional
    async def set_role(self, id: int, data: UserRoleUpdate) -> UserModel:
        """Replace a user's role after the command verifies the target role.

        Args:
            id: Stored user identity.
            data: Required role identity checked by the owning command.

        Returns:
            The user with the new role and all other account fields preserved.

        Raises:
            NotFoundException: The user identity is absent.
        """
        protect_owner(await self.get_by_id(id))
        user = await self.repo.update_by_id(id, data.to_row())
        user = self._check_for_id_existence(id, user)
        return user

    @handle_conflicts(entity="User")
    @transactional
    async def set_mobile(self, id: int, mobile: str) -> UserModel:
        """Store the contact checked by its owning command.

        Args:
            id: Internal account identity.
            mobile: Trusted verified mobile.

        Returns:
            Updated account with only this contact changed.

        Raises:
            NotFoundException: The account is absent.
            ConflictException: A unique contact is already in use.
        """
        user = await self.repo.update_by_id(id, {"mobile": mobile})
        user = self._check_for_id_existence(id, user)
        return user

    @handle_conflicts(entity="User")
    @transactional
    async def set_email(self, id: int, email: str | None) -> UserModel:
        """Store the contact checked by its owning command.

        Args:
            id: Internal account identity.
            email: Trusted verified email, or None to remove it.

        Returns:
            Updated account with only this contact changed.

        Raises:
            NotFoundException: The account is absent.
            ConflictException: A unique contact is already in use.
        """
        user = await self.repo.update_by_id(id, {"email": email})
        user = self._check_for_id_existence(id, user)
        return user

    @transactional
    async def replace_password_hash(
        self, id: int, current: str, replacement: str
    ) -> UserModel | None:
        """Store a new password hash when the verified current hash matches.

        Args:
            id: Account identity.
            current: Verified stored hash before the change.
            replacement: New prepared hash.

        Returns:
            Updated account, or None when the verified state changed.
        """
        user = await self.repo.replace_password_hash(id, current, replacement)
        return user

    @transactional
    async def set_password_hash(
        self, id: int, hashed_password: str | None
    ) -> UserModel:
        """Store or clear a password hash prepared by the owning command.

        Args:
            id: Stored user identity.
            hashed_password: Precomputed hash; explicit None clears it.

        Returns:
            The user with only its stored password hash changed.

        Raises:
            NotFoundException: The user identity is absent.
        """
        user = await self.repo.update_by_id(
            id, {"hashed_password": hashed_password}
        )
        user = self._check_for_id_existence(id, user)
        return user

    @transactional
    async def remove(self, id: int) -> UserModel:
        """Delete one account through the native transaction boundary.

        Args:
            id: Stored user identity.

        Returns:
            The account as it was immediately before deletion.

        Raises:
            NotFoundException: The user identity is absent.
        """
        protect_owner(await self.get_by_id(id))
        user = await self.repo.remove_by_id(id)
        user = self._check_for_id_existence(id, user)
        return user
