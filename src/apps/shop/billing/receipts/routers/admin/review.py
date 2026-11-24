"""Record an administrator's decision on a pending receipt."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.commands import IReceiptReviewCommand
from ...domain.dtos.review import ReceiptReview
from ..schemas.records import ReceiptOutput

router = APIRouter(prefix="/admin/receipts", route_class=DishkaRoute)


@router.patch("/{id:int}/review")
async def patch_review(
    id: IdType,
    data: ReceiptReview,
    actor: Annotated[AdminIdentity, Depends(require_admin("shop"))],
    command: FromDishka[IReceiptReviewCommand],
) -> APIResponse[ReceiptOutput, None]:
    receipt = await command.review(id, data, actor_id=actor.user_id)
    output = ReceiptOutput.from_obj(receipt)
    return APIResponse[ReceiptOutput, None].from_data(output)
