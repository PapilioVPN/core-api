"""Persist and look up API keys through native PostgreSQL operations."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import and_
from sqlmodel import col

from ....domain.models.records import APIKeyModel
from ..tables import CardAPIKeyTable


class APIKeyRepository(PGPersistenceRepository[APIKeyModel]):
    table = CardAPIKeyTable

    async def list(self, *, limit: int, offset: int) -> PagedType[APIKeyModel]:
        """Page stored key records by descending identity.

        Args:
            limit: Maximum rows to return.
            offset: Number of matching rows to skip.

        Returns:
            The requested page with its total count.
        """
        page = await self.get_page(
            order_by=[col(self.table.id).desc()], limit=limit, offset=offset
        )
        return page

    async def find_active(
        self, digest: str, *, now: datetime
    ) -> APIKeyModel | None:
        """Find an unexpired and unrevoked key by its unique digest.

        Args:
            digest: Digest of the supplied credential.
            now: Current UTC instant for the exclusive expiry boundary.

        Returns:
            The active key or None if there is no match.
        """
        table = self.table
        record = await self.get_one(
            col(table.digest) == digest,
            col(table.revoked_at).is_(None),
            col(table.expires_at) > now,
        )
        return record

    async def revoke(
        self, id: int, *, revoked_at: datetime
    ) -> APIKeyModel | None:
        """Record the revocation only if one has not already been stored.

        Args:
            id: Stored key identity.
            revoked_at: UTC instant of the revocation.

        Returns:
            The updated key, or None if it is absent or already revoked.
        """
        table = self.table
        rows = await self.update(
            and_(col(table.id) == id, col(table.revoked_at).is_(None)),
            {"revoked_at": revoked_at},
        )
        return rows[0] if rows else None
