"""Bind payment record operations to the native request scope."""

from collections.abc import AsyncIterator
from logging import getLogger

from dishka import Provider, Scope, alias, provide
from papilio.infra.http.connection import HTTPConnection

from .app.commands.create import PaymentCreateCommand
from .app.commands.quote import PaymentQuoteCommand
from .app.executions.check import PaymentCheckExecution
from .app.executions.issue import PaymentIssueExecution
from .app.interfaces.check import IPaymentCheckExecution
from .app.interfaces.commands import (
    IPaymentCreateCommand,
    IPaymentQuoteCommand,
)
from .app.interfaces.gateways import IPlisioGateway
from .app.interfaces.issue import IPaymentIssueExecution, IPaymentIssuePipeline
from .app.interfaces.services import ICryptoPaymentService
from .app.pipelines.check import PaymentCheckPipeline
from .app.pipelines.issue import PaymentIssuePipeline
from .app.pipelines.recheck import PaymentRecheckPipeline
from .app.services.crud import CryptoPaymentService
from .infra.pg.repositories.crud import CryptoPaymentRepository
from .infra.plisio.client import PlisioGateway
from .infra.plisio.logging import RedactAPIKey


class CryptoPaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoPaymentRepository)
    service = provide(CryptoPaymentService, provides=ICryptoPaymentService)
    create = provide(PaymentCreateCommand)
    create_command = alias(
        PaymentCreateCommand, provides=IPaymentCreateCommand
    )
    quote = provide(PaymentQuoteCommand)
    quote_command = alias(PaymentQuoteCommand, provides=IPaymentQuoteCommand)
    execution = provide(
        PaymentIssueExecution, provides=IPaymentIssueExecution, scope=Scope.APP
    )
    issue = provide(PaymentIssuePipeline, scope=Scope.APP)
    issue_pipeline = alias(
        PaymentIssuePipeline, provides=IPaymentIssuePipeline
    )
    check_execution = provide(
        PaymentCheckExecution, provides=IPaymentCheckExecution, scope=Scope.APP
    )
    check = provide(PaymentCheckPipeline, scope=Scope.APP)
    recheck = provide(PaymentRecheckPipeline, scope=Scope.APP)

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
