"""Register and read incoming card transfers from the Finance panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)

from ...app.interfaces.commands import IAdminTransferCommand
from ...app.interfaces.services import ITransferService
from ...domain.dtos.records import AdminTransferCreate, TransferList
from ..schemas.records import TransferOutput

router = APIRouter(
    prefix="/admin/card-to-card/transfers",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("finance"))],
)


@router.post("", status_code=201)
async def post_transfer(
    data: AdminTransferCreate,
    admin: Annotated[AdminIdentity, Depends(current_admin)],
    command: FromDishka[IAdminTransferCommand],
) -> APIResponse[TransferOutput, None]:
    transfer = await command.create(data, admin_id=admin.user_id)
    output = TransferOutput.from_obj(transfer)
    return APIResponse[TransferOutput, None].from_data(output)


@router.get("")
async def get_transfers(
    query: Annotated[TransferList, Query()],
    service: FromDishka[ITransferService],
) -> APIResponse[TransferOutput, PagerMeta]:
    page = await service.list(query)
    return APIResponse[TransferOutput, PagerMeta](
        success=True,
        data=TransferOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/{id:int}")
async def get_transfer(
    id: IdType, service: FromDishka[ITransferService]
) -> APIResponse[TransferOutput, None]:
    transfer = await service.get_by_id(id)
    output = TransferOutput.from_obj(transfer)
    return APIResponse[TransferOutput, None].from_data(output)
