"""Own shared authenticated channels to registered Node management targets."""

from contextlib import AsyncExitStack

import grpc
from grpc.aio import Channel
from py_bridge.api.grpc.client import create_channel

from ...config import NodeHostConfig


class NodeChannels:
    def __init__(
        self, config: NodeHostConfig, resources: AsyncExitStack
    ) -> None:
        self.config = config
        self.resources = resources
        self.channels: dict[int, Channel] = {}

    def get(self, node_id: int, address: str, port: int) -> Channel | None:
        """Borrow a channel only for an exact configured management target.

        Args:
            node_id: Core identity that owns the configured credential.
            address: Current address read from the node registry.
            port: Current port read from the node registry.

        Returns:
            An application-owned channel, or None for an unconfigured target.
        """
        target = self.config.targets.get(node_id)
        channel = None
        if target is not None and (address, port) == (
            target.address,
            target.port,
        ):
            channel = self.channels.get(node_id)
            if channel is None:
                host = f"[{address}]" if ":" in address else address
                credentials = (
                    grpc.ssl_channel_credentials(target.ca_pem.encode())
                    if target.ca_pem is not None
                    else None
                )
                channel = create_channel(
                    f"{host}:{port}",
                    api_key=target.api_key.get_secret_value(),
                    credentials=credentials,
                )
                self.resources.push_async_callback(channel.close)
                self.channels[node_id] = channel
        return channel
