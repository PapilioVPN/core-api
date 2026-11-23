"""Bind password authentication and authorization in request scope."""

from dishka import Provider, Scope, provide

from src.apps.core.auth.app.commands.logout import TokenLogoutCommand
from src.apps.core.auth.app.commands.password import PasswordLoginCommand
from src.apps.core.auth.app.commands.refresh import TokenRefreshCommand
from src.apps.core.auth.app.commands.sessions import SessionCommand
from src.apps.core.auth.app.interfaces.commands import (
    IPasswordLoginCommand,
    ISessionCommand,
    ITokenLogoutCommand,
    ITokenRefreshCommand,
)
from src.apps.core.auth.app.interfaces.services import (
    IAdminIdentityService,
    ISessionService,
)
from src.apps.core.auth.app.services.identity import AdminIdentityService
from src.apps.core.auth.app.services.sessions import SessionService
from src.apps.core.auth.infra.pg.repositories.sessions import (
    SessionRepository,
)


class AuthProvider(Provider):
    scope = Scope.REQUEST

    identity = provide(AdminIdentityService, provides=IAdminIdentityService)
    password_login = provide(
        PasswordLoginCommand, provides=IPasswordLoginCommand
    )
    session_repo = provide(SessionRepository)
    sessions = provide(SessionService, provides=ISessionService)
    session_command = provide(SessionCommand, provides=ISessionCommand)
    refresh = provide(TokenRefreshCommand, provides=ITokenRefreshCommand)
    logout = provide(TokenLogoutCommand, provides=ITokenLogoutCommand)
