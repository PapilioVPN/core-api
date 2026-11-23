"""Bind native signing configuration and refresh history to their scopes."""

from dishka import Provider, Scope, provide
from papilio.core.config import JWTConfig, Settings

from src.apps.core.tokens.app.interfaces.refresh import IRefreshUseService
from src.apps.core.tokens.app.interfaces.services import ITokenService
from src.apps.core.tokens.app.services.refresh import RefreshUseService
from src.apps.core.tokens.app.services.tokens import TokenService
from src.apps.core.tokens.infra.pg.repositories.refresh import (
    RefreshUseRepository,
)
from src.apps.core.tokens.infra.tokens.jwt import JWTCodec


class TokensProvider(Provider):
    @provide(scope=Scope.APP)
    def jwt_settings(self, settings: Settings) -> JWTConfig:
        """Resolve the native JWT configuration supplied by the application."""
        config = settings.jwt
        if config is None:
            raise ValueError("JWT configuration is required")
        return config

    codec = provide(JWTCodec, scope=Scope.APP)
    tokens = provide(TokenService, provides=ITokenService, scope=Scope.APP)
    refresh_repo = provide(RefreshUseRepository, scope=Scope.REQUEST)
    refresh_use = provide(
        RefreshUseService, provides=IRefreshUseService, scope=Scope.REQUEST
    )
