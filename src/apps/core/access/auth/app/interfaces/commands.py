"""Administrator credential and session commands."""

from typing import Protocol
from uuid import UUID

from src.apps.core.access.auth.domain.dtos.password import PasswordLogin
from src.apps.core.access.auth.domain.dtos.refresh import TokenRefresh
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.tokens.domain.results.issued import TokenPair


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


class IPasswordLoginCommand(Protocol):
    async def login(
        self, data: PasswordLogin, *, user_agent: str | None
    ) -> TokenPair:
        """Authenticate an active administrator and issue credentials.

        Args:
            data: Mobile and raw password supplied by the caller.
            user_agent: Optional client label recorded with the session.

        Returns:
            Access and refresh credentials with actual UTC-aware expirations.
            The account owner selects the administrator audience and assembles
            role and active scope claims for the access credential only.

        Raises:
            UnAuthorizedException: Credentials are invalid, the account has no
                usable password hash, or its account/role is unavailable.
        """
        ...


class ISessionRevokeCommand(Protocol):
    async def revoke(self, user_id: int, id: UUID) -> bool: ...


class ISessionRevokeOthersCommand(Protocol):
    async def revoke_others(self, identity: AdminIdentity) -> int: ...
