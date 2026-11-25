"""Bind gateway settings to the native request scope."""

from dishka import Provider, Scope, provide

from .app.interfaces.services import ICryptoGatewayService
from .app.services.crud import CryptoGatewayService
from .infra.pg.repositories.crud import CryptoGatewayRepository


class CryptoGatewayProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoGatewayRepository)
    gateways = provide(CryptoGatewayService, provides=ICryptoGatewayService)
