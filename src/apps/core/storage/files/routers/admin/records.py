"""Administrative file metadata and transfers through their app contracts."""

from typing import Annotated
from urllib.parse import quote

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.core.config import StorageConfig
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.storage.files.app.interfaces.services import IFileService
from src.apps.core.storage.files.app.interfaces.uploads import IFileUpload
from src.apps.core.storage.files.domain.dtos.records import (
    FileBatchRead,
    FileList,
)
from src.apps.core.storage.files.domain.results.downloads import FileDownload
from src.apps.core.storage.files.routers.dependencies.records import (
    file_download,
)
from src.apps.core.storage.files.routers.schemas.records import (
    FileOutput,
    FileUploadInput,
)
from src.apps.core.storage.files.routers.streams import RequestBodyStream

router = APIRouter(
    prefix="/admin/storage/files",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("storage"))],
)


@router.post(
    "",
    response_model=APIResponse[FileOutput, None],
    status_code=201,
)
async def post_file(
    request: Request,
    data: Annotated[FileUploadInput, Query()],
    uploads: FromDishka[IFileUpload],
    config: FromDishka[StorageConfig],
) -> APIResponse[FileOutput, None]:
    """Stream a raw body into the configured local/S3 upload workflow.

    Args:
        request: Binary body; no full-body buffering or multipart parsing.
        data: Original name and declared MIME supplied in query parameters.
        uploads: Existing APP streaming/deduplication coordinator.
        config: Native byte limit for this management API. Business consumers
            may use their own routes, authorization, MIME and size policies.
    Returns:
        Committed logical metadata; location and credentials stay private.
    Raises:
        HTTPException: Actual body exceeds storage.max_file_size (413).
        Exception: Existing app validation, configuration and conflicts retain
            their native HTTP meanings; client disconnection propagates.
    """
    async with RequestBodyStream(
        request.stream(), max_bytes=config.max_file_size
    ) as source:
        result = await uploads.upload(
            source, data, max_bytes=config.max_file_size
        )
    output = FileOutput.from_obj(result.file)
    return APIResponse[FileOutput, None].from_data(output)


@router.get("", response_model=APIResponse[FileOutput, PagerMeta])
async def get_files(
    query: Annotated[FileList, Query()],
    service: FromDishka[IFileService],
) -> APIResponse[FileOutput, PagerMeta]:
    """Read a filtered page of logical metadata without loading file bytes.

    Args:
        query: Native page/per_page, literal case-insensitive name search and
            exact content/MIME filters. App owns page-to-offset conversion.
        service: Existing request-scoped file record service.
    Returns:
        ID-ordered metadata and native paging totals, including empty pages.
        Physical locations and credentials are excluded.
    """
    page = await service.list(query)
    output = FileOutput.from_objs(page.items)
    return APIResponse[FileOutput, PagerMeta](
        success=True,
        data=output,
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/batch", response_model=APIResponse[FileOutput, None])
async def get_file_batch(
    query: Annotated[FileBatchRead, Query()],
    service: FromDishka[IFileService],
) -> APIResponse[FileOutput, None]:
    """Read a bounded identity set using the existing native set operation.

    Args:
        query: One to 100 logical file IDs, including repeats and misses.
        service: Existing request-scoped file record service.
    Returns:
        Found metadata once each, omitting missing IDs; order is unspecified.
        No physical contents, locations or credentials are loaded.
    """
    files = await service.get_by_ids(query)
    output = FileOutput.from_objs(files)
    return APIResponse[FileOutput, None].from_data(output)


@router.get("/{id}", response_model=APIResponse[FileOutput, None])
async def get_file(
    id: IdType,
    service: FromDishka[IFileService],
) -> APIResponse[FileOutput, None]:
    """Read required logical metadata independently of physical storage.

    Args:
        id: Native positive logical file identity.
        service: Existing request-scoped file record service.
    Returns:
        Stored logical metadata without a physical location or credentials.
    Raises:
        NotFoundException: No logical file has this identity.
    """
    file = await service.get_by_id(id)
    output = FileOutput.from_obj(file)
    return APIResponse[FileOutput, None].from_data(output)


@router.get("/{id}/content", response_class=StreamingResponse)
async def get_file_content(
    download: Annotated[FileDownload, Depends(file_download)],
) -> StreamingResponse:
    """Download an authorized logical file from its recorded location.

    Args:
        download: Opened by the native yield dependency before headers; its
            stream remains owned until response completion or cancellation.
    Returns:
        Bounded attachment stream with recorded MIME and actual byte length.
        No storage path, S3 configuration or credentials are exposed.
    """
    metadata = download.metadata
    filename = quote(metadata.original_name, safe="")
    response = StreamingResponse(
        download.source,
        media_type=metadata.mime_type,
        headers={
            "Content-Length": str(metadata.size_bytes),
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
            "X-Content-Type-Options": "nosniff",
        },
    )
    return response
