"""Health resource reads protected by the system permission."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.system.info.app.interfaces.services import (
    ISystemResourcesService,
)
from src.apps.core.system.info.routers.schemas.common import (
    MeasurementOutput,
)
from src.apps.core.system.info.routers.schemas.resources import (
    CoreCpuUsageOutput,
    CpuOutput,
    CpuUsageOutput,
    HostOutput,
    MemoryOutput,
    RuntimeOutput,
    SwapOutput,
    UserSessionOutput,
)

router = APIRouter(
    prefix="/admin/health/resources",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("system"))],
)


@router.get(
    "/host", response_model=APIResponse[MeasurementOutput[HostOutput], None]
)
async def host(
    service: FromDishka[ISystemResourcesService],
) -> APIResponse[MeasurementOutput[HostOutput], None]:
    """Return measured host data.

    Args:
        service: Injected ISystemResourcesService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_host()
    output = MeasurementOutput[HostOutput].from_obj(result)
    return APIResponse[MeasurementOutput[HostOutput], None].from_data(output)


@router.get(
    "/runtime",
    response_model=APIResponse[MeasurementOutput[RuntimeOutput], None],
)
async def runtime(
    service: FromDishka[ISystemResourcesService],
) -> APIResponse[MeasurementOutput[RuntimeOutput], None]:
    """Return measured runtime data.

    Args:
        service: Injected ISystemResourcesService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_runtime()
    output = MeasurementOutput[RuntimeOutput].from_obj(result)
    return APIResponse[MeasurementOutput[RuntimeOutput], None].from_data(
        output
    )


@router.get(
    "/sessions",
    response_model=APIResponse[
        MeasurementOutput[tuple[UserSessionOutput, ...]], None
    ],
)
async def sessions(
    service: FromDishka[ISystemResourcesService],
) -> APIResponse[MeasurementOutput[tuple[UserSessionOutput, ...]], None]:
    """Return measured sessions data.

    Args:
        service: Injected ISystemResourcesService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_sessions()
    output = MeasurementOutput[tuple[UserSessionOutput, ...]].from_obj(result)
    return APIResponse[
        MeasurementOutput[tuple[UserSessionOutput, ...]], None
    ].from_data(output)


@router.get(
    "/cpu", response_model=APIResponse[MeasurementOutput[CpuOutput], None]
)
async def cpu(
    service: FromDishka[ISystemResourcesService],
) -> APIResponse[MeasurementOutput[CpuOutput], None]:
    """Return measured cpu data.

    Args:
        service: Injected ISystemResourcesService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_cpu()
    output = MeasurementOutput[CpuOutput].from_obj(result)
    return APIResponse[MeasurementOutput[CpuOutput], None].from_data(output)


@router.get(
    "/cpu/usage",
    response_model=APIResponse[MeasurementOutput[CpuUsageOutput], None],
)
async def cpu_usage(
    service: FromDishka[ISystemResourcesService],
    sample_seconds: Annotated[
        float, Query(gt=0, le=5, allow_inf_nan=False)
    ] = 0.1,
) -> APIResponse[MeasurementOutput[CpuUsageOutput], None]:
    """Return measured cpu usage data.

    Args:
        service: Injected ISystemResourcesService contract.
        sample_seconds: CPU sampling interval, over zero through 5 seconds.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_cpu_usage(sample_seconds)
    output = MeasurementOutput[CpuUsageOutput].from_obj(result)
    return APIResponse[MeasurementOutput[CpuUsageOutput], None].from_data(
        output
    )


@router.get(
    "/cpu/cores/usage",
    response_model=APIResponse[MeasurementOutput[CoreCpuUsageOutput], None],
)
async def core_usage(
    service: FromDishka[ISystemResourcesService],
    sample_seconds: Annotated[
        float, Query(gt=0, le=5, allow_inf_nan=False)
    ] = 0.1,
) -> APIResponse[MeasurementOutput[CoreCpuUsageOutput], None]:
    """Return measured core usage data.

    Args:
        service: Injected ISystemResourcesService contract.
        sample_seconds: CPU sampling interval, over zero through 5 seconds.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_core_usage(sample_seconds)
    output = MeasurementOutput[CoreCpuUsageOutput].from_obj(result)
    return APIResponse[MeasurementOutput[CoreCpuUsageOutput], None].from_data(
        output
    )


@router.get(
    "/memory",
    response_model=APIResponse[MeasurementOutput[MemoryOutput], None],
)
async def memory(
    service: FromDishka[ISystemResourcesService],
) -> APIResponse[MeasurementOutput[MemoryOutput], None]:
    """Return measured memory data.

    Args:
        service: Injected ISystemResourcesService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_memory()
    output = MeasurementOutput[MemoryOutput].from_obj(result)
    return APIResponse[MeasurementOutput[MemoryOutput], None].from_data(output)


@router.get(
    "/swap", response_model=APIResponse[MeasurementOutput[SwapOutput], None]
)
async def swap(
    service: FromDishka[ISystemResourcesService],
) -> APIResponse[MeasurementOutput[SwapOutput], None]:
    """Return measured swap data.

    Args:
        service: Injected ISystemResourcesService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_swap()
    output = MeasurementOutput[SwapOutput].from_obj(result)
    return APIResponse[MeasurementOutput[SwapOutput], None].from_data(output)
