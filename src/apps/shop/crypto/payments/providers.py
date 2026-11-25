"""Compose crypto payment persistence, operations and the provider adapter."""

from dishka import Provider, Scope, provide

from src.settings.config import CoreSettings

from .app.commands.records import CryptoPaymentCommand
from .app.interfaces.commands import ICryptoPaymentCommand
from .app.interfaces.gateway import ICryptoPaymentGateway
from .app.interfaces.queries import ICryptoPaymentSearchQuery
from .app.interfaces.services import ICryptoPaymentService
from .app.queries.search import CryptoPaymentSearchQuery
from .app.services.crud import CryptoPaymentService
from .config import CryptoPaymentsConfig
from .infra.nowpayments.client import NowPaymentsGateway
from .infra.pg.repositories.crud import CryptoPaymentRepository


class CryptoPaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoPaymentRepository)
    payments = provide(CryptoPaymentService, provides=ICryptoPaymentService)
    command = provide(CryptoPaymentCommand, provides=ICryptoPaymentCommand)
    search = provide(
        CryptoPaymentSearchQuery, provides=ICryptoPaymentSearchQuery
    )
    gateway = provide(
        NowPaymentsGateway, provides=ICryptoPaymentGateway, scope=Scope.APP
    )

    @provide(scope=Scope.APP)
    def config(self, settings: CoreSettings) -> CryptoPaymentsConfig:
        """Select private integration settings."""
        return settings.crypto_payments
