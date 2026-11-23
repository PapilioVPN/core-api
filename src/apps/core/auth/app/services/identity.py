"""Administrator token identity through the shared JWT service."""

from src.apps.core.auth.app.validators.identity import (
    parse_admin_identity,
)
from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.tokens.app.interfaces.services import ITokenService


class AdminIdentityService:
    def __init__(self, tokens: ITokenService) -> None:
        """Bind the existing token-verification owner.

        Args:
            tokens: Shared request-scoped token service.

        Returns:
            None.
        """
        self.tokens = tokens

    async def resolve(self, token: str) -> AdminIdentity:
        """Verify admin access and preserve its permission claims.

        Args:
            token: Untrusted access credential; never log its value.

        Returns:
            Verified user/role identities and the payload's scope masks.
            Consumers check current account/role availability separately.

        Raises:
            UnAuthorizedException: Verification or account-ID adaptation fails.
            Exception: Backend failures and cancellation propagate unchanged.
        """
        verified = await self.tokens.verify_access(token, audience="admin")
        result = parse_admin_identity(verified)
        return result
