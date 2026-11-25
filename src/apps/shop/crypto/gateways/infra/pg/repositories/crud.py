"""Read and persist gateway accounts."""

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy.exc import IntegrityError
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

    async def remove_by_id(self, id: int) -> CryptoGatewayModel | None:
        """Remove one account or report that a payment references it."""
        try:
            gateway = await super().remove_by_id(id)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) != "23503":
                raise
            raise ConflictException(
                message="This gateway has a payment record.",
                message_code="crypto_gateway_in_use",
                unique_dict={"gateway_id": id},
            ) from error
        return gateway
