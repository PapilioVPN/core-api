"""Coordinate session revocation and its audit events."""

from uuid import UUID

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.access.audit.app.interfaces.records import IAuditWriter
from src.apps.core.access.audit.domain.dtos.event import AuditEvent
from src.apps.core.access.audit.domain.enums.actions import AuditAction
from src.apps.core.access.auth.app.interfaces.services import ISessionService
from src.apps.core.access.auth.domain.results.identity import AdminIdentity


class SessionRevokeCommand:
    def __init__(self, sessions: ISessionService, audit: IAuditWriter) -> None:
        """Bind storage and audit operations in the same request.

        Args:
            sessions: Authoritative administrator session service.
            audit: Writer on the same PostgreSQL UoW.

        Returns:
            None.
        """
        self.sessions = sessions
        self.audit = audit

    @transactional
    async def revoke(self, user_id: int, id: UUID) -> bool:
        """Close one owned active session and append its audit event.

        Args:
            user_id: Verified owner account.
            id: Session UUID.

        Returns:
            True if the session was active and is now closed.
        """
        revoked = await self.sessions.revoke(user_id, id)
        if revoked:
            await self.audit.record(
                user_id, AuditEvent(AuditAction.SESSION_REVOKE, id)
            )
        return revoked


class SessionRevokeOthersCommand:
    def __init__(self, sessions: ISessionService, audit: IAuditWriter) -> None:
        """Bind session records and audit on the same request."""
        self.sessions = sessions
        self.audit = audit

    @transactional
    async def revoke_others(self, identity: AdminIdentity) -> int:
        """Close other active sessions for this account.

        Args:
            identity: Authenticated account and session to preserve.

        Returns:
            Count of sessions closed.
        """
        count = await self.sessions.revoke_others(
            identity.user_id, identity.session_id
        )
        if count:
            await self.audit.record(
                identity.user_id,
                AuditEvent(
                    AuditAction.SESSION_REVOKE_OTHERS,
                    identity.user_id,
                    count=count,
                ),
            )
        return count
