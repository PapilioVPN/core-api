"""Record an authenticated bank transfer notification."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse

from ....api_keys.routers.dependencies.identity import require_api_key
from ...app.interfaces.commands import IHookTransferCommand
from ...domain.dtos.records import HookTransferCreate
from ..schemas.records import TransferOutput

router = APIRouter(
    prefix="/hooks/card-to-card/transfers", route_class=DishkaRoute
)


@router.post("", status_code=201)
async def post_bank_transfer(
    data: HookTransferCreate,
    key_id: Annotated[int, Depends(require_api_key)],
    command: FromDishka[IHookTransferCommand],
) -> APIResponse[TransferOutput, None]:
    transfer = await command.create(data, key_id=key_id)
    output = TransferOutput.from_obj(transfer)
    return APIResponse[TransferOutput, None].from_data(output)
