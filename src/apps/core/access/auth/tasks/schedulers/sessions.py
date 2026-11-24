"""Bounded cleanup of expired administrator sessions."""

from dishka import FromDishka
from papilio_tasks.apps.schedulers import TaskRouter

from src.apps.core.access.auth.app.interfaces.services import ISessionService
from src.apps.core.access.auth.infra.broker.config import BrokerConfig
from src.apps.core.access.auth.infra.broker.tasks import cleanup_sessions

router = TaskRouter()


@router.task(cleanup_sessions, schedule=BrokerConfig.cleanup_schedule)
async def remove_expired(*, service: FromDishka[ISessionService]) -> int:
    """Delete one bounded batch of expired sessions.

    Args:
        service: Request-scoped session owner.

    Returns:
        Committed count of expired sessions removed.
    """
    count = await service.remove_expired()
    return count
