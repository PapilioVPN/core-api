"""Register Hysteria log selection and the native streaming adapter."""

from dishka import Provider, Scope, provide

from .app.interfaces.logs import IHysteriaLogsGateway, IHysteriaLogsQuery
from .app.queries.logs import HysteriaLogsQuery
from .infra.grpc.logs import HysteriaLogsGateway


class HysteriaLogsProvider(Provider):
    scope = Scope.REQUEST

    query = provide(HysteriaLogsQuery, provides=IHysteriaLogsQuery)
    gateway = provide(
        HysteriaLogsGateway, provides=IHysteriaLogsGateway, scope=Scope.APP
    )
