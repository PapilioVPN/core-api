"""Serialize blocking response ownership while exposing bounded async reads."""

from threading import Lock

from anyio import CancelScope, ClosedResourceError, EndOfStream
from anyio.abc import ByteReceiveStream
from botocore.client import BaseClient
from botocore.response import StreamingBody

from src.apps.core.storage.files.infra.s3.client import (
    s3_session,
    s3_transport,
)
from src.apps.core.storage.providers.domain.dtos.configs import S3Config
from src.shared.utils.asyncio.threads import ThreadRunner


class S3ReadStream(ByteReceiveStream):
    def __init__(
        self, threads: ThreadRunner, config: S3Config, storage_key: str
    ) -> None:
        """Bind a blocking response owner before any worker can open it.

        Args:
            threads: Existing native thread runner.
            config: Explicit validated S3 destination and credentials.
            storage_key: Exact original object key.
        Returns:
            None. The lock serializes open/read/close inside worker threads,
            including cleanup when a caller cancels pending blocking I/O.
        """
        self.threads = threads
        self.config = config
        self.storage_key = storage_key
        self._lock = Lock()
        self._closed = False
        self._client: BaseClient | None = None
        self._body: StreamingBody | None = None

    def _open(self) -> None:
        """Open the client and response inside their serialized worker owner.

        Args:
            None.
        Returns:
            None. Partial resources remain owned until aclose runs.
        Raises:
            Exception: Native SDK failures propagate.
        """
        with self._lock:
            if self._closed:
                raise ClosedResourceError
            endpoint = (
                str(self.config.endpoint_url)
                if self.config.endpoint_url
                else None
            )
            client = s3_session(self.config).client(
                "s3", endpoint_url=endpoint, config=s3_transport(self.config)
            )
            self._client = client
            response = client.get_object(
                Bucket=self.config.bucket, Key=self.storage_key
            )
            self._body = response["Body"]

    async def start(self) -> None:
        """Run native SDK connection/response creation outside the loop.

        Args:
            None.
        Returns:
            None. The caller must own this object's finally/aclose boundary.
        """
        await self.threads.run(self._open)

    def _read(self, max_bytes: int) -> bytes:
        """Read one bounded response block while holding its worker ownership.

        Args:
            max_bytes: Positive bound no larger than one MiB.
        Returns:
            One nonempty block, without buffering the complete object.
        Raises:
            ClosedResourceError: The stream is closed or not open.
            EndOfStream: The native body is exhausted.
            Exception: Native read/integrity failures propagate unchanged.
        """
        with self._lock:
            if self._closed or self._body is None:
                raise ClosedResourceError
            chunk = self._body.read(max_bytes)
            if not chunk:
                raise EndOfStream
        return chunk

    async def receive(self, max_bytes: int = 65536) -> bytes:
        """Receive at most the requested bound and never more than one MiB.

        Args:
            max_bytes: Positive requested byte count.
        Returns:
            A nonempty block from the current response position.
        Raises:
            ValueError: The requested bound is not positive.
            Exception: EOF, closure and native SDK read errors propagate.
        """
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        chunk = await self.threads.run(self._read, min(max_bytes, 1024 * 1024))
        return chunk

    def _close(self) -> None:
        """Wait for pending worker I/O, then close both native resources once.

        Args:
            None.
        Returns:
            None. Repeated cleanup is harmless.
        """
        with self._lock:
            self._closed = True
            body, self._body = self._body, None
            client, self._client = self._client, None
            try:
                if body is not None:
                    body.close()
            finally:
                if client is not None:
                    client.close()

    async def aclose(self) -> None:
        """Close native blocking resources outside the event loop.

        Args:
            None.
        Returns:
            None. AnyIO cancellation scopes shield awaited cleanup.
        """
        with CancelScope(shield=True):
            await self.threads.run(self._close)
