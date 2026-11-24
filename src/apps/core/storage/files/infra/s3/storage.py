"""Conditional native S3 uploads and operation-owned streamed downloads."""

import errno
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, closing
from os import fstat

from anyio.abc import ByteReceiveStream
from botocore.exceptions import ClientError

from src.apps.core.storage.files.domain.results.staging import StagedFile
from src.apps.core.storage.files.infra.s3.client import (
    s3_session,
    s3_transport,
)
from src.apps.core.storage.files.infra.s3.streams import S3ReadStream
from src.apps.core.storage.providers.domain.dtos.configs import S3Config
from src.shared.utils.asyncio.threads import ThreadRunner


def put_if_absent(
    data: StagedFile, config: S3Config, *, storage_key: str, mime_type: str
) -> str | None:
    """Stream one file through native conditional PutObject in a worker.

    Args:
        data: Trusted source retained unchanged in its staging context.
        config: Explicit validated destination and credentials.
        storage_key: Exact app-owned object key.
        mime_type: Declared content type.
    Returns:
        Acknowledged key, or None only for PreconditionFailed/412. This uses
        native single-request size limits; multipart is a separate increment.
    Raises:
        OSError: Source cannot be opened or its size changed.
        ClientError: Other SDK failures, including unsupported conditions and
            races, propagate without an unconditional fallback.
    """
    key = None
    endpoint = str(config.endpoint_url) if config.endpoint_url else None
    with data.path.open("rb") as source:
        if fstat(source.fileno()).st_size != data.size_bytes:
            raise OSError("Prepared file size changed before S3 upload")
        with closing(
            s3_session(config).client(
                "s3", endpoint_url=endpoint, config=s3_transport(config)
            )
        ) as client:
            try:
                client.put_object(
                    Bucket=config.bucket,
                    Key=storage_key,
                    Body=source,
                    ContentLength=data.size_bytes,
                    ContentType=mime_type,
                    IfNoneMatch="*",
                )
                key = storage_key
            except ClientError as error:
                if not (
                    error.response["ResponseMetadata"]["HTTPStatusCode"] == 412
                    and error.response["Error"]["Code"] == "PreconditionFailed"
                ):
                    raise
    return key


class S3FileStorage:
    def __init__(self, threads: ThreadRunner) -> None:
        """Bind blocking SDK calls without opening clients or SQL resources.

        Args:
            threads: Existing application-owned native thread runner.
        Returns:
            None. Clients and responses remain operation-owned.
        """
        self.threads = threads

    async def save_if_absent(
        self,
        data: StagedFile,
        config: S3Config,
        *,
        storage_key: str,
        mime_type: str,
    ) -> str | None:
        """Upload conditionally without buffering file bytes on the event loop.

        Args:
            data: Caller-owned staging output kept unchanged during transfer.
            config: Explicit validated S3 connection.
            storage_key: App-owned object key, not a public URL.
            mime_type: Declared content type.
        Returns:
            Acknowledged key, or None for an existing destination. No DB state
            is read/written; cancellation does not undo a remote publication.
        Raises:
            Exception: Native file/SDK errors propagate unchanged.
        """
        key = await self.threads.run(
            put_if_absent,
            data,
            config,
            storage_key=storage_key,
            mime_type=mime_type,
        )
        return key

    async def save(
        self,
        data: StagedFile,
        config: S3Config,
        *,
        storage_key: str,
        mime_type: str,
    ) -> str:
        """Require a newly published object through the conditional SDK path.

        Args:
            data: Trusted staged source.
            config: Explicit validated S3 connection.
            storage_key: App-owned object key.
            mime_type: Declared content type.
        Returns:
            Acknowledged newly published key.
        Raises:
            FileExistsError: The object already exists and is not replaced.
            Exception: Other file/SDK failures propagate unchanged.
        """
        key = await self.save_if_absent(
            data, config, storage_key=storage_key, mime_type=mime_type
        )
        if key is None:
            raise FileExistsError(
                errno.EEXIST, "S3 object exists", storage_key
            )
        return key

    @asynccontextmanager
    async def open(
        self, config: S3Config, *, storage_key: str
    ) -> AsyncIterator[ByteReceiveStream]:
        """Open a bounded SDK response with explicit asynchronous cleanup.

        Args:
            config: Explicit recorded destination and current credentials.
            storage_key: Exact original object key.
        Returns:
            A native byte stream bridge, closed with its SDK client on exit.
            Worker ownership exists before opening, including failed/cancelled
            opens; no live response is abandoned between worker and caller.
        Raises:
            Exception: Native SDK/read failures propagate with no fallback.
        """
        source = S3ReadStream(self.threads, config, storage_key)
        try:
            await source.start()
            yield source
        finally:
            await source.aclose()
