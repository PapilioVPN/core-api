"""Read individual or selected payments in the operator panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType, ListIdType

from src.apps.core.auth.routers.dependencies.authorization import require_admin

from ...app.interfaces.services import IPaymentCRUD
from ..schemas.records import PaymentOutput

router = APIRouter(
    prefix="/admin/payments",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("billing"))],
)


@router.get("/batch")
async def get_payments_batch(
    ids: Annotated[ListIdType, Query()], payments: FromDishka[IPaymentCRUD]
) -> APIResponse[PaymentOutput, None]:
    rows = await payments.get_by_ids(ids)
    return APIResponse[PaymentOutput, None].from_data(
        PaymentOutput.from_objs(rows)
    )


@router.get("/{id:int}")
async def get_payment(
    id: IdType, payments: FromDishka[IPaymentCRUD]
) -> APIResponse[PaymentOutput, None]:
    payment = await payments.get_by_id(id)
    return APIResponse[PaymentOutput, None].from_data(
        PaymentOutput.from_obj(payment)
    )
