"""Read IPG payment evidence in the Finance panel."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.services import IPaymentService
from ..schemas.records import PaymentOutput

router = APIRouter(
    prefix="/admin/ipg/payments",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("finance"))],
)


@router.get("/{id:int}")
async def get_payment(
    id: IdType, payments: FromDishka[IPaymentService]
) -> APIResponse[PaymentOutput, None]:
    payment = await payments.get_by_id(id)
    output = PaymentOutput.from_obj(payment)
    return APIResponse[PaymentOutput, None].from_data(output)
