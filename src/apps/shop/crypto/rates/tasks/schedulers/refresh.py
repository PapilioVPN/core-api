"""Run the same refresh pipeline for scheduled and manual jobs."""

from dishka import FromDishka
from papilio_tasks.apps.schedulers import TaskRouter

from ...app.pipelines.refresh import RateRefreshPipeline
from ...domain.models.records import Rate
from ...domain.results.records import RateFailure
from ...infra.broker.tasks import refresh_rate

router = TaskRouter()


@router.task(refresh_rate)
async def refresh(
    *, pipeline: FromDishka[RateRefreshPipeline]
) -> Rate | RateFailure:
    """Refresh the cached USD rate.

    Args:
        pipeline: Existing owner of the Wallex read and Redis update.

    Returns:
        The saved observation or its failure reason.
    """
    result = await pipeline.run()
    return result
