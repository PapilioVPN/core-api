"""Read filtered pages of payments in the operator panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta

from src.apps.core.auth.routers.dependencies.authorization import require_admin

from ...app.interfaces.queries import IPaymentSearch
from ...domain.dtos.search import PaymentSearch
from ..schemas.records import PaymentOutput

router = APIRouter(
    prefix="/admin/payments",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("billing"))],
)


@router.get("")
async def get_payments(
    data: Annotated[PaymentSearch, Query()], query: FromDishka[IPaymentSearch]
) -> APIResponse[PaymentOutput, PagerMeta]:
    page = await query.search(data)
    return APIResponse[PaymentOutput, PagerMeta](
        success=True,
        data=PaymentOutput.from_objs(page.items),
        meta=PagerMeta.from_total(data.page, data.per_page, page.total_items),
    )
