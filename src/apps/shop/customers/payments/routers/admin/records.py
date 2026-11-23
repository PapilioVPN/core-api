"""Register, read and review manual payments from the panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType, ListIdType

from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.auth.routers.dependencies.authorization import require_admin
from src.apps.core.auth.routers.dependencies.identity import current_admin

from ...app.interfaces.commands import IPaymentCommand
from ...app.interfaces.services import IPaymentCRUD
from ...domain.dtos.records import PaymentCreate, PaymentReview
from ..schemas.records import PaymentOutput

router = APIRouter(
    prefix="/admin/payments",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("customers"))],
)

CurrentAdmin = Annotated[AdminIdentity, Depends(current_admin)]


@router.post("", status_code=201)
async def post_payment(
    data: PaymentCreate, command: FromDishka[IPaymentCommand]
) -> APIResponse[PaymentOutput, None]:
    payment = await command.create(data)
    return APIResponse[PaymentOutput, None].from_data(
        PaymentOutput.from_obj(payment)
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


@router.patch("/{id:int}")
async def patch_payment(
    id: IdType,
    data: PaymentReview,
    identity: CurrentAdmin,
    payments: FromDishka[IPaymentCRUD],
) -> APIResponse[PaymentOutput, None]:
    payment = await payments.review(id, data, reviewer_id=identity.user_id)
    return APIResponse[PaymentOutput, None].from_data(
        PaymentOutput.from_obj(payment)
    )
