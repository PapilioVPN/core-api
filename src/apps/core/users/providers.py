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

    repository = provide(UserRepository)
    owner = provide(OwnerCommand)
    service = provide(UserService, provides=IUserService)
    profile = provide(UserProfileService, provides=IUserProfileService)
    profile_command = provide(UserProfileCommand, provides=IUserProfileCommand)
    create_command = provide(UserCreateCommand, provides=IUserCreateCommand)
    role_command = provide(UserRoleCommand, provides=IUserRoleCommand)
    password_command = provide(
        UserPasswordCommand, provides=IUserPasswordCommand
    )
