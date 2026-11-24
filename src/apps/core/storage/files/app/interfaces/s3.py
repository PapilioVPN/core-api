"""Database-independent conditional S3 publication and scoped byte streams."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from anyio.abc import ByteReceiveStream

from src.apps.core.storage.files.domain.results.staging import StagedFile
from src.apps.core.storage.providers.domain.dtos.configs import S3Config


class IS3FileStorage(Protocol):
    async def save(
        self,
        data: StagedFile,
        config: S3Config,
        *,
        storage_key: str,
        mime_type: str,
    ) -> str:
        """Publish a staged file with a conditional native PutObject request.

        Args:
            data: Trusted, unchanged source kept in its staging context.
            config: Explicit validated destination and credentials.
            storage_key: Trusted object key chosen by the owning app.
            mime_type: Declared content type selected by the owning app.
        Returns:
            The acknowledged object key, without metadata registration.
        Raises:
            FileExistsError: Conditional publication found an existing key.
            Exception: File/SDK errors propagate. No unconditional fallback,
                multipart emulation or distributed transaction is introduced.
        """
        ...

    async def save_if_absent(
        self,
        data: StagedFile,
        config: S3Config,
        *,
        storage_key: str,
        mime_type: str,
    ) -> str | None:
        """Publish once; report an existing key without adopting its bytes.

        Args:
            data: Trusted staging output, retained by the caller.
            config: Explicit validated S3 connection.
            storage_key: App-owned object key.
            mime_type: Declared content type.
        Returns:
            Acknowledged key, or None for native PreconditionFailed/412 only.
        Raises:
            Exception: Other file/SDK failures propagate unchanged.
        """
        ...

    def open(
        self, config: S3Config, *, storage_key: str
    ) -> AbstractAsyncContextManager[ByteReceiveStream]:
        """Open an operation-owned S3 byte stream without database resources.

        Args:
            config: Explicit recorded destination and current credentials.
            storage_key: Trusted original object key, not a URL.
        Returns:
            A context yielding a native byte-stream bridge. Reads are bounded
            to one MiB; context exit closes the response and SDK client.
        Raises:
            Exception: Native SDK/read errors propagate, with no fallback.
        """
        ...
