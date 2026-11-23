"""Public health without authentication or system metadata."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from papilio.api.responses.envelope import APIResponse

from src.apps.core.system.app.interfaces.health import (
    IPublicHealthService,
)
from src.apps.core.system.routers.schemas.common import (
    PublicHealthOutput,
)

router = APIRouter(prefix="/health", route_class=DishkaRoute)


@router.get("", response_model=APIResponse[PublicHealthOutput, None])
async def health(
    service: FromDishka[IPublicHealthService],
) -> APIResponse[PublicHealthOutput, None]:
    """Return availability and PostgreSQL's optional server clock.

    Args:
        service: Injected public health contract.

    Returns:
        Native response envelope; unavailable PG reports nok and a null clock.
    """
    result = await service.check()
    output = PublicHealthOutput.from_obj(result)
    return APIResponse[PublicHealthOutput, None].from_data(output)
