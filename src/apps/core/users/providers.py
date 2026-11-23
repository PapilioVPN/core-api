"""Bind user persistence and focused commands to the native request scope."""

from dishka import Provider, Scope, provide

from src.apps.core.users.app.commands.create import UserCreateCommand
from src.apps.core.users.app.commands.owner import OwnerCommand
from src.apps.core.users.app.commands.password import (
    UserPasswordCommand,
)
from src.apps.core.users.app.commands.profile import UserProfileCommand
from src.apps.core.users.app.commands.role import UserRoleCommand
from src.apps.core.users.app.interfaces.commands import (
    IUserCreateCommand,
    IUserPasswordCommand,
    IUserProfileCommand,
    IUserRoleCommand,
)
from src.apps.core.users.app.interfaces.services import (
    IUserProfileService,
    IUserService,
)
from src.apps.core.users.app.services.profile import UserProfileService
from src.apps.core.users.app.services.records import UserService
from src.apps.core.users.infra.pg.repositories.records import (
    UserRepository,
)


class UserProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(UserRepository, scope=Scope.REQUEST)
    owner = provide(OwnerCommand, scope=Scope.REQUEST)
    service = provide(UserService, provides=IUserService, scope=Scope.REQUEST)
    profile = provide(
        UserProfileService, provides=IUserProfileService, scope=Scope.REQUEST
    )
    profile_command = provide(
        UserProfileCommand, provides=IUserProfileCommand, scope=Scope.REQUEST
    )
    create_command = provide(
        UserCreateCommand, provides=IUserCreateCommand, scope=Scope.REQUEST
    )
    role_command = provide(
        UserRoleCommand, provides=IUserRoleCommand, scope=Scope.REQUEST
    )
    password_command = provide(
        UserPasswordCommand, provides=IUserPasswordCommand, scope=Scope.REQUEST
    )
