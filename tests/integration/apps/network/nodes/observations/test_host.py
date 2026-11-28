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

from src.apps.network.nodes.observations.infra.grpc.v1.host_pb2 import (
    CPUSnapshot,
    MemorySnapshot,
    NetworkSnapshot,
    StorageSnapshot,
    SystemSnapshot,
)
from src.apps.network.nodes.observations.infra.grpc.v1.host_pb2_grpc import (
    HostServiceServicer,
    add_HostServiceServicer_to_server,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)
from src.apps.network.nodes.registry.domain.dtos.records import NodeCreate
from tests.integration.apps.network.nodes.credentials import enroll_nodes

from ..auth import admin_headers

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
        self.deadline: float | None = None

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
        self.deadline = context.time_remaining()
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
    app: FastAPI,
    client: AsyncClient,
) -> None:
    peer, server, port, ca_pem = host_peer
    headers = await admin_headers(app, client)
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        nodes = await scope.get(INodeService)
        record = await nodes.create(
            NodeCreate(
                name="Live host",
                address="127.0.0.1",
                port=port,
                default_timeout=3,
            )
        )
    node_id = record.id
    assert node_id is not None
    node = f"/admin/nodes/{node_id}"
    url = f"{node}/host-stats"
    await enroll_nodes(
        app,
        {
            node_id: (NODE_KEY, ca_pem),
        },
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
    before_fleet = peer.calls
    fleet = await client.post(
        "/admin/nodes/host-stats",
        headers=headers,
        json={"node_ids": [node_id, 99999, node_id]},
    )
    assert fleet.status_code == 200, fleet.text
    reports = fleet.json()["data"]
    assert reports[0] == reports[2]
    assert reports[0]["stats"] == data["stats"]
    assert reports[1]["status"] == "node_not_found"
    assert peer.calls == before_fleet + 1

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
        node,
        headers=headers,
        json={"address": "127.0.0.1", "api_key": NODE_KEY, "ca_pem": ca_pem},
    )
    assert restored.status_code == 200, restored.text
    await server.stop(None)
    reply = await client.get(url, headers=headers)
    assert reply.json()["data"]["status"] == "unavailable"
    assert reply.json()["data"]["stats"] is None


async def test_panel_registration_and_key_rotation_drive_the_channel(
    host_peer: tuple[HostPeer, aio.Server, int, str],
    app: FastAPI,
    client: AsyncClient,
) -> None:
    peer, _, port, ca = host_peer
    headers = await admin_headers(
        app, client, mobile="09120000693", role_key="registry-node-key"
    )
    created = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Panel native host",
            "address": "127.0.0.1",
            "port": port,
            "api_key": NODE_KEY,
            "ca_pem": ca,
            "default_timeout": 7,
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["data"]["default_timeout"] == 7
    assert NODE_KEY not in created.text
    assert "ca_pem" not in created.json()["data"]
    path = f"/admin/nodes/{created.json()['data']['id']}"
    live = await client.get(f"{path}/host-stats", headers=headers)
    assert live.json()["data"]["status"] == "partial"
    assert peer.deadline is not None and 6 < peer.deadline <= 7.1
    invalid = await client.patch(
        path, headers=headers, json={"ca_pem": "invalid-certificate"}
    )
    assert invalid.status_code == 422
    assert "invalid-certificate" not in invalid.text

    changed = await client.patch(
        path, headers=headers, json={"api_key": "different-isolated-key"}
    )
    assert changed.status_code == 200, changed.text
    assert "different-isolated-key" not in changed.text
    rejected = await client.get(f"{path}/host-stats", headers=headers)
    assert rejected.json()["data"]["status"] == "rejected"
    restored = await client.patch(
        path, headers=headers, json={"api_key": NODE_KEY, "default_timeout": 4}
    )
    assert restored.status_code == 200, restored.text
    assert restored.json()["data"]["default_timeout"] == 4
    fleet = await client.post(
        "/admin/nodes/host-stats",
        headers=headers,
        json={"node_ids": [created.json()["data"]["id"]]},
    )
    assert fleet.status_code == 200, fleet.text
    assert fleet.json()["data"][0]["status"] == "partial"
    assert peer.deadline is not None and 3 < peer.deadline <= 4.1
    assert peer.calls == 2
