"""Read card payments and record operator decisions."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.commands import IReviewPaymentCommand
from ...app.interfaces.queries import ICardPaymentQuery
from ...app.interfaces.services import ICardPaymentService
from ...domain.dtos.records import CardPaymentList
from ...domain.dtos.review import CardPaymentReview
from ..schemas.records import CardPaymentOutput

router = APIRouter(
    prefix="/admin/card-payments",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("finance"))],
)


@router.get("")
async def get_payments(
    query: Annotated[CardPaymentList, Query()],
    payments: FromDishka[ICardPaymentQuery],
) -> APIResponse[CardPaymentOutput, PagerMeta]:
    page = await payments.list(query)
    return APIResponse[CardPaymentOutput, PagerMeta](
        success=True,
        data=CardPaymentOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/{id:int}")
async def get_payment(
    id: IdType, service: FromDishka[ICardPaymentService]
) -> APIResponse[CardPaymentOutput, None]:
    payment = await service.get_by_id(id)
    return APIResponse[CardPaymentOutput, None].from_data(
        CardPaymentOutput.from_obj(payment)
    )


@router.patch("/{id:int}/review")
async def patch_review(
    id: IdType,
    data: CardPaymentReview,
    command: FromDishka[IReviewPaymentCommand],
) -> APIResponse[CardPaymentOutput, None]:
    payment = await command.review(id, data)
    return APIResponse[CardPaymentOutput, None].from_data(
        CardPaymentOutput.from_obj(payment)
    )
