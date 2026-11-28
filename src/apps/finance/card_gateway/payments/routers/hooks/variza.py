"""Acknowledge Variza deliveries after payment confirmation completes."""

from http import HTTPStatus
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response

from ...app.interfaces.commands import IConfirmPaymentCommand
from ...domain.dtos.paid import PaidDelivery
from ..dependencies.variza import read_variza_delivery

router = APIRouter(
    prefix="/hooks/card-gateway/variza", route_class=DishkaRoute
)


@router.post("/{gateway_id:int}", response_class=Response)
async def post_variza(
    delivery: Annotated[PaidDelivery | None, Depends(read_variza_delivery)],
    command: FromDishka[IConfirmPaymentCommand],
) -> Response:
    if delivery is not None:
        await command.confirm(delivery)
    return Response(status_code=HTTPStatus.OK)
