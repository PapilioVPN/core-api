"""Compose crypto payment operations and their hosted gateway adapters."""

from collections.abc import AsyncIterator, Mapping
from logging import getLogger

from dishka import Provider, Scope, provide
from papilio.infra.http.connection import HTTPConnection

from .app.commands.records import CryptoPaymentCommand
from .app.interfaces.commands import ICryptoPaymentCommand
from .app.interfaces.gateway import ICryptoPaymentGateway
from .app.interfaces.queries import ICryptoPaymentSearchQuery
from .app.interfaces.services import ICryptoPaymentService
from .app.queries.search import CryptoPaymentSearchQuery
from .app.services.crud import CryptoPaymentService
from .infra.nowpayments.client import NowPaymentsGateway
from .infra.pg.repositories.crud import CryptoPaymentRepository
from .infra.plisio.client import PlisioGateway
from .infra.plisio.logging import RedactAPIKey


class CryptoPaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoPaymentRepository)
    payments = provide(CryptoPaymentService, provides=ICryptoPaymentService)
    command = provide(CryptoPaymentCommand, provides=ICryptoPaymentCommand)
    search = provide(
        CryptoPaymentSearchQuery, provides=ICryptoPaymentSearchQuery
    )
    nowpayments = provide(NowPaymentsGateway, scope=Scope.APP)

    @provide(scope=Scope.APP)
    async def plisio(
        self, connection: HTTPConnection
    ) -> AsyncIterator[PlisioGateway]:
        """Redact Plisio query credentials for the adapter's lifetime."""
        logger = getLogger("httpx")
        redactor = RedactAPIKey()
        logger.addFilter(redactor)
        try:
            yield PlisioGateway(connection)
        finally:
            logger.removeFilter(redactor)

    @provide(scope=Scope.APP)
    def adapters(
        self, nowpayments: NowPaymentsGateway, plisio: PlisioGateway
    ) -> Mapping[str, ICryptoPaymentGateway]:
        """Bind each implemented kind to its native adapter."""
        return {"nowpayments": nowpayments, "plisio": plisio}
