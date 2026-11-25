"""Native PostgreSQL reads and writes for bank deposits."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlmodel import col

from ....domain.dtos.records import DepositSearch
from ....domain.models.records import DepositModel
from ..tables import DepositTable


class DepositRepository(PGPersistenceRepository[DepositModel]):
    table = DepositTable

    async def search(self, query: DepositSearch) -> PagedType[DepositModel]:
        """Page reports by amount, matched payment or match presence."""
        table = self.table
        filters = []
        if query.amount is not None:
            filters.append(col(table.amount) == query.amount)
        if query.payment_id is not None:
            filters.append(col(table.payment_id) == query.payment_id)
        if query.matched is not None:
            filters.append(
                col(table.payment_id).is_not(None)
                if query.matched
                else col(table.payment_id).is_(None)
            )
        page = await self.get_page(
            where=filters,
            order_by=[col(table.id).desc()],
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
        )
        return page
