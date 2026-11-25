"""Read bank reports and their payment matches in the panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.services import IDepositService
from ...domain.dtos.records import DepositSearch
from ..schemas.records import DepositOutput

router = APIRouter(
    prefix="/admin/deposits",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.get("")
async def get_deposits(
    data: Annotated[DepositSearch, Query()],
    service: FromDishka[IDepositService],
) -> APIResponse[DepositOutput, PagerMeta]:
    page = await service.search(data)
    return APIResponse[DepositOutput, PagerMeta](
        success=True,
        data=DepositOutput.from_objs(page.items),
        meta=PagerMeta.from_total(data.page, data.per_page, page.total_items),
    )


@router.get("/{id:int}")
async def get_deposit(
    id: IdType, service: FromDishka[IDepositService]
) -> APIResponse[DepositOutput, None]:
    record = await service.get(id)
    output = DepositOutput.from_obj(record)
    return APIResponse[DepositOutput, None].from_data(output)
