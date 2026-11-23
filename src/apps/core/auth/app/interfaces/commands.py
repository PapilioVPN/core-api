"""Administrator refresh and logout command contracts."""

from typing import Protocol

from src.apps.core.auth.domain.dtos.refresh import TokenRefresh
from src.apps.core.tokens.domain.results.issued import TokenPair


class ITokenRefreshCommand(Protocol):
    async def refresh(self, data: TokenRefresh) -> TokenPair:
        """Rotate one administrator refresh using current account grants.

        Args:
            data: Private refresh credential; caller claims are ignored.

        Returns:
            New access/refresh pair after current account/role/policy reads
            and consumption of the old refresh in one native transaction.
            The new pair retains the same session identity.

        Raises:
            UnAuthorizedException: Token is invalid/reused or account/role
                unavailable. On failure SQL consumption is rolled back.
        """
        ...


class ITokenLogoutCommand(Protocol):
    async def logout(self, data: TokenRefresh) -> None:
        """Close the session of the supplied unused refresh.

        Args:
            data: Private refresh credential; no access or sudo is required.

        Returns:
            None. Repeated revocation leaves other sessions unchanged.

        Raises:
            UnAuthorizedException: Credential verification fails.
        """
        ...
