"""Administrator session records and lifetime."""

from datetime import UTC, datetime
from uuid import UUID

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType

from src.apps.core.access.auth.app.validators.identity import (
    session_unavailable,
)
from src.apps.core.access.auth.domain.dtos.sessions import SessionList
from src.apps.core.access.auth.domain.models.sessions import SessionModel
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.domain.results.sessions import SessionResult
from src.apps.core.access.auth.infra.pg.repositories.sessions import (
    SessionRepository,
)


class SessionService:
    def __init__(self, repo: SessionRepository) -> None:
        """Bind the session repository on the native request UoW.

        Args:
            repo: Owner of administrator session persistence.

        Returns:
            None.
        """
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
        """Store the login and its refresh expiry.

        Args:
            user_id: Authenticated owner account.
            id: New session UUID.
            expires_at: Aware UTC refresh-token deadline.
            user_agent: Bounded device label, if supplied.

        Returns:
            None after the session is saved.
        """
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
        """Require the current account's live session.

        Args:
            user_id: Verified account identity.
            id: Session UUID carried by its signed credential.

        Returns:
            None when the session is valid.

        Raises:
            UnAuthorizedException: Session is absent, expired or foreign.
        """
        if not await self.repo.exists(user_id, id, now=datetime.now(UTC)):
            raise session_unavailable()

    async def rotate(
        self, user_id: int, id: UUID, *, expires_at: datetime
    ) -> None:
        """Record refresh time and expiry in the owning transaction.

        Args:
            user_id: Verified account identity.
            id: Session UUID from the refresh credential.
            expires_at: Aware UTC deadline of the replacement credential.

        Returns:
            None after extending the session.

        Raises:
            UnAuthorizedException: The session is no longer active.
        """
        rotated = await self.repo.rotate(
            user_id, id, now=datetime.now(UTC), expires_at=expires_at
        )
        if not rotated:
            raise session_unavailable()

    async def list(
        self, identity: AdminIdentity, query: SessionList
    ) -> PagedType[SessionResult]:
        """List active sessions and identify the authenticated one.

        Args:
            identity: Authenticated account and current session.
            query: Native page and page size.

        Returns:
            Newest-first active sessions and their filtered total.
        """
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
        """Close one owned active session.

        Args:
            user_id: Verified owner account.
            id: Session UUID.

        Returns:
            True if a live session was removed.
        """
        revoked = await self.repo.revoke(user_id, id, now=datetime.now(UTC))
        return revoked

    @transactional
    async def revoke_others(self, user_id: int, id: UUID) -> int:
        """Close other active sessions for the same account.

        Args:
            user_id: Verified owner account.
            id: Current session UUID to preserve.

        Returns:
            Number of live sessions removed.
        """
        count = await self.repo.revoke_others(
            user_id, id, now=datetime.now(UTC)
        )
        return count

    @transactional
    async def remove_expired(self, *, limit: int = 100) -> int:
        """Delete one bounded batch of expired sessions.

        Args:
            limit: Maximum number of rows to remove.

        Returns:
            Count removed at the current UTC time.
        """
        count = await self.repo.remove_expired(
            now=datetime.now(UTC), limit=limit
        )
        return count
