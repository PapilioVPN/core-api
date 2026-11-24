"""Upload receipt evidence independently of a payment."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query, Request
from papilio.api.responses.envelope import APIResponse
from papilio.core.config import StorageConfig

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.storage.files.routers.streams import RequestBodyStream

from ...app.interfaces.uploads import IReceiptUpload
from ...domain.dtos.uploads import ReceiptUpload
from ..schemas.uploads import ReceiptUploadOutput

router = APIRouter(
    prefix="/admin/receipts",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("/images", status_code=201)
async def post_receipt_image(
    request: Request,
    data: Annotated[ReceiptUpload, Query()],
    uploads: FromDishka[IReceiptUpload],
    config: FromDishka[StorageConfig],
) -> APIResponse[ReceiptUploadOutput, None]:
    async with RequestBodyStream(
        request.stream(), max_bytes=config.max_file_size
    ) as source:
        result = await uploads.upload(
            source, data, max_bytes=config.max_file_size
        )
    output = ReceiptUploadOutput(url=result.url)
    return APIResponse[ReceiptUploadOutput, None].from_data(output)
