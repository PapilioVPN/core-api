"""Bind the Xray validation capability to the native container."""

from dishka import Provider, Scope, provide

from src.settings.config import CoreSettings

from .app.interfaces.validation import (
    IXrayConfigGateway,
    IXrayConfigValidation,
)
from .app.services.validation import XrayConfigValidationService
from .config import XrayConfig
from .infra.grpc.validation import XrayConfigGateway


class XrayProvider(Provider):
    scope = Scope.REQUEST

    gateway = provide(
        XrayConfigGateway, provides=IXrayConfigGateway, scope=Scope.APP
    )
    validation = provide(
        XrayConfigValidationService, provides=IXrayConfigValidation
    )

    @provide(scope=Scope.APP)
    def config(self, settings: CoreSettings) -> XrayConfig:
        """Select the deployment's Xray validation deadline."""
        return settings.xray
