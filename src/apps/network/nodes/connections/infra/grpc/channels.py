"""Own authenticated channels for versioned registry endpoints."""

from asyncio import Task, create_task, gather

import grpc
from grpc.aio import Channel
from py_bridge.api.grpc.client import create_channel

from src.apps.network.nodes.registry.app.interfaces.credentials import (
    INodeCredentialCipher,
)
from src.apps.network.nodes.registry.domain.results.records import NodeEndpoint


class NodeChannels:
    def __init__(self, credentials: INodeCredentialCipher) -> None:
        self.credentials = credentials
        self.channels: dict[int, tuple[int, Channel | None]] = {}
        self.retiring: set[Task[None]] = set()

    async def get(self, target: NodeEndpoint) -> Channel | None:
        """Borrow or replace the channel for this exact registry revision.

        Args:
            target: Materialized registry endpoint and encrypted credentials.

        Returns:
            A shared authenticated channel or None for an unusable snapshot.
        """
        cached = self.channels.get(target.id)
        channel = None
        if cached is not None and cached[0] >= target.connection_revision:
            if cached[0] == target.connection_revision:
                channel = cached[1]
        else:
            ciphertext = target.api_key_ciphertext
            key = (
                await self.credentials.open(ciphertext)
                if target.is_enabled and ciphertext is not None
                else None
            )
            # Another caller may install a newer channel during decryption.
            cached = self.channels.get(target.id)
            if cached is None or cached[0] < target.connection_revision:
                if key is not None:
                    address = target.address
                    host = f"[{address}]" if ":" in address else address
                    credentials = (
                        grpc.ssl_channel_credentials(target.ca_pem.encode())
                        if target.ca_pem is not None
                        else None
                    )
                    channel = create_channel(
                        f"{host}:{target.port}",
                        api_key=key.get_secret_value(),
                        credentials=credentials,
                    )
                self.channels[target.id] = (
                    target.connection_revision,
                    channel,
                )
                if cached is not None and cached[1] is not None:
                    retired = create_task(cached[1].close(grace=30))
                    self.retiring.add(retired)
                    retired.add_done_callback(self.retiring.discard)
            elif cached[0] == target.connection_revision:
                channel = cached[1]
        return channel

    async def close(self) -> None:
        """Join retirement and close the current generation on shutdown."""
        await gather(
            *(
                channel.close()
                for _, channel in self.channels.values()
                if channel
            ),
            *self.retiring,
        )
        self.channels.clear()
