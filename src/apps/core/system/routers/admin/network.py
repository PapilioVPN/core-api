"""Network diagnostics protected by system read permission."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse

from src.apps.core.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.system.app.interfaces.records import (
    INetworkHealthService,
)
from src.apps.core.system.routers.schemas.common import (
    MeasurementOutput,
)
from src.apps.core.system.routers.schemas.network import (
    InterfaceOutput,
    NetworkIoOutput,
)

router = APIRouter(
    prefix="/admin/health/network",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("system"))],
)


@router.get(
    "/interfaces",
    response_model=APIResponse[
        MeasurementOutput[tuple[InterfaceOutput, ...]], None
    ],
)
async def interfaces(
    service: FromDishka[INetworkHealthService],
) -> APIResponse[MeasurementOutput[tuple[InterfaceOutput, ...]], None]:
    """Return measured interfaces data.

    Args:
        service: Injected INetworkHealthService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_interfaces()
    output = MeasurementOutput[tuple[InterfaceOutput, ...]].from_obj(result)
    return APIResponse[
        MeasurementOutput[tuple[InterfaceOutput, ...]], None
    ].from_data(output)


@router.get(
    "/io",
    response_model=APIResponse[
        MeasurementOutput[tuple[NetworkIoOutput, ...] | None], None
    ],
)
async def io_counters(
    service: FromDishka[INetworkHealthService],
) -> APIResponse[MeasurementOutput[tuple[NetworkIoOutput, ...] | None], None]:
    """Return measured io counters data.

    Args:
        service: Injected INetworkHealthService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_io_counters()
    output = MeasurementOutput[tuple[NetworkIoOutput, ...] | None].from_obj(
        result
    )
    return APIResponse[
        MeasurementOutput[tuple[NetworkIoOutput, ...] | None], None
    ].from_data(output)


@router.get(
    "/io/total",
    response_model=APIResponse[
        MeasurementOutput[NetworkIoOutput | None], None
    ],
)
async def total_io_counters(
    service: FromDishka[INetworkHealthService],
) -> APIResponse[MeasurementOutput[NetworkIoOutput | None], None]:
    """Return measured total io counters data.

    Args:
        service: Injected INetworkHealthService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_total_io_counters()
    output = MeasurementOutput[NetworkIoOutput | None].from_obj(result)
    return APIResponse[
        MeasurementOutput[NetworkIoOutput | None], None
    ].from_data(output)
