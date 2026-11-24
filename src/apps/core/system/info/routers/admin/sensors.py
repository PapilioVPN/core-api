"""Sensor diagnostics protected by system read permission."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.system.info.app.interfaces.services import (
    ISensorService,
)
from src.apps.core.system.info.routers.schemas.common import (
    MeasurementOutput,
)
from src.apps.core.system.info.routers.schemas.sensors import (
    BatteryOutput,
    FanOutput,
    TemperatureOutput,
)

router = APIRouter(
    prefix="/admin/health/sensors",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("system"))],
)


@router.get(
    "/temperatures",
    response_model=APIResponse[
        MeasurementOutput[tuple[TemperatureOutput, ...] | None], None
    ],
)
async def temperatures(
    service: FromDishka[ISensorService],
) -> APIResponse[
    MeasurementOutput[tuple[TemperatureOutput, ...] | None], None
]:
    """Return measured temperatures data.

    Args:
        service: Injected ISensorService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_temperatures()
    output = MeasurementOutput[tuple[TemperatureOutput, ...] | None].from_obj(
        result
    )
    return APIResponse[
        MeasurementOutput[tuple[TemperatureOutput, ...] | None], None
    ].from_data(output)


@router.get(
    "/fans",
    response_model=APIResponse[
        MeasurementOutput[tuple[FanOutput, ...] | None], None
    ],
)
async def fans(
    service: FromDishka[ISensorService],
) -> APIResponse[MeasurementOutput[tuple[FanOutput, ...] | None], None]:
    """Return measured fans data.

    Args:
        service: Injected ISensorService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_fans()
    output = MeasurementOutput[tuple[FanOutput, ...] | None].from_obj(result)
    return APIResponse[
        MeasurementOutput[tuple[FanOutput, ...] | None], None
    ].from_data(output)


@router.get(
    "/battery",
    response_model=APIResponse[MeasurementOutput[BatteryOutput | None], None],
)
async def battery(
    service: FromDishka[ISensorService],
) -> APIResponse[MeasurementOutput[BatteryOutput | None], None]:
    """Return measured battery data.

    Args:
        service: Injected ISensorService contract.

    Returns:
        Native envelope preserving source units and null/empty distinctions.
    """
    result = await service.read_battery()
    output = MeasurementOutput[BatteryOutput | None].from_obj(result)
    return APIResponse[
        MeasurementOutput[BatteryOutput | None], None
    ].from_data(output)
