"""Close the administrator session identified by an unused refresh token."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.access.auth.app.interfaces.commands import (
    ISessionRevokeCommand,
)
from src.apps.core.access.auth.app.validators.identity import (
    parse_admin_subject,
    require_session_id,
)
from src.apps.core.access.auth.domain.dtos.refresh import TokenRefresh
from src.apps.core.access.tokens.app.interfaces.refresh import (
    IRefreshUseService,
)
from src.apps.core.access.tokens.app.interfaces.services import ITokenService


class TokenLogoutCommand:
    def __init__(
        self,
        tokens: ITokenService,
        uses: IRefreshUseService,
        sessions: ISessionRevokeCommand,
    ) -> None:
        """Bind credential verification and refresh-consumption persistence.

        Args:
            tokens: Shared credential verification owner.
            uses: Request-local consumption service on the same SQL UoW.
            sessions: Persistent administrator session owner.

        Returns:
            None.
        """
        self.tokens = tokens
        self.uses = uses
        self.sessions = sessions

    @transactional
    async def logout(self, data: TokenRefresh) -> None:
        """Close the session using its unused refresh credential.

        Args:
            data: Private refresh credential; Bearer and sudo are not required.

        Returns:
            None after closing the session. A repeated or rotated refresh
            credential leaves the session state unchanged.

        Raises:
            UnAuthorizedException: Invalid, expired or non-admin refresh.
            Exception: SQL/commit failures and cancellation propagate.
        """
        verified = await self.tokens.verify_refresh(
            data.refresh_token, audience="admin"
        )
        user_id = parse_admin_subject(verified)
        session_id = require_session_id(verified)
        if await self.uses.revoke(verified):
            await self.sessions.revoke(user_id, session_id)
