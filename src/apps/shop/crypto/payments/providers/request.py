"""Bind cryptocurrency payment records and write operations per request."""

from dishka import Provider, Scope, alias, provide

from ..app.commands.confirm import PaymentConfirmCommand
from ..app.commands.create import PaymentCreateCommand
from ..app.commands.quote import PaymentQuoteCommand
from ..app.interfaces.commands import (
    IPaymentConfirmCommand,
    IPaymentCreateCommand,
    IPaymentQuoteCommand,
)
from ..app.interfaces.services import (
    ICryptoPaymentService,
    IPaymentNotificationService,
    IPaymentPricingService,
)
from ..app.services.crud import CryptoPaymentService
from ..app.services.notifications import PaymentNotificationService
from ..app.services.pricing import PaymentPricingService
from ..infra.pg.repositories.crud import CryptoPaymentRepository


class PaymentRequestProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoPaymentRepository)
    service = provide(CryptoPaymentService, provides=ICryptoPaymentService)
    create = provide(PaymentCreateCommand)
    create_command = alias(
        PaymentCreateCommand, provides=IPaymentCreateCommand
    )
    quote = provide(PaymentQuoteCommand)
    quote_command = alias(PaymentQuoteCommand, provides=IPaymentQuoteCommand)
    confirm = provide(PaymentConfirmCommand, provides=IPaymentConfirmCommand)
    pricing = provide(PaymentPricingService, provides=IPaymentPricingService)
    notification = provide(
        PaymentNotificationService, provides=IPaymentNotificationService
    )
