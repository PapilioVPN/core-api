"""Health storage HTTP reads; access guards are deferred."""

from pathlib import Path
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.system.info.app.interfaces.services import (
    IDiskService,
)
from src.apps.core.system.info.routers.schemas.common import (
    MeasurementOutput,
)
from src.apps.core.system.info.routers.schemas.storage import (
    DiskIoOutput,
    DiskUsageOutput,
    PartitionOutput,
)

router = APIRouter(
    prefix="/admin/health/storage",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("system"))],
)


@router.get(
    "/partitions",
    response_model=APIResponse[
        MeasurementOutput[tuple[PartitionOutput, ...]], None
    ],
)
async def partitions(
    service: FromDishka[IDiskService], include_virtual: bool = True
) -> APIResponse[MeasurementOutput[tuple[PartitionOutput, ...]], None]:
    """Return measured partitions data.

    Args:
        service: Injected IDiskService contract.
        include_virtual: Include virtual filesystem partitions.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_partitions(include_virtual=include_virtual)
    output = MeasurementOutput[tuple[PartitionOutput, ...]].from_obj(result)
    return APIResponse[
        MeasurementOutput[tuple[PartitionOutput, ...]], None
    ].from_data(output)


@router.get(
    "/usage",
    response_model=APIResponse[MeasurementOutput[DiskUsageOutput], None],
)
async def usage(
    service: FromDishka[IDiskService],
    path: Annotated[str, Query(pattern=r"^/")] = "/",
) -> APIResponse[MeasurementOutput[DiskUsageOutput], None]:
    """Return measured usage data.

    Args:
        service: Injected IDiskService contract.
        path: Absolute path to an existing filesystem entry.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_usage(Path(path))
    output = MeasurementOutput[DiskUsageOutput].from_obj(result)
    return APIResponse[MeasurementOutput[DiskUsageOutput], None].from_data(
        output
    )


@router.get(
    "/io",
    response_model=APIResponse[
        MeasurementOutput[tuple[DiskIoOutput, ...] | None], None
    ],
)
async def io_counters(
    service: FromDishka[IDiskService],
) -> APIResponse[MeasurementOutput[tuple[DiskIoOutput, ...] | None], None]:
    """Return measured io counters data.

    Args:
        service: Injected IDiskService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_io_counters()
    output = MeasurementOutput[tuple[DiskIoOutput, ...] | None].from_obj(
        result
    )
    return APIResponse[
        MeasurementOutput[tuple[DiskIoOutput, ...] | None], None
    ].from_data(output)


@router.get(
    "/io/total",
    response_model=APIResponse[MeasurementOutput[DiskIoOutput | None], None],
)
async def total_io_counters(
    service: FromDishka[IDiskService],
) -> APIResponse[MeasurementOutput[DiskIoOutput | None], None]:
    """Return measured total io counters data.

    Args:
        service: Injected IDiskService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_total_io_counters()
    output = MeasurementOutput[DiskIoOutput | None].from_obj(result)
    return APIResponse[MeasurementOutput[DiskIoOutput | None], None].from_data(
        output
    )
