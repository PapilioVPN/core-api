"""Bind live Xray outbound health to native discovery."""

from dishka import Provider, Scope, provide

from .app.interfaces.health import (
    IXrayOutboundHealthGateway,
    IXrayOutboundHealthQuery,
)
from .app.queries.health import XrayOutboundHealthQuery
from .infra.grpc.health import XrayOutboundHealthGateway


class XrayOutboundHealthProvider(Provider):
    scope = Scope.REQUEST

    query = provide(XrayOutboundHealthQuery, provides=IXrayOutboundHealthQuery)
    gateway = provide(
        XrayOutboundHealthGateway,
        provides=IXrayOutboundHealthGateway,
        scope=Scope.APP,
    )
