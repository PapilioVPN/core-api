"""Dependency probes protected by system read permission."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse

from src.apps.core.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.system.app.interfaces.records import (
    IPostgresHealthService,
    IRedisHealthService,
)
from src.apps.core.system.routers.schemas.common import (
    PostgresHealthOutput,
    ProbeOutput,
)

router = APIRouter(
    prefix="/admin/health",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("system"))],
)


@router.get("/postgres", response_model=APIResponse[ProbeOutput, None])
async def postgres(
    service: FromDishka[IPostgresHealthService],
) -> APIResponse[ProbeOutput, None]:
    """Return PostgreSQL connection availability.

    Args:
        service: Injected PostgreSQL health contract.

    Returns:
        Native envelope containing ok/nok and attempt milliseconds.
    """
    result = await service.ping()
    output = ProbeOutput.from_obj(result)
    return APIResponse[ProbeOutput, None].from_data(output)


@router.get("/redis", response_model=APIResponse[ProbeOutput, None])
async def redis(
    service: FromDishka[IRedisHealthService],
) -> APIResponse[ProbeOutput, None]:
    """Return Redis connection availability.

    Args:
        service: Injected Redis health contract.

    Returns:
        Native envelope containing ok/nok and attempt milliseconds.
    """
    result = await service.ping()
    output = ProbeOutput.from_obj(result)
    return APIResponse[ProbeOutput, None].from_data(output)


@router.get(
    "/postgres/time", response_model=APIResponse[PostgresHealthOutput, None]
)
async def postgres_time(
    service: FromDishka[IPostgresHealthService],
) -> APIResponse[PostgresHealthOutput, None]:
    """Return the measured PostgreSQL clock snapshot.

    Args:
        service: Injected PostgreSQL health contract.

    Returns:
        Native envelope with status, optional clock and attempt milliseconds.
    """
    result = await service.read_server_time()
    output = PostgresHealthOutput.from_obj(result)
    return APIResponse[PostgresHealthOutput, None].from_data(output)
