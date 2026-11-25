"""Request an on-demand rate refresh from the shop panel."""

from http import HTTPStatus

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.refresh import IRateRefreshPublisher
from ...domain.errors import RefreshUnavailable
from ..schemas.refresh import RefreshAccepted

router = APIRouter(
    prefix="/admin/crypto-rates",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("/refresh", status_code=HTTPStatus.ACCEPTED)
async def refresh(
    publisher: FromDishka[IRateRefreshPublisher | None],
) -> APIResponse[RefreshAccepted, None]:
    if publisher is None:
        raise RefreshUnavailable()
    task_id = await publisher.enqueue()
    return APIResponse[RefreshAccepted, None].from_data(
        RefreshAccepted(task_id=task_id)
    )
