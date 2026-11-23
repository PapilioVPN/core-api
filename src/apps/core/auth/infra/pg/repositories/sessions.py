"""Read and mutate sessions by account, identity and expiry."""

from datetime import datetime
from uuid import UUID

from papilio.infra.db.repositories.backends.postgresql import PGReader
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import CursorResult, delete, insert, select, update
from sqlmodel import col

from src.apps.core.auth.domain.models.sessions import SessionModel
from src.apps.core.auth.infra.pg.tables import SessionTable


class SessionRepository(PGReader):
    async def create(self, session: SessionModel) -> None:
        """Insert one session in the caller's transaction."""
        stmt = insert(SessionTable).values(session.to_row())
        await self.uow.execute(stmt)

    async def exists(self, user_id: int, id: UUID, *, now: datetime) -> bool:
        """Check an owned session whose expiration is after the UTC cutoff."""
        stmt = select(col(SessionTable.id)).where(
            col(SessionTable.user_id) == user_id,
            col(SessionTable.id) == id,
            col(SessionTable.expires_at) > now,
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list(
        self, user_id: int, *, now: datetime, limit: int, offset: int
    ) -> PagedType[SessionModel]:
        """Read a bounded newest-first page of currently active sessions."""
        stmt = (
            select(SessionTable)
            .where(
                col(SessionTable.user_id) == user_id,
                col(SessionTable.expires_at) > now,
            )
            .order_by(
                col(SessionTable.last_seen_at).desc(),
                col(SessionTable.id).desc(),
            )
        )
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return PagedType(items=list(page.items), total_items=page.total_items)

    async def rotate(
        self, user_id: int, id: UUID, *, now: datetime, expires_at: datetime
    ) -> bool:
        """Extend a still-active session after a successful refresh."""
        stmt = (
            update(SessionTable)
            .where(
                col(SessionTable.user_id) == user_id,
                col(SessionTable.id) == id,
                col(SessionTable.expires_at) > now,
            )
            .values(last_seen_at=now, expires_at=expires_at)
            .returning(col(SessionTable.id))
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def revoke(self, user_id: int, id: UUID, *, now: datetime) -> bool:
        """Delete the matching live owned session, if present."""
        stmt = (
            delete(SessionTable)
            .where(
                col(SessionTable.user_id) == user_id,
                col(SessionTable.id) == id,
                col(SessionTable.expires_at) > now,
            )
            .returning(col(SessionTable.id))
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def revoke_others(
        self, user_id: int, id: UUID, *, now: datetime
    ) -> int:
        """Delete other live sessions for this account and count them."""
        stmt = delete(SessionTable).where(
            col(SessionTable.user_id) == user_id,
            col(SessionTable.id) != id,
            col(SessionTable.expires_at) > now,
        )
        result = await self.uow.execute(stmt)
        assert isinstance(result, CursorResult)
        return result.rowcount

    async def remove_expired(self, *, now: datetime, limit: int) -> int:
        """Delete at most limit expired rows and return the affected count."""
        ids = (
            select(col(SessionTable.id))
            .where(col(SessionTable.expires_at) <= now)
            .order_by(col(SessionTable.expires_at), col(SessionTable.id))
            .limit(limit)
        )
        stmt = delete(SessionTable).where(
            col(SessionTable.id).in_(ids),
            col(SessionTable.expires_at) <= now,
        )
        result = await self.uow.execute(stmt)
        assert isinstance(result, CursorResult)
        return result.rowcount
