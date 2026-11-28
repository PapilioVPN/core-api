"""Register the live-log query and its shared streaming gateway."""

from dishka import Provider, Scope, provide

from .app.interfaces.live import IXrayLogsGateway, IXrayLogsQuery
from .app.queries.live import XrayLogsQuery
from .infra.grpc.live import XrayLogsGateway


class XrayLogsProvider(Provider):
    scope = Scope.REQUEST

    query = provide(XrayLogsQuery, provides=IXrayLogsQuery)
    gateway = provide(
        XrayLogsGateway, provides=IXrayLogsGateway, scope=Scope.APP
    )
