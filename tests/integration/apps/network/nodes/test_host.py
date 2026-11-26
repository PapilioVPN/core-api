"""Exercise Panel host observations over native, authenticated gRPC."""

import asyncio
from collections.abc import AsyncIterator
from typing import cast

import grpc
import pytest
import trustme
from dishka import AsyncContainer
from fastapi import FastAPI
from google.protobuf.empty_pb2 import Empty
from grpc import aio
from httpx import AsyncClient

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.config import NodeHostConfig
from src.apps.network.nodes.domain.dtos.records import NodeCreate
from src.apps.network.nodes.infra.grpc.v1.host_pb2 import (
    CPUSnapshot,
    MemorySnapshot,
    NetworkSnapshot,
    StorageSnapshot,
    SystemSnapshot,
)
from src.apps.network.nodes.infra.grpc.v1.host_pb2_grpc import (
    HostServiceServicer,
    add_HostServiceServicer_to_server,
)
from src.settings.config import CoreSettings

from .auth import admin_headers

pytestmark = pytest.mark.integration

NODE_KEY = "isolated-host-rpc-test-key"


class HostPeer(HostServiceServicer):
    def __init__(self) -> None:
        self.snapshot = SystemSnapshot(
            uptime_seconds=0,
            logical_cpu_count=4,
            memory=MemorySnapshot(total_bytes=(1 << 64) - 1, used_bytes=0),
        )
        self.peers: set[str] = set()
        self.error: grpc.StatusCode | None = None
        self.block = False
        self.calls = 0

    async def GetSystemStats(  # noqa: N802 - Generated RPC method name.
        self,
        request: Empty,
        context: aio.ServicerContext[Empty, SystemSnapshot],
    ) -> SystemSnapshot:
        metadata = context.invocation_metadata() or ()
        if not any(
            key == "x-api-key" and value == NODE_KEY for key, value in metadata
        ):
            await context.abort(grpc.StatusCode.UNAUTHENTICATED)
        self.peers.add(context.peer())
        self.calls += 1
        if self.error is not None:
            await context.abort(self.error, "private transport detail")
        if self.block:
            await asyncio.Event().wait()
        return self.snapshot


@pytest.fixture
async def host_peer() -> AsyncIterator[tuple[HostPeer, aio.Server, int, str]]:
    ca = trustme.CA()
    cert = ca.issue_cert("127.0.0.1")
    credentials = grpc.ssl_server_credentials(
        [(cert.private_key_pem.bytes(), cert.cert_chain_pems[0].bytes())]
    )
    server = aio.server()
    peer = HostPeer()
    add_HostServiceServicer_to_server(peer, server)
    port = server.add_secure_port("127.0.0.1:0", credentials)
    await server.start()
    try:
        yield peer, server, port, ca.cert_pem.bytes().decode()
    finally:
        await server.stop(None)


async def test_live_host_stats(
    host_peer: tuple[HostPeer, aio.Server, int, str],
    pg: CoreSettings,
    app: FastAPI,
    client: AsyncClient,
) -> None:
    peer, server, port, ca_pem = host_peer
    headers = await admin_headers(app, client)
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        nodes = await scope.get(INodeService)
        record = await nodes.create(
            NodeCreate(name="Live host", address="127.0.0.1", port=port)
        )
    node_id = record.id
    assert node_id is not None
    node = f"/admin/nodes/{node_id}"
    url = f"{node}/host-stats"
    pg.node_host = NodeHostConfig.model_validate(
        {
            "timeout_seconds": 0.25,
            "targets": {
                node_id: {
                    "address": "127.0.0.1",
                    "port": port,
                    "api_key": NODE_KEY,
                    "ca_pem": ca_pem,
                }
            },
        }
    )
    unauthorized = await client.get(url)
    assert unauthorized.status_code == 401
    absent = await client.get("/admin/nodes/99999/host-stats", headers=headers)
    assert absent.status_code == 404, absent.text
    inventory = await client.get(node, headers=headers)
    assert inventory.json()["data"]["connection_status"] == "unchecked"
    assert peer.calls == 0

    reply = await client.get(url, headers=headers)
    assert reply.status_code == 200, reply.text
    data = reply.json()["data"]
    assert data["node_id"] == node_id
    assert data["status"] == "partial"
    assert data["received_at"]
    assert data["stats"] == {
        "uptime_seconds": "0",
        "logical_cpu_count": 4,
        "cpu": None,
        "memory": {
            "total_bytes": str((1 << 64) - 1),
            "available_bytes": None,
            "used_bytes": "0",
            "swap_total_bytes": "0",
            "swap_free_bytes": "0",
        },
        "storage": None,
        "network": None,
    }
    peer.snapshot.cpu.CopyFrom(CPUSnapshot(steal_percent=0))
    peer.snapshot.storage.CopyFrom(StorageSnapshot(read_only=False))
    peer.snapshot.network.CopyFrom(NetworkSnapshot())
    reply = await client.get(url, headers=headers)
    assert reply.status_code == 200, reply.text
    data = reply.json()["data"]
    assert data["status"] == "available"
    assert data["stats"]["cpu"]["steal_percent"] == 0
    assert data["stats"]["storage"]["read_only"] is False
    assert len(peer.peers) == 1

    peer.snapshot.logical_cpu_count = 0
    reply = await client.get(url, headers=headers)
    assert reply.json()["data"]["status"] == "partial"
    assert reply.json()["data"]["stats"]["logical_cpu_count"] is None

    peer.error = grpc.StatusCode.PERMISSION_DENIED
    reply = await client.get(url, headers=headers)
    assert reply.json()["data"]["status"] == "rejected"
    assert "private transport detail" not in reply.text
    peer.error = None
    peer.block = True
    reply = await client.get(url, headers=headers)
    assert reply.json()["data"]["status"] == "timeout"
    peer.block = False

    before = peer.calls
    paused = await client.patch(
        node, headers=headers, json={"is_enabled": False}
    )
    assert paused.status_code == 200, paused.text
    assert (await client.get(url, headers=headers)).json()["data"][
        "status"
    ] == "disabled"
    changed = await client.patch(
        node,
        headers=headers,
        json={"is_enabled": True, "address": "other.example.invalid"},
    )
    assert changed.status_code == 200, changed.text
    assert (await client.get(url, headers=headers)).json()["data"][
        "status"
    ] == "not_configured"
    assert peer.calls == before
    restored = await client.patch(
        node, headers=headers, json={"address": "127.0.0.1"}
    )
    assert restored.status_code == 200, restored.text
    await server.stop(None)
    reply = await client.get(url, headers=headers)
    assert reply.json()["data"]["status"] == "unavailable"
    assert reply.json()["data"]["stats"] is None
