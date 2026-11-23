"""Bind password authentication and authorization in request scope."""

from dishka import Provider, Scope, provide

from src.apps.core.auth.app.commands.logout import TokenLogoutCommand
from src.apps.core.auth.app.commands.refresh import TokenRefreshCommand
from src.apps.core.auth.app.interfaces.commands import (
    ITokenLogoutCommand,
    ITokenRefreshCommand,
)
from src.apps.core.auth.app.interfaces.services import (
    IAdminIdentityService,
    IPasswordLoginService,
)
from src.apps.core.auth.app.services.identity import AdminIdentityService
from src.apps.core.auth.app.services.password import PasswordLoginService
from src.apps.core.auth.app.services.sessions import SessionService
from src.apps.core.auth.infra.pg.repositories.sessions import (
    SessionRepository,
)


class AuthProvider(Provider):
    scope = Scope.REQUEST

    identity = provide(AdminIdentityService, provides=IAdminIdentityService)
    password_login = provide(
        PasswordLoginService, provides=IPasswordLoginService
    )
    session_repo = provide(SessionRepository)
    sessions = provide(SessionService)
    refresh = provide(TokenRefreshCommand, provides=ITokenRefreshCommand)
    logout = provide(TokenLogoutCommand, provides=ITokenLogoutCommand)
