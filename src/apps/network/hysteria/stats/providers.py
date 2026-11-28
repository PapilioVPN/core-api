"""Bind the native gateway and the Panel's HysteriaRuntime query."""

from dishka import Provider, Scope, provide

from .app.interfaces.runtime import (
    IHysteriaRuntimeGateway,
    IHysteriaRuntimeQuery,
)
from .app.queries.runtime import HysteriaRuntimeQuery
from .infra.grpc.runtime import HysteriaRuntimeGateway


class HysteriaRuntimeProvider(Provider):
    scope = Scope.REQUEST

    query = provide(HysteriaRuntimeQuery, provides=IHysteriaRuntimeQuery)
    gateway = provide(
        HysteriaRuntimeGateway,
        provides=IHysteriaRuntimeGateway,
        scope=Scope.APP,
    )
