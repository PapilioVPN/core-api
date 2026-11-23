"""One-time refresh consumption shared by account-owning applications."""

from typing import Protocol

from src.apps.core.tokens.domain.models.tokens import VerifiedToken


class IRefreshUseService(Protocol):
    async def revoke(self, token: VerifiedToken) -> None:
        """Ensure a verified refresh identity can no longer be consumed.

        Args:
            token: Refresh metadata verified by the owning token service.

        Returns:
            None. An existing consumption is unchanged and counts as success.
            Native outer transaction ownership applies.
        """
        ...

    async def remove_expired(self, *, limit: int) -> int:
        """Remove one bounded batch of expired consumption records.

        Args:
            limit: Trusted maximum rows removed in this invocation.

        Returns:
            Actual count removed using the service's current UTC cutoff.
            Unexpired records remain; outer transaction ownership applies.
        """
        ...

    async def consume(self, token: VerifiedToken) -> None:
        """Record a verified refresh identity in the owning transaction.

        Args:
            token: Refresh metadata verified by the owning token service.

        Returns:
            None after this transaction records consumption; nested callers
            retain commit ownership. Raw credential values are never stored.

        Raises:
            UnAuthorizedException: This refresh identity was already used.
        """
        ...
