"""Bind customer group operations to Papilio's request scope."""

from dishka import Provider, Scope, provide

from .app.interfaces.services import ICustomerGroupService
from .app.services.crud import CustomerGroupService
from .infra.pg.repositories.crud import CustomerGroupRepository


class GroupProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CustomerGroupRepository)
    service = provide(CustomerGroupService, provides=ICustomerGroupService)
