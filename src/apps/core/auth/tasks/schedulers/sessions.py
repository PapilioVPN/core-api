"""Bounded cleanup of expired administrator sessions."""

from dishka import FromDishka
from papilio_tasks.apps.schedulers import TaskRouter

from src.apps.core.auth.app.services.sessions import SessionService
from src.apps.core.auth.infra.broker.tasks import cleanup

router = TaskRouter()


@router.task(
    cleanup,
    schedule=[{"schedule_id": "admin-sessions-cleanup", "interval": 60}],
)
async def remove_expired(*, service: FromDishka[SessionService]) -> int:
    """Delete at most 100 expired sessions and return the committed count."""
    count = await service.remove_expired(limit=100)
    return count
