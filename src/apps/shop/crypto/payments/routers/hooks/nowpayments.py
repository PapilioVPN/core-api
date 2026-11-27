"""Accept signed NOWPayments payment notifications."""

from http import HTTPStatus
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Header, Response
from fastapi.responses import JSONResponse
from papilio.api.responses.envelope import APIResponse
from papilio.errors.exceptions import ConflictException, UnAuthorizedException
from papilio.errors.outputs import BaseErrorOut
from papilio.types.aliases import IdType
from pydantic import JsonValue

from src.apps.shop.crypto.gateways.domain.results.configs import ConfigFailure

from ...app.interfaces.commands import IPaymentConfirmCommand
from ...app.interfaces.services import IPaymentNotificationService
from ...domain.results.records import PaymentFailure
from ...domain.results.settlement import Settlement

router = APIRouter(prefix="/hooks/crypto/nowpayments", route_class=DishkaRoute)


@router.post("/{gateway_id:int}", status_code=HTTPStatus.NO_CONTENT)
async def post_nowpayments(
    gateway_id: IdType,
    data: dict[str, JsonValue],
    signature: Annotated[str, Header(alias="x-nowpayments-sig")],
    command: FromDishka[IPaymentConfirmCommand],
    notifications: FromDishka[IPaymentNotificationService],
) -> Response:
    settlement = await notifications.verify(gateway_id, data, signature)
    result = Response(status_code=HTTPStatus.NO_CONTENT)
    if isinstance(settlement, Settlement):
        await command.confirm(settlement)
    elif settlement is PaymentFailure.INVALID_NOTIFICATION:
        raise UnAuthorizedException(
            message="Invalid NOWPayments notification signature.",
            message_code="nowpayments_signature_invalid",
        )
    elif settlement is PaymentFailure.INVOICE_MISMATCH:
        raise ConflictException(
            message="The notification does not match a full invoice payment.",
            message_code="nowpayments_invoice_mismatch",
            unique_dict={"gateway_id": gateway_id},
        )
    elif isinstance(settlement, ConfigFailure):
        body = APIResponse[None, None](
            success=False,
            error=BaseErrorOut(
                message="The gateway configuration is unavailable.",
                message_code="crypto_gateway_config_unavailable",
            ),
        )
        result = JSONResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            content=body.model_dump(mode="json"),
        )
    return result
