"""Read Xray instance observations through the administrator API."""

import asyncio
from typing import cast

import grpc
import pytest
import trustme
from dishka import AsyncContainer
from fastapi import FastAPI
from grpc import aio
from httpx import ASGITransport, AsyncClient

from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)
from src.apps.network.nodes.registry.domain.dtos.records import NodeCreate
from src.apps.network.xray.instances.infra.grpc.v1.instances_pb2 import (
    XrayInstanceRequest,
    XrayInstanceState,
    XrayInstanceStatus,
)
from src.apps.network.xray.instances.infra.grpc.v1.instances_pb2_grpc import (
    XrayInstancesServiceServicer,
    add_XrayInstancesServiceServicer_to_server,
)
from src.bootstrap.api import create_api
from src.settings.config import CoreSettings
from tests.integration.apps.network.nodes.credentials import enroll_nodes

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
_KEY = "isolated-xray-status-test-key"


async def test_status_does_not_dial_unconfigured_node(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000921", role_key="xray-status-test"
    )
    created = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Xray status without access",
            "address": "unconfigured-xray-status.example.invalid",
            "port": 8081,
        },
    )
    assert created.status_code == 201, created.text
    id = created.json()["data"]["id"]
    url = f"/admin/nodes/{id}/xray/instances/edge"
    assert (await client.get(url)).status_code == 401
    response = await client.get(url, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["data"] == {
        "node_id": id,
        "instance_id": "edge",
        "status": "not_configured",
        "instance": None,
        "received_at": None,
    }
    assert (
        await client.get(url.replace("/edge", "/Invalid"), headers=headers)
    ).status_code == 422
    assert (
        await client.get(
            "/admin/nodes/9999999/xray/instances/edge", headers=headers
        )
    ).status_code == 404
    assert (
        await client.patch(
            f"/admin/nodes/{id}",
            headers=headers,
            json={"is_enabled": False},
        )
    ).status_code == 200
    stopped = await client.get(url, headers=headers)
    assert stopped.json()["data"]["status"] == "disabled"
    assert stopped.json()["data"]["instance"] is None


class StatusPeer(XrayInstancesServiceServicer):
    def __init__(self) -> None:
        self.pending = asyncio.Event()
        self.release = asyncio.Event()
        self.peers: set[str] = set()
        self.calls: list[str] = []

    async def GetStatus(
        self,
        request: XrayInstanceRequest,
        context: aio.ServicerContext[XrayInstanceRequest, XrayInstanceStatus],
    ) -> XrayInstanceStatus:
        assert [field.name for field, _ in request.ListFields()] == ["id"]
        metadata = context.invocation_metadata() or ()
        assert ("x-api-key", _KEY) in tuple(metadata)
        deadline = context.time_remaining()
        assert deadline is not None and 0 < deadline <= 3.1
        self.calls.append(request.id)
        self.peers.add(context.peer())
        if request.id == "held":
            self.pending.set()
            await self.release.wait()
        if request.id == "late":
            await context.abort(
                grpc.StatusCode.DEADLINE_EXCEEDED, "private deadline detail"
            )
        return XrayInstanceStatus(
            id=request.id,
            state=XrayInstanceState.XRAY_INSTANCE_STATE_READY,
            xray_version="test-xray",
            node_version="test-node",
            applied_config_sha256="a" * 64,
        )


async def test_status_reuses_channel_and_releases_database(
    pg: CoreSettings,
) -> None:
    assert pg.db is not None
    pg.db.pool_size = 1
    pg.db.max_overflow = 0
    app = create_api(pg)
    ca = trustme.CA()
    cert = ca.issue_cert("127.0.0.1")
    server = aio.server()
    peer = StatusPeer()
    add_XrayInstancesServiceServicer_to_server(peer, server)
    port = server.add_secure_port(
        "127.0.0.1:0",
        grpc.ssl_server_credentials(
            [(cert.private_key_pem.bytes(), cert.cert_chain_pems[0].bytes())]
        ),
    )
    await server.start()
    try:
        async with (
            app.router.lifespan_context(app),
            AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client,
        ):
            headers = await admin_headers(
                app, client, mobile="09120000922", role_key="xray-status-pool"
            )
            container = cast(AsyncContainer, app.state.dishka_container)
            async with container() as scope:
                nodes = await scope.get(INodeService)
                row = await nodes.create(
                    NodeCreate(
                        name="Xray status peer", address="127.0.0.1", port=port
                    )
                )
            assert row.id is not None
            await enroll_nodes(
                app,
                {
                    row.id: (_KEY, ca.cert_pem.bytes().decode()),
                },
            )
            node_url = f"/admin/nodes/{row.id}"
            instances = f"{node_url}/xray/instances"
            waiting = asyncio.create_task(
                client.get(f"{instances}/held", headers=headers)
            )
            try:
                await asyncio.wait_for(peer.pending.wait(), 2)
                async with asyncio.timeout(1.5):
                    record = await client.get(node_url, headers=headers)
                    assert record.status_code == 200, record.text
                    assert peer.calls == ["held"]
                    fast = await client.get(
                        f"{instances}/fast", headers=headers
                    )
                    assert fast.status_code == 200, fast.text
                    assert fast.json()["data"]["instance"]["state"] == "ready"
            finally:
                peer.release.set()
                held = await asyncio.wait_for(waiting, 4)
            assert held.status_code == 200, held.text
            assert held.json()["data"]["instance"][
                "applied_config_sha256"
            ] == ("a" * 64)
            assert peer.calls == ["held", "fast"]
            assert len(peer.peers) == 1
            timed_out = await client.get(f"{instances}/late", headers=headers)
            timeout_data = timed_out.json()["data"]
            assert timeout_data["status"] == "timeout"
            assert timeout_data["instance"] is None
            assert timeout_data["received_at"] is None
            assert "private deadline detail" not in timed_out.text
            assert peer.calls == ["held", "fast", "late"]
            await server.stop(None)
            unavailable = await client.get(
                f"{instances}/fast", headers=headers
            )
            assert unavailable.json()["data"]["status"] == "unavailable"
    finally:
        await server.stop(None)
