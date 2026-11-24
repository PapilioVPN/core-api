"""Register a receipt after an administrator uploads its image."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.images import IReceiptImages
from ...app.interfaces.services import IReceiptService
from ...domain.dtos.records import ReceiptCreate
from ...domain.enums.images import ImageFormat
from ..schemas.records import ReceiptOutput

router = APIRouter(
    prefix="/admin/receipts",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("billing"))],
)


@router.post(
    "", response_model=APIResponse[ReceiptOutput, None], status_code=201
)
async def post_receipt(
    data: ReceiptCreate,
    images: FromDishka[IReceiptImages],
    receipts: FromDishka[IReceiptService],
) -> APIResponse[ReceiptOutput, None]:
    """Check the uploaded image, then register its receipt."""
    _, format, digest = data.image_url.rsplit("/", 2)
    async with images.open(ImageFormat(format), digest):
        pass
    receipt = await receipts.create(data)
    return APIResponse[ReceiptOutput, None].from_data(
        ReceiptOutput.from_obj(receipt)
    )
