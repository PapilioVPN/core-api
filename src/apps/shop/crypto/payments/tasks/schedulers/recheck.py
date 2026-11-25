"""Execute the scheduled Plisio recheck through the batch pipeline."""

from dishka import FromDishka
from papilio_tasks.apps.schedulers import TaskRouter

from ...app.pipelines.recheck import PaymentRecheckPipeline
from ...domain.dtos.recheck import PaymentRecheck
from ...domain.results.check import RecheckStats
from ...infra.broker.config import BrokerConfig
from ...infra.broker.tasks import recheck_payments

router = TaskRouter()


@router.task(recheck_payments, schedule=BrokerConfig.recheck_schedule)
async def recheck(
    query: PaymentRecheck, *, pipeline: FromDishka[PaymentRecheckPipeline]
) -> RecheckStats:
    """Run one bounded batch through the existing payment checker."""
    result = await pipeline.run(query)
    return result
