"""Bind password authentication and authorization in request scope."""

from dishka import Provider, Scope, provide

from src.apps.core.access.auth.app.commands.logout import TokenLogoutCommand
from src.apps.core.access.auth.app.commands.password import (
    PasswordLoginCommand,
)
from src.apps.core.access.auth.app.commands.refresh import TokenRefreshCommand
from src.apps.core.access.auth.app.commands.sessions import (
    SessionRevokeCommand,
    SessionRevokeOthersCommand,
)
from src.apps.core.access.auth.app.interfaces.commands import (
    IPasswordLoginCommand,
    ISessionRevokeCommand,
    ISessionRevokeOthersCommand,
    ITokenLogoutCommand,
    ITokenRefreshCommand,
)
from src.apps.core.access.auth.app.interfaces.services import (
    IAdminIdentityService,
    ISessionService,
)
from src.apps.core.access.auth.app.services.identity import (
    AdminIdentityService,
)
from src.apps.core.access.auth.app.services.sessions import SessionService
from src.apps.core.access.auth.infra.pg.repositories.sessions import (
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
    revoke = provide(SessionRevokeCommand, provides=ISessionRevokeCommand)
    revoke_others = provide(
        SessionRevokeOthersCommand, provides=ISessionRevokeOthersCommand
    )
    refresh = provide(TokenRefreshCommand, provides=ITokenRefreshCommand)
    logout = provide(TokenLogoutCommand, provides=ITokenLogoutCommand)
