"""Read cached prices and request refreshes from the Shop panel."""

from http import HTTPStatus

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response
from papilio.api.responses.envelope import APIResponse
from papilio.errors.outputs import BaseErrorOut

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.cache import IRateCache
from ...app.interfaces.refresh import IRateRefreshPublisher
from ...domain.results.records import RateFailure
from ..schemas.records import RateOutput
from ..schemas.refresh import RefreshAccepted

router = APIRouter(
    prefix="/admin/crypto-rates",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.get("")
async def get_rates(
    response: Response, cache: FromDishka[IRateCache]
) -> APIResponse[RateOutput, None]:
    rates = await cache.find_all()
    response.headers["Cache-Control"] = "no-store"
    if isinstance(rates, RateFailure):
        response.status_code = HTTPStatus.BAD_GATEWAY
        result = APIResponse[RateOutput, None](
            success=False,
            error=BaseErrorOut(
                message="The exchange rate is unavailable.",
                message_code="crypto_rate_unavailable",
            ),
        )
    else:
        result = APIResponse[RateOutput, None].from_data(
            RateOutput.from_objs(rates)
        )
    return result


@router.post("/refresh", status_code=HTTPStatus.ACCEPTED)
async def refresh(
    response: Response,
    publisher: FromDishka[IRateRefreshPublisher | RateFailure],
) -> APIResponse[RefreshAccepted, None]:
    task_id = (
        publisher
        if isinstance(publisher, RateFailure)
        else await publisher.enqueue()
    )
    if isinstance(task_id, RateFailure):
        response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
        result = APIResponse[RefreshAccepted, None](
            success=False,
            error=BaseErrorOut(
                message="Rate refresh could not be queued.",
                message_code="crypto_rate_refresh_unavailable",
            ),
        )
    else:
        result = APIResponse[RefreshAccepted, None].from_data(
            RefreshAccepted(task_id=task_id)
        )
    return result
