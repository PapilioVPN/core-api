"""Resolve an administrator against their live session and grants."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.auth.app.helpers.identity import active_scopes
from src.apps.core.auth.app.services.sessions import SessionService
from src.apps.core.auth.app.validators.identity import (
    parse_admin_subject,
    require_session_id,
)
from src.apps.core.auth.app.validators.password import (
    require_active_role,
    require_active_user,
)
from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.roles.app.interfaces.queries import IRoleQuery
from src.apps.core.tokens.app.interfaces.services import ITokenService
from src.apps.core.users.app.interfaces.services import IUserService


class AdminIdentityService:
    def __init__(
        self,
        tokens: ITokenService,
        sessions: SessionService,
        users: IUserService,
        roles: IRoleQuery,
    ) -> None:
        self.tokens = tokens
        self.sessions = sessions
        self.users = users
        self.roles = roles

    @transactional
    async def resolve(self, token: str) -> AdminIdentity:
        """Verify an access token and read the current grants from PostgreSQL.

        Args:
            token: Untrusted access credential; never log its value.

        Returns:
            The active account, owned session and current role permissions.

        Raises:
            UnAuthorizedException: Token, session or account is unavailable.
        """
        verified = await self.tokens.verify_access(token, audience="admin")
        user_id = parse_admin_subject(verified)
        session_id = require_session_id(verified)
        await self.sessions.require(user_id, session_id)
        user = require_active_user(await self.users.find_by_id(user_id))
        role = require_active_role(
            await self.roles.find_by_id(user.role_id),
            super_admin=user.is_super_admin,
        )
        result = AdminIdentity(
            user_id=user_id,
            role_id=role.id,
            scopes=active_scopes(role),
            session_id=session_id,
            is_super_admin=user.is_super_admin,
        )
        return result
