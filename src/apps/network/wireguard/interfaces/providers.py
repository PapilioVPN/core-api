"""Bind the WireGuard capability to native application discovery."""

from dishka import Provider, Scope, provide

from .app.interfaces.dry_run import (
    IWireGuardValidationGateway,
    IWireGuardValidationService,
)
from .app.interfaces.status import (
    IWireGuardStatusGateway,
    IWireGuardStatusQuery,
)
from .app.queries.status import WireGuardStatusQuery
from .app.services.dry_run import WireGuardValidationService
from .infra.grpc.dry_run import WireGuardValidationGateway
from .infra.grpc.status import WireGuardStatusGateway


class WireGuardInterfacesProvider(Provider):
    scope = Scope.REQUEST

    query = provide(WireGuardStatusQuery, provides=IWireGuardStatusQuery)
    status_gateway = provide(
        WireGuardStatusGateway,
        provides=IWireGuardStatusGateway,
        scope=Scope.APP,
    )
    validation = provide(
        WireGuardValidationService, provides=IWireGuardValidationService
    )
    validation_gateway = provide(
        WireGuardValidationGateway,
        provides=IWireGuardValidationGateway,
        scope=Scope.APP,
    )
