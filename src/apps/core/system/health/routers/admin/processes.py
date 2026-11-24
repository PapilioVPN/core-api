"""Health processes HTTP reads; access guards are deferred."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from fastapi import Path as PathParameter
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.system.health.app.interfaces.health import (
    IProcessHealthService,
)
from src.apps.core.system.health.routers.schemas.common import (
    MeasurementOutput,
)
from src.apps.core.system.health.routers.schemas.processes import (
    ProcessListingOutput,
    ProcessOutput,
)

router = APIRouter(
    prefix="/admin/health/processes",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("system"))],
)


@router.get(
    "",
    response_model=APIResponse[MeasurementOutput[ProcessListingOutput], None],
)
async def processes(
    service: FromDishka[IProcessHealthService],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> APIResponse[MeasurementOutput[ProcessListingOutput], None]:
    """Return measured processes data.

    Args:
        service: Injected IProcessHealthService contract.
        limit: Maximum returned processes, from 1 through 1000.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_processes(limit=limit)
    output = MeasurementOutput[ProcessListingOutput].from_obj(result)
    return APIResponse[
        MeasurementOutput[ProcessListingOutput], None
    ].from_data(output)


@router.get("/count", response_model=APIResponse[MeasurementOutput[int], None])
async def process_count(
    service: FromDishka[IProcessHealthService],
) -> APIResponse[MeasurementOutput[int], None]:
    """Return measured process count data.

    Args:
        service: Injected IProcessHealthService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_process_count()
    output = MeasurementOutput[int].from_obj(result)
    return APIResponse[MeasurementOutput[int], None].from_data(output)


@router.get(
    "/{process_id}",
    response_model=APIResponse[MeasurementOutput[ProcessOutput | None], None],
)
async def process(
    service: FromDishka[IProcessHealthService],
    process_id: Annotated[int, PathParameter(gt=0)],
) -> APIResponse[MeasurementOutput[ProcessOutput | None], None]:
    """Return measured process data.

    Args:
        service: Injected IProcessHealthService contract.
        process_id: Positive native process identifier.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_process(process_id)
    output = MeasurementOutput[ProcessOutput | None].from_obj(result)
    return APIResponse[
        MeasurementOutput[ProcessOutput | None], None
    ].from_data(output)
