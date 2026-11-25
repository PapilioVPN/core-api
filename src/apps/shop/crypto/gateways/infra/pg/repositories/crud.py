"""Persist gateway accounts and read filtered pages for the panel."""

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import col

from ....domain.models.records import CryptoGatewayModel
from ..tables import CryptoGatewayTable


class CryptoGatewayRepository(PGPersistenceRepository[CryptoGatewayModel]):
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
        """Read a page of stored gateway accounts.

        Args:
            limit: Maximum rows to read.
            offset: Matching rows to skip.
            q: Literal title or key substring.
            kind: Exact provider type.
            is_active: Optional activity filter.

        Returns:
            Matching accounts in descending ID order and their total.
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
        if kind is not None:
            where.append(col(table.kind) == kind)
        if is_active is not None:
            where.append(col(table.is_active).is_(is_active))
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page

    async def remove_by_id(self, id: int) -> CryptoGatewayModel | None:
        """Remove a gateway account that has no payment history.

        Args:
            id: Stored gateway identity.

        Returns:
            The removed account, or None if absent.

        Raises:
            ConflictException: A payment references the account.
        """
        try:
            gateway = await super().remove_by_id(id)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) != "23503":
                raise
            raise ConflictException(
                message="This gateway has payment history.",
                message_code="crypto_gateway_in_use",
                unique_dict={},
            ) from error
        return gateway
