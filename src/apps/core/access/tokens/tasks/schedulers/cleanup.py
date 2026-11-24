"""Native scheduled cleanup of expired refresh-consumption history."""

from dishka import FromDishka
from papilio_tasks.apps.schedulers import TaskRouter

from src.apps.core.access.tokens.app.interfaces.refresh import (
    IRefreshUseService,
)
from src.apps.core.access.tokens.domain.dtos.refresh import RefreshUseCleanup
from src.apps.core.access.tokens.infra.broker.config import BrokerConfig
from src.apps.core.access.tokens.infra.broker.tasks import cleanup_refresh

router = TaskRouter()


@router.task(cleanup_refresh, schedule=BrokerConfig.cleanup_schedule)
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
