"""Administrator authentication contracts for HTTP and app consumers."""

from typing import Protocol

from src.apps.core.auth.domain.dtos.password import PasswordLogin
from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.tokens.domain.results.records import TokenPair


class IAdminIdentityService(Protocol):
    async def resolve(self, token: str) -> AdminIdentity:
        """Resolve an administrator identity from an access credential.

        Args:
            token: Untrusted encoded access token; never log its value.

        Returns:
            Verified internal user/role IDs and payload scope masks, including
            zero masks. Expected audience is administrator-owned; this does not
            check account/role availability or evaluate scope/sudo permissions.

        Raises:
            UnAuthorizedException: Access verification fails or the verified
                subject or role/scope claim shape is invalid.
        """
        ...


class IPasswordLoginService(Protocol):
    async def login(self, data: PasswordLogin) -> TokenPair:
        """Authenticate an active administrator and issue credentials.

        Args:
            data: Mobile and raw password supplied by the caller.

        Returns:
            Access and refresh credentials with actual UTC-aware expirations.
            The account owner selects the administrator audience and assembles
            role and active scope claims for the access credential only.

        Raises:
            UnAuthorizedException: Credentials are invalid, the account has no
                usable password hash, or its account/role is unavailable.
        """
        ...
