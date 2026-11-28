"""Bind WireGuard runtime and egress observations."""

from dishka import Provider, Scope, provide

from .app.interfaces.egress import (
    IWireGuardEgressGateway,
    IWireGuardEgressQuery,
)
from .app.interfaces.logs import IWireGuardLogsGateway, IWireGuardLogsQuery
from .app.interfaces.runtime import (
    IWireGuardRuntimeGateway,
    IWireGuardRuntimeQuery,
)
from .app.queries.egress import WireGuardEgressQuery
from .app.queries.logs import WireGuardLogsQuery
from .app.queries.runtime import WireGuardRuntimeQuery
from .infra.grpc.egress import WireGuardEgressGateway
from .infra.grpc.logs import WireGuardLogsGateway
from .infra.grpc.runtime import WireGuardRuntimeGateway


class WireGuardDiagnosticsProvider(Provider):
    scope = Scope.REQUEST

    runtime_query = provide(
        WireGuardRuntimeQuery, provides=IWireGuardRuntimeQuery
    )
    runtime_gateway = provide(
        WireGuardRuntimeGateway,
        provides=IWireGuardRuntimeGateway,
        scope=Scope.APP,
    )
    egress_query = provide(
        WireGuardEgressQuery, provides=IWireGuardEgressQuery
    )
    egress_gateway = provide(
        WireGuardEgressGateway,
        provides=IWireGuardEgressGateway,
        scope=Scope.APP,
    )
    logs_query = provide(WireGuardLogsQuery, provides=IWireGuardLogsQuery)
    logs_gateway = provide(
        WireGuardLogsGateway, provides=IWireGuardLogsGateway, scope=Scope.APP
    )
