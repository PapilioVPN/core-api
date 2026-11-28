"""Read and write card gateway accounts with native PostgreSQL operations."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlmodel import col

from ....domain.dtos.records import GatewayList
from ....domain.enums.records import GatewayKind
from ....domain.models.records import GatewayModel
from ..tables import CardGatewayTable


class GatewayRepository(PGPersistenceRepository[GatewayModel]):
    table = CardGatewayTable

    async def find_by_kind(self, kind: GatewayKind) -> GatewayModel | None:
        """Read the unique account for the provider kind, if configured."""
        gateway = await self.get_one(col(self.table.kind) == kind)
        return gateway

    async def list(
        self, query: GatewayList, *, offset: int
    ) -> PagedType[GatewayModel]:
        """Read a filtered page of stored gateway accounts.

        Args:
            query: Validated filters and page size.
            offset: Number of matching accounts to skip.

        Returns:
            Matching accounts in descending ID order and the unpaged count.
        """
        table = self.table
        where = []
        if query.q is not None:
            where.append(col(table.title).icontains(query.q, autoescape=True))
        if query.kind is not None:
            where.append(col(table.kind) == query.kind)
        if query.is_active is not None:
            where.append(col(table.is_active).is_(query.is_active))
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=query.per_page,
            offset=offset,
        )
        return page
