"""Open before response headers and close after streaming or disconnection."""

from collections.abc import AsyncIterator

from dishka.integrations.fastapi import FromDishka, inject
from papilio.types.aliases import IdType

from src.apps.core.storage.files.app.interfaces.downloads import IFileDownload
from src.apps.core.storage.files.domain.results.downloads import FileDownload


@inject
async def file_download(
    id: IdType, downloads: FromDishka[IFileDownload]
) -> AsyncIterator[FileDownload]:
    """Keep the app download context alive for the whole response.

    Args:
        id: Logical reference authorized by the owning router dependency.
        downloads: APP coordinator; SQL preparation closes before byte I/O.
    Returns:
        Native yield dependency containing metadata and an open byte stream.
        FastAPI finalizes it on success, response failure or cancellation.
    Raises:
        Exception: App preparation/open errors retain their native meaning and
            occur before the HTTP response starts.
    """
    async with downloads.open(id) as download:
        yield download
