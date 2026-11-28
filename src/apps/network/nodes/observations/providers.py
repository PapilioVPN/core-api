"""Bind live scalar and fleet host observations."""

from dishka import Provider, Scope, provide

from .app.interfaces.host import (
    IFleetHostStatsQuery,
    IHostStatsQuery,
    INodeHostGateway,
)
from .app.queries.fleet import FleetHostStatsQuery
from .app.queries.host import HostStatsQuery
from .app.services.fanout import HostStatsFanout
from .infra.grpc.host import NodeHostGateway


class NodeObservationsProvider(Provider):
    scope = Scope.REQUEST

    stats = provide(HostStatsQuery, provides=IHostStatsQuery)
    fleet = provide(FleetHostStatsQuery, provides=IFleetHostStatsQuery)
    fanout = provide(HostStatsFanout, scope=Scope.APP)
    host = provide(NodeHostGateway, provides=INodeHostGateway, scope=Scope.APP)
