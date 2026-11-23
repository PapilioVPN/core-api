"""Shared asynchronous token operations over the standalone JWT codec."""

from datetime import timedelta

from papilio.core.config import JWTConfig
from papilio.security.tokens import TokenType

from src.apps.core.tokens.domain.models.tokens import (
    TokenIdentity,
    VerifiedToken,
)
from src.apps.core.tokens.domain.results.records import TokenPair
from src.apps.core.tokens.infra.tokens.jwt import JWTCodec


class TokenService:
    """Issue and verify credentials through the standalone JWT codec."""

    def __init__(
        self,
        codec: JWTCodec,
        config: JWTConfig,
    ) -> None:
        """Bind signing infrastructure and the owning policy service.

        Args:
            codec: Configured standalone JWT signing/verification owner.
            config: Native configured token lifetimes.

        Returns:
            None.
        """
        self.codec = codec
        self.config = config

    async def issue(self, identity: TokenIdentity) -> TokenPair:
        """Issue two credentials for an identity approved by its account owner.

        Args:
            identity: Trusted subject, audience and owner-built access claims.

        Returns:
            Access/refresh credentials with their actual UTC-aware expirations.
            Refresh contains identity only; no session is created here.

        Raises:
            PyJWTError: The codec cannot sign a credential.
        """
        access = self.codec.encode(
            identity,
            kind=TokenType.ACCESS,
            expires_in=timedelta(
                minutes=self.config.access_token_expire_minutes
            ),
        )
        refresh = self.codec.encode(
            identity,
            kind=TokenType.REFRESH,
            expires_in=timedelta(
                minutes=self.config.refresh_token_expire_minutes
            ),
        )
        result = TokenPair(
            access_token=access.token,
            refresh_token=refresh.token,
            access_expires_at=access.expires_at,
            refresh_expires_at=refresh.expires_at,
        )
        return result

    async def verify_access(
        self, token: str, *, audience: str
    ) -> VerifiedToken:
        """Verify access credentials for an explicitly selected consumer.

        Args:
            token: Untrusted encoded access token; never log its value.
            audience: Expected consumer supplied by the owning application.

        Returns:
            Verified identity, owner claims and actual UTC-aware timestamps.

        Raises:
            UnAuthorizedException: The credential fails JWT verification.
        """
        result = self.codec.decode(
            token, audience=audience, kind=TokenType.ACCESS
        )
        return result

    async def verify_refresh(
        self, token: str, *, audience: str
    ) -> VerifiedToken:
        """Verify refresh credentials without renewal or account checks.

        Args:
            token: Untrusted encoded refresh token; never log its value.
            audience: Expected consumer supplied by the owning application.

        Returns:
            Verified identity without owner claims, and UTC-aware timestamps.

        Raises:
            UnAuthorizedException: The credential fails JWT verification.
        """
        result = self.codec.decode(
            token, audience=audience, kind=TokenType.REFRESH
        )
        return result
