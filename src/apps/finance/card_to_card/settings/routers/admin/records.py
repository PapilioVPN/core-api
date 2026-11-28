"""Read and edit automatic card transfer settings in the panel."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.queries import ITransferSettingsQuery
from ...app.interfaces.services import ITransferSettingsService
from ...domain.dtos.records import (
    TransferSettingsUpdate,
    TransferSettingsWrite,
)
from ...domain.enums.records import SettingsKey
from ..schemas.records import TransferSettingsOutput

router = APIRouter(
    prefix="/admin/card-to-card/settings",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("finance"))],
)


@router.get("")
async def get_settings(
    query: FromDishka[ITransferSettingsQuery],
) -> APIResponse[TransferSettingsOutput, None]:
    settings = await query.get(SettingsKey.GENERAL)
    output = TransferSettingsOutput.from_obj(settings)
    return APIResponse[TransferSettingsOutput, None].from_data(output)


@router.put("")
async def put_settings(
    data: TransferSettingsWrite,
    service: FromDishka[ITransferSettingsService],
) -> APIResponse[TransferSettingsOutput, None]:
    settings = await service.save(SettingsKey.GENERAL, data)
    output = TransferSettingsOutput.from_obj(settings)
    return APIResponse[TransferSettingsOutput, None].from_data(output)


@router.patch("")
async def patch_settings(
    data: TransferSettingsUpdate,
    service: FromDishka[ITransferSettingsService],
) -> APIResponse[TransferSettingsOutput, None]:
    settings = await service.update(SettingsKey.GENERAL, data)
    output = TransferSettingsOutput.from_obj(settings)
    return APIResponse[TransferSettingsOutput, None].from_data(output)
