"""Bind the Hysteria capability to native application discovery."""

from dishka import Provider, Scope, provide

from .app.interfaces.dry_run import (
    IHysteriaValidationGateway,
    IHysteriaValidationService,
)
from .app.services.dry_run import HysteriaValidationService
from .infra.grpc.dry_run import HysteriaValidationGateway


class HysteriaValidationProvider(Provider):
    scope = Scope.REQUEST

    validation = provide(
        HysteriaValidationService, provides=IHysteriaValidationService
    )
    validation_gateway = provide(
        HysteriaValidationGateway,
        provides=IHysteriaValidationGateway,
        scope=Scope.APP,
    )
