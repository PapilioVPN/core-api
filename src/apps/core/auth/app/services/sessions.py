"""Admin session lifetime and authenticated self-service policies."""

from datetime import UTC, datetime
from uuid import UUID

from papilio.errors.exceptions import NotFoundException
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType

from src.apps.core.auth.app.validators.identity import session_unavailable
from src.apps.core.auth.domain.dtos.sessions import SessionList
from src.apps.core.auth.domain.models.sessions import SessionModel
from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.auth.domain.results.sessions import SessionResult
from src.apps.core.auth.infra.pg.repositories.sessions import (
    SessionRepository,
)


class SessionService:
    def __init__(self, repo: SessionRepository) -> None:
        self.repo = repo

    @transactional
    async def create(
        self,
        user_id: int,
        id: UUID,
        *,
        expires_at: datetime,
        user_agent: str | None,
    ) -> None:
        """Store the login and its current refresh expiry, in UTC."""
        now = datetime.now(UTC)
        await self.repo.create(
            SessionModel(
                id=id,
                user_id=user_id,
                created_at=now,
                last_seen_at=now,
                expires_at=expires_at,
                user_agent=user_agent,
            )
        )

    async def require(self, user_id: int, id: UUID) -> None:
        """Reject absent, expired or foreign sessions."""
        if not await self.repo.exists(user_id, id, now=datetime.now(UTC)):
            raise session_unavailable()

    async def rotate(
        self, user_id: int, id: UUID, *, expires_at: datetime
    ) -> None:
        """Record refresh time and expiry in the owning transaction."""
        rotated = await self.repo.rotate(
            user_id, id, now=datetime.now(UTC), expires_at=expires_at
        )
        if not rotated:
            raise session_unavailable()

    async def list(
        self, identity: AdminIdentity, query: SessionList
    ) -> PagedType[SessionResult]:
        """List active sessions and identify the authenticated one."""
        page = await self.repo.list(
            identity.user_id,
            now=datetime.now(UTC),
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
        )
        return PagedType(
            items=[
                SessionResult(
                    id=row.id,
                    created_at=row.created_at,
                    last_seen_at=row.last_seen_at,
                    expires_at=row.expires_at,
                    user_agent=row.user_agent,
                    current=row.id == identity.session_id,
                )
                for row in page.items
            ],
            total_items=page.total_items,
        )

    @transactional
    async def revoke(self, user_id: int, id: UUID) -> bool:
        """Close one owned active session and report whether it existed."""
        revoked = await self.repo.revoke(user_id, id, now=datetime.now(UTC))
        return revoked

    async def revoke_one(self, identity: AdminIdentity, id: UUID) -> None:
        """Close an owned session or report it as missing."""
        if not await self.revoke(identity.user_id, id):
            raise NotFoundException(
                message="Session not found",
                message_code="session_not_found",
                entity="Session",
                identifier="id",
                identifier_value=id,
            )

    @transactional
    async def revoke_others(self, identity: AdminIdentity) -> int:
        """Close other active sessions for this account."""
        count = await self.repo.revoke_others(
            identity.user_id, identity.session_id, now=datetime.now(UTC)
        )
        return count

    @transactional
    async def remove_expired(self, *, limit: int) -> int:
        """Delete one bounded batch of expired sessions."""
        count = await self.repo.remove_expired(
            now=datetime.now(UTC), limit=limit
        )
        return count
