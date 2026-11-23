"""User persistence through Papilio's native PostgreSQL repository."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import func, or_, select, update
from sqlmodel import col

from src.apps.core.users.domain.models.records import UserModel
from src.apps.core.users.domain.results.records import UserAccess
from src.apps.core.users.infra.pg.tables import UserTable


class UserRepository(PGPersistenceRepository[UserModel]):
    table = UserTable

    async def find_access(self, id: int) -> UserAccess | None:
        """Select only the account fields needed for authorization.

        Args:
            id: Stored account identity.

        Returns:
            Current account flags and role ID, or None for a missing account.
        """
        stmt = select(
            col(self.table.id),
            col(self.table.role_id),
            col(self.table.is_active),
            col(self.table.is_super_admin),
        ).where(col(self.table.id) == id)
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        access = None if row is None else UserAccess(*row)
        return access

    async def find_by_mobile(self, mobile: str) -> UserModel | None:
        """Read a user by exact mobile, including inactive accounts.

        Args:
            mobile: Exact stored mobile, passed unchanged as a bound value.

        Returns:
            The stored user, or None when the mobile does not exist.
        """
        user = await self.get_one(col(self.table.mobile) == mobile)
        return user

    async def replace_password_hash(
        self, id: int, current: str, replacement: str
    ) -> UserModel | None:
        """Conditionally update the exact active account in one statement.

        Args:
            id: Internal account identity.
            current: Expected stored hash.
            replacement: Newly prepared hash.

        Returns:
            Updated row, or None when the predicate no longer matches.
        """
        stmt = (
            update(UserTable)
            .where(
                col(UserTable.id) == id,
                col(UserTable.is_active).is_(True),
                col(UserTable.hashed_password) == current,
            )
            .values(hashed_password=replacement)
            .returning(UserTable)
            .execution_options(
                populate_existing=True, synchronize_session=False
            )
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_role_id(self, role_id: int) -> bool:
        """Check for any user referencing a role with native SELECT EXISTS.

        Args:
            role_id: Exact role ID, matched through the indexed foreign key.

        Returns:
            True if at least one user, including inactive users, has the role;
            False if none do.
        """
        exists = await self.exists(col(self.table.role_id) == role_id)
        return exists

    async def list(
        self,
        *,
        limit: int,
        offset: int = 0,
        q: str | None = None,
        role_id: int | None = None,
        is_active: bool | None = None,
    ) -> PagedType[UserModel]:
        """Read an ID-ordered user page and its filtered total count.

        Args:
            limit: Positive maximum number of rows to retrieve.
            offset: Nonnegative number of matching rows to skip.
            q: Literal case-insensitive substring of full name or mobile;
                None skips search.
            role_id: Exact role ID; None includes all roles.
            is_active: Stored account flag; None includes both states.

        Returns:
            Materialized matching users and total count before pagination.

        Raises:
            ValueError: Limit is nonpositive or offset is negative.
        """
        stmt = select(self.table).order_by(col(self.table.id))
        if q is not None:
            stmt = stmt.where(
                or_(
                    func.concat(
                        col(self.table.first_name),
                        " ",
                        col(self.table.last_name),
                    ).icontains(q, autoescape=True),
                    col(self.table.mobile).icontains(q, autoescape=True),
                )
            )
        if role_id is not None:
            stmt = stmt.where(col(self.table.role_id) == role_id)
        if is_active is not None:
            stmt = stmt.where(col(self.table.is_active) == is_active)
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return page
