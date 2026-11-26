"""Register and read wallet top-up requests in the administrator panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.services import IWalletDepositService
from ...domain.dtos.records import DepositCreate, DepositSearch
from ..schemas.records import DepositOutput

router = APIRouter(
    prefix="/admin/wallets/{customer_id:int}/deposits",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_deposit(
    customer_id: IdType,
    data: DepositCreate,
    service: FromDishka[IWalletDepositService],
) -> APIResponse[DepositOutput, None]:
    row = await service.create(customer_id, data)
    output = DepositOutput.from_obj(row)
    return APIResponse[DepositOutput, None].from_data(output)


@router.get("")
async def get_deposits(
    customer_id: IdType,
    data: Annotated[DepositSearch, Query()],
    service: FromDishka[IWalletDepositService],
) -> APIResponse[DepositOutput, PagerMeta]:
    page = await service.search(customer_id, data)
    return APIResponse[DepositOutput, PagerMeta](
        success=True,
        data=DepositOutput.from_objs(page.items),
        meta=PagerMeta.from_total(data.page, data.per_page, page.total_items),
    )


@router.get("/{id:int}")
async def get_deposit(
    customer_id: IdType, id: IdType, service: FromDishka[IWalletDepositService]
) -> APIResponse[DepositOutput, None]:
    row = await service.get_by_id(customer_id, id)
    output = DepositOutput.from_obj(row)
    return APIResponse[DepositOutput, None].from_data(output)
