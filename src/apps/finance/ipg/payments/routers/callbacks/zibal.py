"""Accept Zibal payment redirects."""

from typing import Annotated, Literal

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, Response

from ....gateways.domain.enums.records import GatewayKind
from ...app.interfaces.callback import IVerifyCallbackCommand

router = APIRouter(route_class=DishkaRoute)


@router.get("/callbacks/ipg/zibal", status_code=204)
async def zibal_callback(
    track_id: Annotated[
        str, Query(alias="trackId", pattern=r"^[0-9]{1,128}$")
    ],
    success: Annotated[Literal["0", "1"], Query()],
    command: FromDishka[IVerifyCallbackCommand],
) -> Response:
    if success == "1":
        await command.verify(GatewayKind.ZIBAL, track_id)
    return Response(status_code=204)
