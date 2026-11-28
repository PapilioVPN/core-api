"""Bind the OpenVPN capability to native application discovery."""

from dishka import Provider, Scope, provide

from .app.interfaces.dry_run import (
    IOpenVPNValidationGateway,
    IOpenVPNValidationService,
)
from .app.services.dry_run import OpenVPNValidationService
from .infra.grpc.dry_run import OpenVPNValidationGateway


class OpenVPNValidationProvider(Provider):
    scope = Scope.REQUEST

    validation = provide(
        OpenVPNValidationService, provides=IOpenVPNValidationService
    )
    validation_gateway = provide(
        OpenVPNValidationGateway,
        provides=IOpenVPNValidationGateway,
        scope=Scope.APP,
    )
