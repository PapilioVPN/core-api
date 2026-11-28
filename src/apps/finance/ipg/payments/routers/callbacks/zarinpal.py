"""Accept ZarinPal payment redirects."""

from typing import Annotated, Literal

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, Response

from ....gateways.domain.enums.records import GatewayKind
from ...app.interfaces.callback import IVerifyCallbackCommand

router = APIRouter(route_class=DishkaRoute)


@router.get("/callbacks/ipg/zarinpal", status_code=204)
async def zarinpal_callback(
    authority: Annotated[
        str, Query(alias="Authority", min_length=1, max_length=128)
    ],
    status: Annotated[Literal["OK", "NOK"], Query(alias="Status")],
    command: FromDishka[IVerifyCallbackCommand],
) -> Response:
    if status == "OK":
        await command.verify(GatewayKind.ZARINPAL, authority)
    return Response(status_code=204)
