"""Administrator refresh and logout command contracts."""

from typing import Protocol

from src.apps.core.auth.domain.dtos.refresh import TokenRefresh
from src.apps.core.tokens.domain.results.records import TokenPair


class ITokenRefreshCommand(Protocol):
    async def refresh(self, data: TokenRefresh) -> TokenPair:
        """Rotate one administrator refresh using current account grants.

        Args:
            data: Private refresh credential; caller claims are ignored.

        Returns:
            New access/refresh pair after current account/role/policy reads
            and consumption of the old refresh in one native transaction.
            No sudo credential is issued or extended.

        Raises:
            UnAuthorizedException: Token is invalid/reused or account/role
                unavailable. On failure SQL consumption is rolled back.
        """
        ...


class ITokenLogoutCommand(Protocol):
    async def logout(self, data: TokenRefresh) -> None:
        """Revoke the supplied administrator refresh in a native transaction.

        Args:
            data: Private refresh credential; no access or sudo is required.

        Returns:
            None. Repeated revocation succeeds without changing history;
            other credentials retain their own validity.

        Raises:
            UnAuthorizedException: Credential verification fails.
        """
        ...
