"""Bind the Xray dry-run operation and its gRPC gateway."""

from dishka import Provider, Scope, provide

from .app.interfaces.dry_run import IXrayConfigGateway, IXrayConfigValidation
from .app.services.dry_run import XrayConfigValidationService
from .infra.grpc.dry_run import XrayConfigGateway


class XrayValidationProvider(Provider):
    scope = Scope.REQUEST

    gateway = provide(
        XrayConfigGateway, provides=IXrayConfigGateway, scope=Scope.APP
    )
    validation = provide(
        XrayConfigValidationService, provides=IXrayConfigValidation
    )
