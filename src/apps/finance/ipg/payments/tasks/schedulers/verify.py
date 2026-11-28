"""Run one bounded reconciliation batch through Papilio Tasks."""

from dishka import FromDishka
from papilio_tasks.apps.schedulers import TaskRouter

from ...app.pipelines.verify import VerifyPipeline
from ...domain.dtos.verify import VerifyPolicy
from ...domain.results.verify import VerifyBatch
from ...infra.broker.config import BrokerConfig
from ...infra.broker.tasks import verify_payments

router = TaskRouter()


@router.task(verify_payments, schedule=BrokerConfig.verify_schedule)
async def verify(
    policy: VerifyPolicy, *, pipeline: FromDishka[VerifyPipeline]
) -> VerifyBatch:
    """Check due payment links and report committed confirmations."""
    result = await pipeline.run(policy)
    return result
