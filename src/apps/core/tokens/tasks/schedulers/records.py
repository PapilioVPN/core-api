"""Native scheduled cleanup of expired refresh-consumption history."""

from dishka import FromDishka
from papilio_tasks.apps.schedulers import TaskRouter

from src.apps.core.tokens.app.interfaces.refresh import (
    IRefreshUseService,
)
from src.apps.core.tokens.domain.dtos.refresh import RefreshUseCleanup
from src.apps.core.tokens.infra.broker.tasks import cleanup

router = TaskRouter()


@router.task(
    cleanup,
    schedule=[
        {
            "schedule_id": "refresh-use-cleanup",
            "interval": 60,
            "kwargs": {"query": {"limit": 100}},
        }
    ],
)
async def remove_expired(
    query: RefreshUseCleanup, *, service: FromDishka[IRefreshUseService]
) -> int:
    """Clean one batch using the service's current UTC cutoff.

    Args:
        query: Native-validated maximum of 1..100 records per job.
        service: Request-scoped refresh-consumption service.

    Returns:
        Actual removed count after the service's owned SQL commit.

    Raises:
        Exception: Failures and cancellation propagate to native Taskiq.
    """
    removed = await service.remove_expired(limit=query.limit)
    return removed
