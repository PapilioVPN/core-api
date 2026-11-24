"""Conditional object publication and scoped response streaming."""

from base64 import b64encode
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from errno import EEXIST
from os import fstat

from anyio import open_file, to_thread
from anyio.abc import ByteReceiveStream
from botocore.exceptions import ClientError

from src.apps.core.storage.files.domain.results.staging import StagedFile
from src.apps.core.storage.files.infra.s3.client import S3Clients
from src.apps.core.storage.files.infra.s3.streams import S3ReadStream
from src.apps.core.storage.providers.domain.dtos.configs import S3Config


class S3FileStorage:
    def __init__(self, clients: S3Clients) -> None:
        self._clients = clients

    async def save_if_absent(
        self,
        data: StagedFile,
        config: S3Config,
        *,
        storage_key: str,
        mime_type: str,
    ) -> str | None:
        """Stream the staged bytes with their precomputed SHA-256.

        Args:
            data: Staged file retained unchanged by the caller.
            config: The selected provider connection.
            storage_key: The exact destination object key.
            mime_type: The original declared content type.

        Returns:
            The key if uploaded, or None if S3 rejected an existing key.

        Raises:
            OSError: The staged file cannot be opened or its length changed.
            ClientError: An S3 error other than PreconditionFailed.
        """
        checksum = b64encode(bytes.fromhex(data.sha256)).decode("ascii")
        async with await open_file(data.path, "rb") as source:
            stat = await to_thread.run_sync(fstat, source.wrapped.fileno())
            if stat.st_size != data.size_bytes:
                raise OSError("Prepared file size changed before S3 upload")
            async with self._clients.open(config) as client:
                try:
                    await client.put_object(
                        Bucket=config.bucket,
                        Key=storage_key,
                        Body=source.wrapped,
                        ContentLength=data.size_bytes,
                        ContentType=mime_type,
                        ChecksumSHA256=checksum,
                        IfNoneMatch="*",
                    )
                except ClientError as error:
                    metadata = error.response.get("ResponseMetadata")
                    body = error.response.get("Error")
                    if (
                        metadata
                        and metadata.get("HTTPStatusCode") == 412
                        and body
                        and body.get("Code") == "PreconditionFailed"
                    ):
                        return None
                    raise
        return storage_key

    async def save(
        self,
        data: StagedFile,
        config: S3Config,
        *,
        storage_key: str,
        mime_type: str,
    ) -> str:
        """Publish a new object, or raise FileExistsError for a collision."""
        key = await self.save_if_absent(
            data, config, storage_key=storage_key, mime_type=mime_type
        )
        if key is None:
            raise FileExistsError(EEXIST, "S3 object exists", storage_key)
        return key

    @asynccontextmanager
    async def open(
        self, config: S3Config, *, storage_key: str
    ) -> AsyncGenerator[ByteReceiveStream]:
        """Open a bounded read from the recorded bucket and object key."""
        async with self._clients.open(config) as client:
            response = await client.get_object(
                Bucket=config.bucket, Key=storage_key
            )
            async with (
                response["Body"] as body,
                S3ReadStream(body) as source,
            ):
                yield source
