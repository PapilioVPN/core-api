"""Filter and page through customer profiles for the panel."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import or_
from sqlmodel import col

from ....domain.models.records import CustomerModel
from ..tables import CustomerTable


class ProfileReader(PGIdentifiedRepository[CustomerModel]):
    table = CustomerTable

    async def search(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None,
        group_id: int | None,
        is_blocked: bool | None,
    ) -> PagedType[CustomerModel]:
        """Read one page of customer profiles in descending ID order.

        Args:
            limit: Maximum number of profiles.
            offset: Matching profiles to skip.
            q: Optional literal substring of the name or mobile number.
            group_id: Optional exact customer group identity.
            is_blocked: Optional customer block-state filter.

        Returns:
            The matching page and its total before pagination.
        """
        table = self.table
        where = []
        if q is not None:
            where.append(
                or_(
                    col(table.name).icontains(q, autoescape=True),
                    col(table.mobile).contains(q, autoescape=True),
                )
            )
        if group_id is not None:
            where.append(col(table.group_id) == group_id)
        if is_blocked is not None:
            where.append(col(table.is_blocked).is_(is_blocked))
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page
