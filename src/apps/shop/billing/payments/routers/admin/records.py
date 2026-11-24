"""Register payments in the administrator panel."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.commands import IPaymentCommand
from ...domain.dtos.records import PaymentCreate
from ..schemas.records import PaymentOutput

router = APIRouter(
    prefix="/admin/payments",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_payment(
    data: PaymentCreate, command: FromDishka[IPaymentCommand]
) -> APIResponse[PaymentOutput, None]:
    payment = await command.create(data)
    output = PaymentOutput.from_obj(payment)
    return APIResponse[PaymentOutput, None].from_data(output)
