"""Upload and read receipt images through authorized panel routes."""

from collections.abc import AsyncIterator
from typing import Annotated

from anyio.abc import ByteReceiveStream
from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, Depends, Path, Request
from fastapi.responses import StreamingResponse
from papilio.api.responses.envelope import APIResponse
from papilio.core.config import StorageConfig

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.storage.files.routers.streams import RequestBodyStream

from ...app.interfaces.images import IReceiptImages
from ...domain.enums.images import ImageFormat
from ..schemas.images import ImageOutput

router = APIRouter(
    prefix="/admin/receipts/images",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("billing"))],
)


@router.post(
    "", response_model=APIResponse[ImageOutput, None], status_code=201
)
async def post_image(
    request: Request,
    format: ImageFormat,
    images: FromDishka[IReceiptImages],
    config: FromDishka[StorageConfig],
) -> APIResponse[ImageOutput, None]:
    """Stream the raw image body and return its protected address."""
    async with RequestBodyStream(
        request.stream(), max_bytes=config.max_file_size
    ) as source:
        digest = await images.upload(
            source, format, max_bytes=config.max_file_size
        )
    url = request.url_for(
        "get_receipt_image", format=format.value, digest=digest
    ).path
    return APIResponse[ImageOutput, None].from_data(ImageOutput(url=url))


@inject
async def image_stream(
    format: ImageFormat,
    digest: Annotated[str, Path(pattern=r"^[a-f0-9]{64}$")],
    images: FromDishka[IReceiptImages],
) -> AsyncIterator[ByteReceiveStream]:
    """Hold the open image stream until the response completes."""
    async with images.open(format, digest) as source:
        yield source


@router.get(
    "/{format}/{digest}",
    name="get_receipt_image",
    response_class=StreamingResponse,
)
async def get_image(
    format: ImageFormat,
    source: Annotated[ByteReceiveStream, Depends(image_stream)],
) -> StreamingResponse:
    """Stream evidence to an administrator with billing read permission."""
    return StreamingResponse(
        source,
        media_type=format.mime_type,
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
