"""Read and persist group definitions in PostgreSQL."""

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import col

from ....domain.models.records import CustomerGroupModel
from ..tables import CustomerGroupTable


class CustomerGroupRepository(PGPersistenceRepository[CustomerGroupModel]):
    table = CustomerGroupTable

    async def find_by_key(self, key: str) -> CustomerGroupModel | None:
        """Read a group by its exact key.

        Args:
            key: Stored group key.

        Returns:
            The matching group, or None if absent.
        """
        group = await self.get_one(col(self.table.key) == key)
        return group

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None,
        is_active: bool | None,
    ) -> PagedType[CustomerGroupModel]:
        """Read matching groups in priority and ID order.

        Args:
            limit: Maximum number of rows.
            offset: Matching rows to skip.
            q: Optional literal title or key substring.
            is_active: Optional filter on the stored activity flag.

        Returns:
            The page of groups and their total before pagination.
        """
        table = self.table
        where = []
        if q is not None:
            where.append(
                or_(
                    col(table.key).icontains(q, autoescape=True),
                    col(table.title).icontains(q, autoescape=True),
                )
            )
        if is_active is not None:
            where.append(col(table.is_active).is_(is_active))
        groups = await self.get_page(
            where=where,
            order_by=[col(table.priority).asc(), col(table.id).asc()],
            limit=limit,
            offset=offset,
        )
        return groups

    async def remove_by_id(self, id: int) -> CustomerGroupModel | None:
        """Remove an unused group.

        Args:
            id: Stored customer group identity.

        Returns:
            The removed group or None if absent.

        Raises:
            ConflictException: A customer still references the group.
        """
        try:
            group = await super().remove_by_id(id)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) != "23503":
                raise
            raise ConflictException(
                message="This group is still assigned to a customer.",
                message_code="customer_group_in_use",
                unique_dict={},
            ) from error
        return group
