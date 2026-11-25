"""Read and persist gateway accounts."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlmodel import col

from ....domain.models.records import CryptoGatewayModel
from ..tables import CryptoGatewayTable


class CryptoGatewayRepository(PGIdentifiedRepository[CryptoGatewayModel]):
    table = CryptoGatewayTable

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None,
        kind: str | None,
        is_active: bool | None,
    ) -> PagedType[CryptoGatewayModel]:
        """Page matching gateway accounts.

        Args:
            limit: Maximum number of rows.
            offset: Matching rows to skip.
            q: Literal title substring.
            kind: Exact provider kind.
            is_active: Exact activity state, if supplied.

        Returns:
            Matching gateways in ID order and their filtered total.
        """
        table = self.table
        where = []
        if q is not None:
            where.append(col(table.title).icontains(q, autoescape=True))
        if kind is not None:
            where.append(col(table.kind) == kind)
        if is_active is not None:
            where.append(col(table.is_active).is_(is_active))
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).asc()],
            limit=limit,
            offset=offset,
        )
        return page
