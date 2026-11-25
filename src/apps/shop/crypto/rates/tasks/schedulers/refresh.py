"""Run the same refresh pipeline for scheduled and manual jobs."""

from dishka import FromDishka
from papilio_tasks.apps.schedulers import TaskRouter

from ...app.pipelines.refresh import RateRefreshPipeline
from ...infra.broker.tasks import refresh_rate

router = TaskRouter()


@router.task(refresh_rate)
async def refresh(*, pipeline: FromDishka[RateRefreshPipeline]) -> None:
    """Refresh the cached USD rate.

    Args:
        pipeline: Existing owner of the Wallex read and Redis update.

    Raises:
        RateUnavailable: The price could not be fetched or saved.
    """
    await pipeline.run()
