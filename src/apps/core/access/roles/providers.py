"""Bind role reads, writes and commands to the native request lifetime."""

from dishka import Provider, Scope, provide

from src.apps.core.access.roles.app.commands.remove import RoleRemoveCommand
from src.apps.core.access.roles.app.commands.role_scopes import (
    RoleScopeBatchCreateCommand,
    RoleScopeBatchUpdateCommand,
    RoleScopeCreateCommand,
    RoleScopeRemoveCommand,
    RoleScopeUpdateCommand,
)
from src.apps.core.access.roles.app.interfaces.commands import (
    IRoleRemoveCommand,
    IRoleScopeBatchCreateCommand,
    IRoleScopeBatchUpdateCommand,
    IRoleScopeCreateCommand,
    IRoleScopeRemoveCommand,
    IRoleScopeUpdateCommand,
)
from src.apps.core.access.roles.app.interfaces.queries import IRoleQuery
from src.apps.core.access.roles.app.interfaces.services import (
    IRoleScopeService,
    IRoleService,
)
from src.apps.core.access.roles.app.queries.records import RoleQuery
from src.apps.core.access.roles.app.services.crud import RoleService
from src.apps.core.access.roles.app.services.role_scopes import (
    RoleScopeService,
)
from src.apps.core.access.roles.infra.pg.repositories.crud import (
    RoleRepository,
)
from src.apps.core.access.roles.infra.pg.repositories.reader import RoleReader
from src.apps.core.access.roles.infra.pg.repositories.role_scopes import (
    RoleScopeRepository,
)


class RoleProvider(Provider):
    scope = Scope.REQUEST

    roles = provide(RoleRepository)
    assignments = provide(RoleScopeRepository)
    reader = provide(RoleReader)
    role_service = provide(RoleService, provides=IRoleService)
    assignment_service = provide(RoleScopeService, provides=IRoleScopeService)
    query = provide(RoleQuery, provides=IRoleQuery)
    create_command = provide(
        RoleScopeCreateCommand, provides=IRoleScopeCreateCommand
    )
    update_command = provide(
        RoleScopeUpdateCommand, provides=IRoleScopeUpdateCommand
    )
    remove_scope = provide(
        RoleScopeRemoveCommand, provides=IRoleScopeRemoveCommand
    )
    create_batch_command = provide(
        RoleScopeBatchCreateCommand, provides=IRoleScopeBatchCreateCommand
    )
    update_batch_command = provide(
        RoleScopeBatchUpdateCommand, provides=IRoleScopeBatchUpdateCommand
    )
    remove_command = provide(RoleRemoveCommand, provides=IRoleRemoveCommand)
