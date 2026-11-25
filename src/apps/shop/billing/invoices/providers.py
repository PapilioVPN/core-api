"""Bind the trusted Billing preview operations and native Redis cache."""

from dishka import AnyOf, Provider, Scope, provide

from .app.commands.create import BillingInvoiceCommand
from .app.interfaces.commands import IInvoiceCommand
from .app.interfaces.services import IInvoiceService
from .app.queries.terms import InvoiceTermsQuery
from .app.services.crud import BillingInvoiceService
from .infra.redis.cache import InvoiceCache


class BillingInvoiceProvider(Provider):
    scope = Scope.REQUEST

    cache = provide(InvoiceCache, scope=Scope.APP)
    service = provide(
        BillingInvoiceService,
        scope=Scope.APP,
        provides=AnyOf[BillingInvoiceService, IInvoiceService],
    )
    terms = provide(InvoiceTermsQuery)
    command = provide(BillingInvoiceCommand, provides=IInvoiceCommand)
