"""Bind payment record operations to the request scope."""

from dishka import Provider, Scope, provide

from .app.commands.attach_receipt import PaymentAttachReceiptCommand
from .app.commands.create import PaymentCreateCommand
from .app.commands.review import (
    PaymentAutoConfirmCommand,
    PaymentConfirmCommand,
    PaymentRejectCommand,
)
from .app.interfaces.commands import (
    IPaymentAttachReceiptCommand,
    IPaymentAutoConfirmCommand,
    IPaymentConfirmCommand,
    IPaymentCreateCommand,
    IPaymentRejectCommand,
)
from .app.interfaces.queries import IPaymentQuery, IPaymentSearchQuery
from .app.interfaces.services import (
    IPaymentRegistrationService,
    IPaymentService,
)
from .app.queries.details import PaymentQuery
from .app.queries.search import PaymentSearchQuery
from .app.services.crud import PaymentService
from .app.services.registration import PaymentRegistrationService
from .infra.pg.readers.details import PaymentReader
from .infra.pg.repositories.crud import PaymentRepository


class PaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(PaymentRepository)
    reader = provide(PaymentReader)
    payments = provide(PaymentService, provides=IPaymentService)
    registration = provide(
        PaymentRegistrationService, provides=IPaymentRegistrationService
    )
    create = provide(PaymentCreateCommand, provides=IPaymentCreateCommand)
    attach_receipt = provide(
        PaymentAttachReceiptCommand, provides=IPaymentAttachReceiptCommand
    )
    confirm = provide(PaymentConfirmCommand, provides=IPaymentConfirmCommand)
    confirm_auto = provide(
        PaymentAutoConfirmCommand, provides=IPaymentAutoConfirmCommand
    )
    reject = provide(PaymentRejectCommand, provides=IPaymentRejectCommand)
    query = provide(PaymentQuery, provides=IPaymentQuery)
    search = provide(PaymentSearchQuery, provides=IPaymentSearchQuery)
