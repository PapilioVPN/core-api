"""Bind the Hysteria capability to native application discovery."""

from dishka import Provider, Scope, provide

from .app.interfaces.status import IHysteriaStatusGateway, IHysteriaStatusQuery
from .app.queries.status import HysteriaStatusQuery
from .infra.grpc.status import HysteriaStatusGateway


class HysteriaInstancesProvider(Provider):
    scope = Scope.REQUEST

    query = provide(HysteriaStatusQuery, provides=IHysteriaStatusQuery)
    status_gateway = provide(
        HysteriaStatusGateway, provides=IHysteriaStatusGateway, scope=Scope.APP
    )
