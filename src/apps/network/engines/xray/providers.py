"""Bind the Xray validation capability to the native container."""

from dishka import Provider, Scope, provide

from src.settings.config import CoreSettings

from .app.interfaces.status import IXrayStatusGateway, IXrayStatusQuery
from .app.interfaces.validation import (
    IXrayConfigGateway,
    IXrayConfigValidation,
)
from .app.queries.status import XrayStatusQuery
from .app.services.validation import XrayConfigValidationService
from .config import XrayConfig
from .infra.grpc.status import XrayStatusGateway
from .infra.grpc.validation import XrayConfigGateway


class XrayProvider(Provider):
    scope = Scope.REQUEST

    gateway = provide(
        XrayConfigGateway, provides=IXrayConfigGateway, scope=Scope.APP
    )
    validation = provide(
        XrayConfigValidationService, provides=IXrayConfigValidation
    )

    status_gateway = provide(
        XrayStatusGateway, provides=IXrayStatusGateway, scope=Scope.APP
    )
    status = provide(XrayStatusQuery, provides=IXrayStatusQuery)

    @provide(scope=Scope.APP)
    def config(self, settings: CoreSettings) -> XrayConfig:
        """Select the deployment's Xray validation deadline."""
        return settings.xray
