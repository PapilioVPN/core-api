"""Bind customer group operations to Papilio's request scope."""

from dishka import Provider, Scope, provide

from .app.interfaces.services import IGroupCRUD
from .app.services.crud import GroupCRUD
from .infra.pg.repositories.crud import GroupRepository


class GroupProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(GroupRepository)
    crud = provide(GroupCRUD, provides=IGroupCRUD)
