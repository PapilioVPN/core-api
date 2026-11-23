"""Bind role reads, writes and commands to the native request lifetime."""

from dishka import Provider, Scope, provide

from src.apps.core.roles.app.commands.remove import RoleRemoveCommand
from src.apps.core.roles.app.commands.role_scopes import (
    RoleScopeCommand,
)
from src.apps.core.roles.app.interfaces.commands import (
    IRoleRemoveCommand,
    IRoleScopeCommand,
)
from src.apps.core.roles.app.interfaces.queries import IRoleQuery
from src.apps.core.roles.app.interfaces.services import (
    IRoleScopeService,
    IRoleService,
)
from src.apps.core.roles.app.queries.records import RoleQuery
from src.apps.core.roles.app.services.records import RoleService
from src.apps.core.roles.app.services.role_scopes import (
    RoleScopeService,
)
from src.apps.core.roles.infra.pg.repositories.reader import RoleReader
from src.apps.core.roles.infra.pg.repositories.records import (
    RoleRepository,
)
from src.apps.core.roles.infra.pg.repositories.role_scopes import (
    RoleScopeRepository,
)


class RoleProvider(Provider):
    scope = Scope.REQUEST

    roles = provide(RoleRepository, scope=Scope.REQUEST)
    assignments = provide(RoleScopeRepository, scope=Scope.REQUEST)
    reader = provide(RoleReader, scope=Scope.REQUEST)
    role_service = provide(
        RoleService, provides=IRoleService, scope=Scope.REQUEST
    )
    assignment_service = provide(
        RoleScopeService, provides=IRoleScopeService, scope=Scope.REQUEST
    )
    query = provide(RoleQuery, provides=IRoleQuery, scope=Scope.REQUEST)
    command = provide(
        RoleScopeCommand, provides=IRoleScopeCommand, scope=Scope.REQUEST
    )
    remove_command = provide(
        RoleRemoveCommand, provides=IRoleRemoveCommand, scope=Scope.REQUEST
    )
