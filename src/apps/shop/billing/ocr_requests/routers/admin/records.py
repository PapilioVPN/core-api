"""Read receipt recognition history in the administrator panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.shop.billing.receipts.app.interfaces.services import (
    IReceiptService,
)

from ...app.interfaces.services import IOCRRequestService
from ...domain.dtos.records import OCRRequestList, OCRRequestPage
from ..schemas.records import OCRRequestOutput

router = APIRouter(
    prefix="/admin/receipts/{receipt_id:int}/ocr-requests",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.get("")
async def get_ocr_requests(
    receipt_id: IdType,
    data: Annotated[OCRRequestPage, Query()],
    receipts: FromDishka[IReceiptService],
    requests: FromDishka[IOCRRequestService],
) -> APIResponse[OCRRequestOutput, PagerMeta]:
    receipt = await receipts.get_by_id(receipt_id)
    query = OCRRequestList(
        receipt_id=receipt.id,
        page=data.page,
        per_page=data.per_page,
        status=data.status,
    )
    page = await requests.list(query)
    return APIResponse[OCRRequestOutput, PagerMeta](
        success=True,
        data=OCRRequestOutput.from_objs(page.items),
        meta=PagerMeta.from_total(data.page, data.per_page, page.total_items),
    )
