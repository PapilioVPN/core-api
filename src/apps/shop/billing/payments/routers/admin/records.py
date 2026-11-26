"""Register payments and read their evidence in the administrator panel."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.commands import (
    IPaymentConfirmCommand,
    IPaymentCreateCommand,
    IPaymentRejectCommand,
)
from ...app.interfaces.queries import IPaymentQuery
from ...domain.dtos.records import PaymentCreate
from ...domain.dtos.review import PaymentReview
from ...domain.enums.records import PaymentStatus
from ..schemas.records import (
    PaymentDetailOutput,
    PaymentOutput,
    PaymentReviewOutput,
)

router = APIRouter(
    prefix="/admin/payments",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_payment(
    data: PaymentCreate, command: FromDishka[IPaymentCreateCommand]
) -> APIResponse[PaymentOutput, None]:
    payment = await command.create(data)
    output = PaymentOutput.from_obj(payment)
    return APIResponse[PaymentOutput, None].from_data(output)


@router.get("/{id:int}")
async def get_payment(
    id: IdType, query: FromDishka[IPaymentQuery]
) -> APIResponse[PaymentDetailOutput, None]:
    detail = await query.get_by_id(id)
    output = PaymentDetailOutput.from_obj(detail)
    return APIResponse[PaymentDetailOutput, None].from_data(output)


@router.patch("/{id:int}/review")
async def patch_payment_review(
    id: IdType,
    data: PaymentReview,
    confirm: FromDishka[IPaymentConfirmCommand],
    reject: FromDishka[IPaymentRejectCommand],
) -> APIResponse[PaymentReviewOutput, None]:
    if data.status == PaymentStatus.CONFIRMED:
        payment = await confirm.confirm(id)
    else:
        payment = await reject.reject(id, reason=data.reason)
    output = PaymentReviewOutput.from_obj(payment)
    return APIResponse[PaymentReviewOutput, None].from_data(output)
