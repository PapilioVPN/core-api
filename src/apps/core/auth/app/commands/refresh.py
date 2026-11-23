"""Rotate refresh credentials with current administrator permissions."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.auth.app.helpers.identity import admin_token_identity
from src.apps.core.auth.app.services.sessions import SessionService
from src.apps.core.auth.app.validators.identity import (
    parse_admin_subject,
    require_session_id,
)
from src.apps.core.auth.app.validators.password import (
    require_active_role,
    require_active_user,
)
from src.apps.core.auth.domain.dtos.refresh import TokenRefresh
from src.apps.core.roles.app.interfaces.queries import IRoleQuery
from src.apps.core.tokens.app.interfaces.refresh import (
    IRefreshUseService,
)
from src.apps.core.tokens.app.interfaces.services import ITokenService
from src.apps.core.tokens.domain.results.records import TokenPair
from src.apps.core.users.app.interfaces.services import IUserService


class TokenRefreshCommand:
    def __init__(
        self,
        users: IUserService,
        roles: IRoleQuery,
        tokens: ITokenService,
        uses: IRefreshUseService,
        sessions: SessionService,
    ) -> None:
        """Bind existing account, grants, credential and consumption owners.

        Args:
            users: Current authoritative administrator records.
            roles: Current role details and scope activity/permission masks.
            tokens: Shared refresh verification and configured pair issuance.
            uses: Atomic one-time consumption in the same request's SQL UoW.
            sessions: Persistent administrator session owner.

        Returns:
            None.
        """
        self.users = users
        self.roles = roles
        self.tokens = tokens
        self.uses = uses
        self.sessions = sessions

    @transactional
    async def refresh(self, data: TokenRefresh) -> TokenPair:
        """Consume one refresh and issue current administrator credentials.

        Args:
            data: Private refresh credential, independent of Bearer expiry.

        Returns:
            New pair with fresh token IDs and the same active session.
            Nested callers must wait for their owning transaction to commit
            before using the provisional credentials. No sudo is issued.

        Raises:
            UnAuthorizedException: Refresh rejected or account unavailable.
            Exception: Policy/signing/SQL failures and cancellation propagate;
                SQL rollback leaves the prior credential unconsumed.
        """
        verified = await self.tokens.verify_refresh(
            data.refresh_token, audience="admin"
        )
        user_id = parse_admin_subject(verified)
        session_id = require_session_id(verified)
        user = require_active_user(await self.users.find_access(user_id))
        role = require_active_role(
            await self.roles.find_access(user.role_id),
            super_admin=user.is_super_admin,
        )
        await self.uses.consume(verified)
        result = await self.tokens.issue(
            admin_token_identity(user.id, role, session_id)
        )
        await self.sessions.rotate(
            user.id, session_id, expires_at=result.refresh_expires_at
        )
        return result
