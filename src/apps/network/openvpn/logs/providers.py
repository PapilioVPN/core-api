"""Register OpenVPN log selection and the native streaming adapter."""

from dishka import Provider, Scope, provide

from .app.interfaces.logs import IOpenVPNLogsGateway, IOpenVPNLogsQuery
from .app.queries.logs import OpenVPNLogsQuery
from .infra.grpc.logs import OpenVPNLogsGateway


class OpenVPNLogsProvider(Provider):
    scope = Scope.REQUEST

    query = provide(OpenVPNLogsQuery, provides=IOpenVPNLogsQuery)
    gateway = provide(
        OpenVPNLogsGateway, provides=IOpenVPNLogsGateway, scope=Scope.APP
    )
