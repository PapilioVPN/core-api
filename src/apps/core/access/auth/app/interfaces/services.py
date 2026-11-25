"""Administrator authentication contracts for HTTP and app consumers."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from papilio.schemas.results import PagedType

from src.apps.core.access.auth.domain.dtos.sessions import SessionList
from src.apps.core.access.auth.domain.models.sessions import SessionModel
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.domain.results.sessions import SessionResult


class IAdminIdentityService(Protocol):
    async def resolve(self, token: str) -> AdminIdentity:
        """Resolve an administrator identity from an access credential.

        Args:
            token: Untrusted encoded access token; never log its value.

        Returns:
            Verified account and session IDs with the current role and scopes.

        Raises:
            UnAuthorizedException: Token, session or account is unavailable.
        """
        ...


class ISessionService(Protocol):
    async def create(
        self,
        user_id: int,
        id: UUID,
        *,
        expires_at: datetime,
        user_agent: str | None,
    ) -> SessionModel: ...

    async def require(self, user_id: int, id: UUID) -> None: ...

    async def rotate(
        self, user_id: int, id: UUID, *, expires_at: datetime
    ) -> SessionModel: ...

    async def list(
        self, identity: AdminIdentity, query: SessionList
    ) -> PagedType[SessionResult]: ...

    async def revoke(self, user_id: int, id: UUID) -> bool: ...

    async def revoke_others(self, user_id: int, id: UUID) -> int: ...

    async def remove_expired(self, *, limit: int = 100) -> int: ...
