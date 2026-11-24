"""Application-owned asynchronous S3 clients and their SDK connections."""

from collections.abc import AsyncGenerator
from contextlib import (
    AbstractAsyncContextManager,
    AsyncExitStack,
    asynccontextmanager,
)
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from anyio import CancelScope, Lock
from anyio.abc import AsyncResource

from src.apps.core.storage.providers.domain.dtos.configs import S3Config

if TYPE_CHECKING:
    from types_aiobotocore_s3.client import S3Client

MAX_CACHED_CLIENTS = 8


@dataclass(slots=True)
class ClientEntry:
    client: "S3Client"
    users: int = 0


class S3Clients(AsyncResource):
    def __init__(self) -> None:
        self._session = get_session()
        self._clients: dict[tuple[str | None, ...], ClientEntry] = {}
        self._lock = Lock()

    def _create(
        self, config: S3Config, endpoint: str | None
    ) -> AbstractAsyncContextManager["S3Client"]:
        return self._session.create_client(
            "s3",
            endpoint_url=endpoint,
            region_name=config.region_name,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            aws_session_token=config.aws_session_token,
            config=AioConfig(
                signature_version="s3v4",
                connect_timeout=10,
                read_timeout=30,
                retries={"mode": "standard", "total_max_attempts": 3},
                s3={
                    "addressing_style": config.addressing_style,
                    "payload_signing_enabled": False,
                },
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    @asynccontextmanager
    async def open(self, config: S3Config) -> AsyncGenerator["S3Client"]:
        """Borrow a pooled client for this endpoint and credential snapshot.

        Args:
            config: The current connection settings validated by Storage.

        Yields:
            A client with an SDK connection pool and no owned response body.
        """
        endpoint = str(config.endpoint_url) if config.endpoint_url else None
        key = (
            endpoint,
            config.region_name,
            config.addressing_style,
            config.aws_access_key_id,
            config.aws_secret_access_key,
            config.aws_session_token,
        )
        async with self._lock:
            entry = self._clients.get(key)
            if entry is None:
                if len(self._clients) == MAX_CACHED_CLIENTS:
                    await self._evict_idle()
                if len(self._clients) < MAX_CACHED_CLIENTS:
                    with CancelScope(shield=True):
                        client = await self._create(
                            config, endpoint
                        ).__aenter__()
                        entry = self._clients[key] = ClientEntry(client)
            if entry is not None:
                entry.users += 1

        if entry is None:
            async with self._create(config, endpoint) as client:
                yield client
        else:
            try:
                yield entry.client
            finally:
                entry.users -= 1

    async def _evict_idle(self) -> None:
        for key, entry in self._clients.items():
            if entry.users == 0:
                with CancelScope(shield=True):
                    del self._clients[key]
                    await entry.client.close()
                break

    async def aclose(self) -> None:
        """Close the cached SDK clients when the application exits."""
        with CancelScope(shield=True):
            async with AsyncExitStack() as stack:
                for entry in self._clients.values():
                    stack.push_async_callback(entry.client.close)
                self._clients.clear()
