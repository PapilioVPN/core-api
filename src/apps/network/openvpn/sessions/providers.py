"""Bind the native gateway and the Panel's OpenVPNSessionCount query."""

from dishka import Provider, Scope, provide

from .app.interfaces.count import (
    IOpenVPNSessionCountGateway,
    IOpenVPNSessionCountQuery,
)
from .app.queries.count import OpenVPNSessionCountQuery
from .infra.grpc.count import OpenVPNSessionCountGateway


class OpenVPNSessionCountProvider(Provider):
    scope = Scope.REQUEST

    query = provide(
        OpenVPNSessionCountQuery, provides=IOpenVPNSessionCountQuery
    )
    gateway = provide(
        OpenVPNSessionCountGateway,
        provides=IOpenVPNSessionCountGateway,
        scope=Scope.APP,
    )
