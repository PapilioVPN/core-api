"""Issue and read wallet top-up invoices in the administrator panel."""

from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.commands import IWalletDepositCommand
from ...app.interfaces.services import IWalletDepositService
from ...domain.dtos.records import DepositCreate
from ..schemas.records import DepositOutput

router = APIRouter(
    prefix="/admin/wallets/{customer_id:int}/deposits",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_deposit(
    customer_id: IdType,
    data: DepositCreate,
    command: FromDishka[IWalletDepositCommand],
) -> APIResponse[DepositOutput, None]:
    invoice = await command.issue(customer_id, data)
    output = DepositOutput.from_obj(invoice)
    return APIResponse[DepositOutput, None].from_data(output)


@router.get("/{id:uuid}")
async def get_deposit(
    customer_id: IdType, id: UUID, service: FromDishka[IWalletDepositService]
) -> APIResponse[DepositOutput, None]:
    invoice = await service.get_by_id(customer_id, id)
    output = DepositOutput.from_obj(invoice)
    return APIResponse[DepositOutput, None].from_data(output)
