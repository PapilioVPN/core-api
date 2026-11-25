"""Bind payment record operations to the native request scope."""

from collections.abc import AsyncIterator
from logging import getLogger

from dishka import Provider, Scope, provide
from papilio.infra.http.connection import HTTPConnection

from .app.commands.create import PaymentCreateCommand
from .app.commands.quote import PaymentQuoteCommand
from .app.executions.issue import PaymentIssueExecution
from .app.interfaces.issue import IPaymentIssueExecution, IPlisioGateway
from .app.interfaces.services import ICryptoPaymentService
from .app.pipelines.issue import PaymentIssuePipeline
from .app.services.crud import CryptoPaymentService
from .infra.pg.repositories.crud import CryptoPaymentRepository
from .infra.plisio.client import PlisioGateway
from .infra.plisio.logging import RedactAPIKey


class CryptoPaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoPaymentRepository)
    service = provide(CryptoPaymentService, provides=ICryptoPaymentService)
    create = provide(PaymentCreateCommand)
    quote = provide(PaymentQuoteCommand)
    execution = provide(
        PaymentIssueExecution, provides=IPaymentIssueExecution, scope=Scope.APP
    )
    issue = provide(PaymentIssuePipeline, scope=Scope.APP)

    @provide(scope=Scope.APP)
    async def plisio(
        self, connection: HTTPConnection
    ) -> AsyncIterator[IPlisioGateway]:
        """Borrow the shared pool and redact Plisio's required query key."""
        log = getLogger("httpx")
        redact = RedactAPIKey()
        log.addFilter(redact)
        try:
            yield PlisioGateway(connection)
        finally:
            log.removeFilter(redact)
