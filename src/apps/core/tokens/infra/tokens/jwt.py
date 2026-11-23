"""Administrator JWT claims over Papilio's native signing and verification."""

from datetime import UTC, datetime, timedelta

from papilio.core import resources
from papilio.core.config import JWTConfig
from papilio.errors.exceptions import UnAuthorizedException
from papilio.security.tokens import TokenType, create_token, decode_token
from pydantic import JsonValue, ValidationError

from src.apps.core.tokens.domain.models.tokens import (
    TokenIdentity,
    VerifiedToken,
)
from src.apps.core.tokens.domain.results.records import IssuedToken
from src.apps.core.tokens.infra.tokens.schemas.jwt import JWTPayload


class JWTCodec:
    def __init__(self, config: JWTConfig) -> None:
        """Bind native JWT settings for application-owned credentials."""
        self.config = config

    def encode(
        self,
        identity: TokenIdentity,
        *,
        kind: TokenType,
        expires_in: timedelta,
    ) -> IssuedToken:
        """Sign typed owner claims and return the exact wire expiration."""
        now = datetime.now(UTC).replace(microsecond=0)
        expires_at = now + expires_in
        claims: dict[str, JsonValue] = {
            "aud": identity.audience,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        if kind == TokenType.ACCESS:
            claims["data"] = identity.claims
        if identity.session_id is not None:
            claims["sid"] = str(identity.session_id)
        token = create_token(
            identity.subject,
            self.config.secret_key,
            expires_in=expires_in,
            token_type=kind,
            algorithm=self.config.algorithm,
            extra_claims=claims,
        )
        return IssuedToken(token=token, expires_at=expires_at)

    def decode(
        self, token: str, *, audience: str, kind: TokenType
    ) -> VerifiedToken:
        """Verify the native credential and adapt the reference claim shape."""
        raw = decode_token(
            token,
            self.config.secret_key,
            algorithm=self.config.algorithm,
            expected_type=kind,
            audience=audience,
        )
        try:
            payload = JWTPayload.model_validate(raw)
            if (
                payload.exp <= payload.iat
                or payload.aud != audience
                or ("data" in raw) != (kind == TokenType.ACCESS)
            ):
                raise ValueError("Invalid token claims")
            result = VerifiedToken(
                identity=TokenIdentity(
                    subject=payload.sub,
                    audience=payload.aud,
                    claims=payload.data,
                    session_id=payload.sid,
                ),
                token_id=payload.jti,
                issued_at=datetime.fromtimestamp(payload.iat, UTC),
                expires_at=datetime.fromtimestamp(payload.exp, UTC),
            )
        except (ValidationError, ValueError, OverflowError, OSError) as exc:
            raise UnAuthorizedException(
                message="Invalid authentication token",
                message_code=resources.INVALID_TOKEN,
            ) from exc
        return result
