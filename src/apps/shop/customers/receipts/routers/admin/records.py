"""Register receipts and read their images through the customer scope."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Path,
    Query,
    Request,
)
from fastapi.responses import FileResponse
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.auth.routers.dependencies.authorization import require_admin
from src.apps.core.storage.app.errors import FileTooLarge
from src.apps.core.storage.app.interfaces.files import IFileStorage
from src.apps.core.storage.routers.streams import RequestBodyStream

from ...app.commands.records import IMAGES_PATH, RECEIPTS_PATH
from ...app.interfaces.commands import IReceiptCommand
from ...app.interfaces.services import IReceiptCRUD
from ...domain.dtos.records import ImageType, ReceiptCreate
from ..schemas.records import ReceiptOutput

router = APIRouter(
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("customers"))],
)


@router.post("/admin/customers/{customer_id:int}/receipts", status_code=201)
async def post_receipt(
    customer_id: IdType,
    data: Annotated[ReceiptCreate, Query()],
    request: Request,
    mime_type: Annotated[ImageType, Header(alias="Content-Type")],
    command: FromDishka[IReceiptCommand],
) -> APIResponse[ReceiptOutput, None]:
    try:
        async with RequestBodyStream(request.stream()) as source:
            receipt = await command.create(
                customer_id, data, source, mime_type=mime_type
            )
    except FileTooLarge as error:
        raise HTTPException(413, str(error)) from error
    return APIResponse[ReceiptOutput, None].from_data(
        ReceiptOutput.from_obj(receipt)
    )


@router.get(f"{RECEIPTS_PATH}/{{id:int}}")
async def get_receipt(
    id: IdType, receipts: FromDishka[IReceiptCRUD]
) -> APIResponse[ReceiptOutput, None]:
    receipt = await receipts.get_by_id(id)
    return APIResponse[ReceiptOutput, None].from_data(
        ReceiptOutput.from_obj(receipt)
    )


@router.get(
    f"{IMAGES_PATH}/{{name}}",
    response_class=FileResponse,
)
async def get_receipt_image(
    name: Annotated[str, Path(pattern=r"^[0-9a-f]{64}\.(jpeg|png|webp)$")],
    receipts: FromDishka[IReceiptCRUD],
    files: FromDishka[IFileStorage],
) -> FileResponse:
    await receipts.check_image(f"{IMAGES_PATH}/{name}")
    path = await files.get_path(name)
    return FileResponse(path, headers={"Cache-Control": "private, no-store"})
