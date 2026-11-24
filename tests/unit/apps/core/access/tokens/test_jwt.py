"""Keep JWT validation at the installed native signing boundary."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from papilio.core.config import JWTConfig
from papilio.errors.exceptions import UnAuthorizedException
from papilio.security.tokens import TokenType, create_token

from src.apps.core.access.tokens.domain.models.tokens import TokenIdentity
from src.apps.core.access.tokens.infra.jwt.codec import JWTCodec

pytestmark = pytest.mark.unit


@pytest.fixture
def config() -> JWTConfig:
    return JWTConfig(
        algorithm="HS256",
        secret_key="isolated-jwt-test-signing-key-0123456789",
        api_secret="isolated-jwt-test-api-secret",
        access_token_expire_minutes=15,
    )


@pytest.mark.parametrize("kind", [TokenType.ACCESS, TokenType.REFRESH])
def test_session_claim(config: JWTConfig, kind: TokenType) -> None:
    codec = JWTCodec(config)
    session_id = uuid4()
    identity = TokenIdentity("41", "admin", {"role_id": 2}, session_id)
    issued = codec.encode(identity, kind=kind, expires_in=timedelta(minutes=1))
    verified = codec.decode(issued.token, audience="admin", kind=kind)

    assert verified.identity.session_id == session_id
    expected = identity.claims if kind == TokenType.ACCESS else {}
    assert verified.identity.claims == expected
    assert verified.expires_at == issued.expires_at


@pytest.mark.parametrize(
    "invalid",
    [{"sid": "invalid-session"}, {"data": []}, {"jti": ""}],
)
def test_signed_access_requires_typed_claims(
    config: JWTConfig, invalid: dict[str, object]
) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    expires = now + timedelta(minutes=1)
    token = create_token(
        "41",
        config.secret_key,
        expires_in=timedelta(minutes=1),
        extra_claims={
            "aud": "admin",
            "data": {},
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            **invalid,
        },
    )

    with pytest.raises(UnAuthorizedException):
        JWTCodec(config).decode(token, audience="admin", kind=TokenType.ACCESS)
