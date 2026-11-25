"""Issue and inspect hosted crypto payments from the Shop panel."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response
from papilio.api.responses.envelope import APIResponse
from papilio.errors.outputs import BaseErrorOut
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.commands import ICryptoPaymentCommand
from ...app.interfaces.services import ICryptoPaymentService
from ...domain.dtos.records import PaymentIssue
from ...domain.errors import GatewayUnavailable
from ..schemas.records import PaymentOutput

router = APIRouter(
    prefix="/admin/crypto-payments",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_payment(
    data: PaymentIssue,
    response: Response,
    command: FromDishka[ICryptoPaymentCommand],
    service: FromDishka[ICryptoPaymentService],
) -> APIResponse[PaymentOutput, None]:
    error: BaseErrorOut | None = None
    try:
        payment = await command.issue(data)
    except GatewayUnavailable as failure:
        if failure.payment_id is None:
            raise
        payment = await service.get_by_id(failure.payment_id)
        response.status_code = failure.status_code
        error = failure.as_schema()
    return APIResponse[PaymentOutput, None](
        success=error is None,
        data=PaymentOutput.from_obj(payment),
        error=error,
    )


@router.get("/{id:int}")
async def get_payment(
    id: IdType, service: FromDishka[ICryptoPaymentService]
) -> APIResponse[PaymentOutput, None]:
    payment = await service.get_by_id(id)
    return APIResponse[PaymentOutput, None].from_data(
        PaymentOutput.from_obj(payment)
    )
