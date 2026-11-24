"""Persist one-time refresh consumption through its owning repository."""

from datetime import UTC, datetime

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.access.tokens.app.validators.refresh import (
    validate_refresh_consumption,
)
from src.apps.core.access.tokens.domain.models.refresh import RefreshUseModel
from src.apps.core.access.tokens.domain.models.tokens import VerifiedToken
from src.apps.core.access.tokens.infra.pg.repositories.refresh import (
    RefreshUseRepository,
)


class RefreshUseService:
    def __init__(self, repo: RefreshUseRepository) -> None:
        """Bind the request's refresh-consumption repository.

        Args:
            repo: Native PostgreSQL repository on the owning request's UoW.

        Returns:
            None.
        """
        self.repo = repo

    @transactional
    async def revoke(self, token: VerifiedToken) -> bool:
        """Invalidate one verified refresh without changing existing history.

        Args:
            token: Verified refresh identity and its original expiration.

        Returns:
            True when newly revoked, or False when previously consumed.

        Raises:
            Exception: SQL/commit failures and cancellation propagate.
        """
        inserted = await self.repo.insert_if_absent(
            RefreshUseModel(
                audience=token.identity.audience,
                token_id=token.token_id,
                expires_at=token.expires_at,
            )
        )
        return inserted

    @transactional
    async def remove_expired(self, *, limit: int) -> int:
        """Remove expired history without weakening live replay protection.

        Args:
            limit: Trusted maximum rows removed in this invocation.

        Returns:
            Actual count removed at the current UTC cutoff. Native transactions
            commit an owned call and preserve a caller's outer transaction.

        Raises:
            Exception: SQL/commit failures and cancellation propagate.
        """
        removed = await self.repo.remove_expired(
            before=datetime.now(UTC), limit=limit
        )
        return removed

    @transactional
    async def consume(self, token: VerifiedToken) -> None:
        """Record an unused verified identity without a read-check-write race.

        Args:
            token: Verified refresh identity and original expiration.

        Returns:
            None; raw credentials and account permissions are never persisted.

        Raises:
            UnAuthorizedException: A committed consumption already exists.
            Exception: SQL/commit failures propagate; rollback preserves reuse.
        """
        inserted = await self.revoke(token)
        validate_refresh_consumption(inserted)
