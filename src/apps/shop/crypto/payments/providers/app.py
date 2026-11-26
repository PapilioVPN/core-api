"""Bind shared payment gateways and scoped execution pipelines."""

from collections.abc import AsyncIterator
from logging import getLogger

from dishka import Provider, Scope, alias, provide
from papilio.infra.http.connection import HTTPConnection

from ..app.executions.check import PaymentCheckExecution
from ..app.executions.issue import PaymentIssueExecution
from ..app.interfaces.check import IPaymentCheckExecution
from ..app.interfaces.gateways import (
    INowPaymentsGateway,
    INowPaymentsNotification,
    IPlisioGateway,
)
from ..app.interfaces.issue import (
    IPaymentIssueExecution,
    IPaymentIssuePipeline,
)
from ..app.pipelines.check import PaymentCheckPipeline
from ..app.pipelines.issue import PaymentIssuePipeline
from ..app.pipelines.recheck import PaymentRecheckPipeline
from ..infra.nowpayments.client import NowPaymentsGateway
from ..infra.nowpayments.notifications import NowPaymentsNotification
from ..infra.plisio.client import PlisioGateway
from ..infra.plisio.logging import RedactAPIKey


class PaymentAppProvider(Provider):
    scope = Scope.APP

    decoder = provide(
        NowPaymentsNotification, provides=INowPaymentsNotification
    )
    nowpayments = provide(NowPaymentsGateway, provides=INowPaymentsGateway)
    issue_execution = provide(
        PaymentIssueExecution, provides=IPaymentIssueExecution
    )
    issue = provide(PaymentIssuePipeline)
    issue_pipeline = alias(
        PaymentIssuePipeline, provides=IPaymentIssuePipeline
    )
    check_execution = provide(
        PaymentCheckExecution, provides=IPaymentCheckExecution
    )
    check = provide(PaymentCheckPipeline)
    recheck = provide(PaymentRecheckPipeline)

    @provide
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
