"""Search customer profiles with native paging and filters."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta

from src.apps.core.auth.routers.dependencies.authorization import require_admin

from ...app.interfaces.queries import IProfileSearch
from ...domain.dtos.search import ProfileSearch
from ..schemas.records import ProfileOutput

router = APIRouter(
    prefix="/admin/customers",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("customers"))],
)


@router.get("")
async def get_customers(
    data: Annotated[ProfileSearch, Query()], query: FromDishka[IProfileSearch]
) -> APIResponse[ProfileOutput, PagerMeta]:
    page = await query.search(data)
    return APIResponse[ProfileOutput, PagerMeta](
        success=True,
        data=ProfileOutput.from_objs(page.items),
        meta=PagerMeta.from_total(data.page, data.per_page, page.total_items),
    )
