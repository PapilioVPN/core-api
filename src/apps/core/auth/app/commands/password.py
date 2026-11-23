"""Administrator password login through the owning application interfaces."""

from uuid import uuid4

from papilio.security.passwords import PasswordHasher

from src.apps.core.auth.app.helpers.identity import admin_token_identity
from src.apps.core.auth.app.interfaces.services import ISessionService
from src.apps.core.auth.app.validators.password import (
    require_active_role,
    require_active_user,
    require_password_hash,
    validate_password_match,
)
from src.apps.core.auth.domain.dtos.password import PasswordLogin
from src.apps.core.roles.app.interfaces.queries import IRoleQuery
from src.apps.core.tokens.app.interfaces.services import ITokenService
from src.apps.core.tokens.domain.results.issued import TokenPair
from src.apps.core.users.app.interfaces.services import IUserService


class PasswordLoginCommand:
    def __init__(
        self,
        users: IUserService,
        roles: IRoleQuery,
        hasher: PasswordHasher,
        tokens: ITokenService,
        sessions: ISessionService,
    ) -> None:
        """Bind account, role, native password and token owners.

        Args:
            users: Authoritative mobile-based account reader.
            roles: Materialized role and stored scope-permission reader.
            hasher: Configured native password verifier; bcrypt runs off-loop.
            tokens: Shared credential issuer with current lifetime settings.
            sessions: Persistent administrator session owner.

        Returns:
            None.
        """
        self.users = users
        self.roles = roles
        self.hasher = hasher
        self.tokens = tokens
        self.sessions = sessions

    async def login(
        self, data: PasswordLogin, *, user_agent: str | None
    ) -> TokenPair:
        """Verify administrator credentials and issue current access claims.

        Args:
            data: Validated mobile and private raw password.
            user_agent: Optional bounded HTTP client label.

        Returns:
            Issued access/refresh pair with actual UTC-aware expirations.
            Access carries the role ID and active scope masks, including zero.
            Refresh carries no role or scopes.

        Raises:
            UnAuthorizedException: User/role is absent or inactive, or the
                password is absent, malformed or incorrect.
            Exception: Read, hashing and issuance failures propagate unchanged.
        """
        user = await self.users.find_by_mobile(data.mobile)
        user = require_active_user(user)
        password_hash = require_password_hash(user.hashed_password)
        matches = await self.hasher.verify(data.password, password_hash)
        validate_password_match(matches)
        role = await self.roles.find_access(user.role_id)
        role = require_active_role(role, super_admin=user.is_super_admin)
        session_id = uuid4()
        identity = admin_token_identity(user.id, role, session_id)
        result = await self.tokens.issue(identity)
        await self.sessions.create(
            user.id,
            session_id,
            expires_at=result.refresh_expires_at,
            user_agent=user_agent,
        )
        return result
