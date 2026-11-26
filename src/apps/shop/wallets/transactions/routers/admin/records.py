"""Post direct wallet credits and debits from the administrator panel."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.commands import IWalletTransactionCommand
from ...domain.dtos.records import TransactionPost
from ..schemas.records import TransactionOutput

router = APIRouter(
    prefix="/admin/wallets/{customer_id:int}",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("/credits", status_code=201)
async def post_credit(
    customer_id: IdType,
    data: TransactionPost,
    command: FromDishka[IWalletTransactionCommand],
) -> APIResponse[TransactionOutput, None]:
    row = await command.credit(customer_id, data)
    output = TransactionOutput.from_obj(row)
    return APIResponse[TransactionOutput, None].from_data(output)


@router.post("/debits", status_code=201)
async def post_debit(
    customer_id: IdType,
    data: TransactionPost,
    command: FromDishka[IWalletTransactionCommand],
) -> APIResponse[TransactionOutput, None]:
    row = await command.debit(customer_id, data)
    output = TransactionOutput.from_obj(row)
    return APIResponse[TransactionOutput, None].from_data(output)
