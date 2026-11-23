"""Invalidate the supplied administrator refresh credential."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.auth.app.validators.identity import (
    parse_admin_subject,
)
from src.apps.core.auth.domain.dtos.refresh import TokenRefresh
from src.apps.core.tokens.app.interfaces.refresh import (
    IRefreshUseService,
)
from src.apps.core.tokens.app.interfaces.services import ITokenService


class TokenLogoutCommand:
    def __init__(
        self, tokens: ITokenService, uses: IRefreshUseService
    ) -> None:
        """Bind credential verification and refresh-consumption persistence.

        Args:
            tokens: Shared credential verification owner.
            uses: Request-local consumption service on the same SQL UoW.

        Returns:
            None.
        """
        self.tokens = tokens
        self.uses = uses

    @transactional
    async def logout(self, data: TokenRefresh) -> None:
        """Revoke one refresh, including an already consumed credential.

        Args:
            data: Private refresh credential; Bearer and sudo are not required.

        Returns:
            None after revocation; repeated requests leave history unchanged.
            Access, sudo and other refresh credentials retain their validity.
            Nested callers retain ownership of the final SQL commit.

        Raises:
            UnAuthorizedException: Invalid, expired or non-admin refresh.
            Exception: SQL/commit failures and cancellation propagate.
        """
        verified = await self.tokens.verify_refresh(
            data.refresh_token, audience="admin"
        )
        parse_admin_subject(verified)
        await self.uses.revoke(verified)
