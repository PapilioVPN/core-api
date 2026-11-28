"""Bind the OpenVPN capability to native application discovery."""

from dishka import Provider, Scope, provide

from .app.interfaces.status import IOpenVPNStatusGateway, IOpenVPNStatusQuery
from .app.queries.status import OpenVPNStatusQuery
from .infra.grpc.status import OpenVPNStatusGateway


class OpenVPNInstancesProvider(Provider):
    scope = Scope.REQUEST

    query = provide(OpenVPNStatusQuery, provides=IOpenVPNStatusQuery)
    status_gateway = provide(
        OpenVPNStatusGateway, provides=IOpenVPNStatusGateway, scope=Scope.APP
    )
