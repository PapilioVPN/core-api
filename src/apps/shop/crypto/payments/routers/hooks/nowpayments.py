"""Accept signed NOWPayments payment notifications."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Header, Response
from papilio.types.aliases import IdType
from pydantic import JsonValue

from ...app.interfaces.commands import IPaymentConfirmCommand
from ...app.interfaces.services import IPaymentNotificationService

router = APIRouter(prefix="/hooks/crypto/nowpayments", route_class=DishkaRoute)


@router.post("/{gateway_id:int}", status_code=204)
async def post_nowpayments(
    gateway_id: IdType,
    data: dict[str, JsonValue],
    signature: Annotated[str, Header(alias="x-nowpayments-sig")],
    command: FromDishka[IPaymentConfirmCommand],
    notifications: FromDishka[IPaymentNotificationService],
) -> Response:
    settlement = await notifications.verify(gateway_id, data, signature)
    if settlement is not None:
        await command.confirm(settlement)
    return Response(status_code=204)
