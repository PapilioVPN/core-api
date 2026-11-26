"""Read checkout choices for a wallet top-up from the panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.queries import IDepositMethodsQuery
from ...domain.dtos.methods import DepositMethods
from ..schemas.methods import MethodsOutput

router = APIRouter(
    prefix="/admin/wallets/{customer_id:int}/deposits/methods",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.get("")
async def get_methods(
    customer_id: IdType,
    data: Annotated[DepositMethods, Query()],
    query: FromDishka[IDepositMethodsQuery],
) -> APIResponse[MethodsOutput, PagerMeta]:
    methods = await query.list(customer_id, data)
    meta = PagerMeta.from_total(
        data.page, data.per_page, methods.total_gateways
    )
    return APIResponse[MethodsOutput, PagerMeta](
        success=True, data=MethodsOutput.from_obj(methods), meta=meta
    )
