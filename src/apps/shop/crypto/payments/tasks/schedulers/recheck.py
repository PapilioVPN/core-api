"""Register the bounded crypto payment check."""

from dishka import FromDishka
from papilio_tasks.apps.schedulers import TaskRouter

from ...app.interfaces.commands import ICryptoPaymentCommand
from ...domain.dtos.recheck import PaymentRecheck
from ...infra.broker.config import BrokerConfig
from ...infra.broker.tasks import recheck_payments

router = TaskRouter()


@router.task(recheck_payments, schedule=BrokerConfig.recheck_schedule)
async def recheck(
    query: PaymentRecheck, *, command: FromDishka[ICryptoPaymentCommand]
) -> int:
    """Check one due batch and return the number of payments selected."""
    checked = await command.recheck(limit=query.limit, delay=query.delay)
    return checked
