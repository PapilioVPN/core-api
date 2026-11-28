"""Check per-target evidence in a live Xray fleet snapshot."""

import ssl
from asyncio import create_task, timeout, wait_for
from pathlib import Path
from typing import cast

import grpc
import pytest
import trustme
from dishka import AsyncContainer
from fastapi import FastAPI
from grpc import aio
from httpx import ASGITransport, AsyncClient

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.config import NodeHostConfig
from src.apps.network.nodes.domain.dtos.records import NodeCreate
from src.apps.network.xray.instances.infra.grpc.v1.instances_pb2_grpc import (
    add_XrayInstancesServiceServicer_to_server,
)
from src.bootstrap.api import create_api
from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers
from .test_status import _KEY, StatusPeer

pytestmark = pytest.mark.integration
_URL = "/admin/nodes/xray/instances/status"


async def test_fleet_status_preserves_order_and_reports_local_absence(
    app: FastAPI, client: AsyncClient
) -> None:
    target = {"node_id": 9999999, "instance_id": "edge"}
    denied = await client.post(_URL, json={"targets": [target]})
    assert denied.status_code == 401, denied.text
    headers = await admin_headers(
        app, client, mobile="09120000772", role_key="xray-fleet-local"
    )

    async def register(name: str, enabled: bool) -> int:
        response = await client.post(
            "/admin/nodes",
            headers=headers,
            json={
                "name": name,
                "address": f"{name}.example.invalid",
                "port": 8081,
                "is_enabled": enabled,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]["id"]

    disabled = {
        "node_id": await register("fleet-disabled", False),
        "instance_id": "west",
    }
    unconfigured = {
        "node_id": await register("fleet-unconfigured", True),
        "instance_id": "east",
    }
    selected = [unconfigured, target, disabled, unconfigured]
    response = await client.post(
        _URL, headers=headers, json={"targets": selected}
    )
    assert response.status_code == 200, response.text
    assert "no-store" in response.headers["cache-control"]
    statuses = (
        "not_configured",
        "node_not_found",
        "disabled",
        "not_configured",
    )
    assert response.json()["data"] == [
        {**item, "status": status, "instance": None, "received_at": None}
        for item, status in zip(selected, statuses, strict=True)
    ]
    for invalid in (
        [],
        [target] * 17,
        [{**target, "instance_id": "INVALID"}],
        [{**target, "node_id": 1 << 63}],
        [{**target, "node_id": True}],
    ):
        response = await client.post(
            _URL, headers=headers, json={"targets": invalid}
        )
        assert response.status_code == 422, response.text


async def test_fleet_status_keeps_real_node_result_while_a_peer_times_out(
    pg: CoreSettings,
    node_process: tuple[int, int, trustme.CA, Path],
    node_api_key: str,
) -> None:
    assert pg.db is not None
    pg.db.pool_size = 1
    pg.db.max_overflow = 0
    app = create_api(pg)
    real_grpc, real_http, real_ca, _ = node_process
    tls = ssl.create_default_context()
    real_ca.configure_trust(tls)
    async with AsyncClient(
        verify=tls, headers={"X-API-Key": node_api_key}
    ) as native:
        started = await native.put(
            f"https://127.0.0.1:{real_http}/v1/xray/instances/edge/execution",
            timeout=10,
        )
        assert started.is_success, started.text

    ca = trustme.CA()
    cert = ca.issue_cert("127.0.0.1")
    peer = StatusPeer()
    server = aio.server()
    add_XrayInstancesServiceServicer_to_server(peer, server)
    peer_port = server.add_secure_port(
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
                app, client, mobile="09120000771", role_key="xray-live-fleet"
            )
            container = cast(AsyncContainer, app.state.dishka_container)
            async with container() as scope:
                nodes = await scope.get(INodeService)
                live = await nodes.create(
                    NodeCreate(
                        name="Xray native",
                        address="127.0.0.1",
                        port=real_grpc,
                    )
                )
                controlled = await nodes.create(
                    NodeCreate(
                        name="Xray delayed peer",
                        address="127.0.0.1",
                        port=peer_port,
                    )
                )
            pg.node_host = NodeHostConfig.model_validate(
                {
                    "targets": {
                        live.id: {
                            "address": live.address,
                            "port": real_grpc,
                            "ca_pem": real_ca.cert_pem.bytes().decode(),
                            "api_key": node_api_key,
                        },
                        controlled.id: {
                            "address": controlled.address,
                            "port": peer_port,
                            "ca_pem": ca.cert_pem.bytes().decode(),
                            "api_key": _KEY,
                        },
                    }
                }
            )
            order = [
                (live.id, "edge"),
                (controlled.id, "late"),
                (live.id, "missing"),
                (controlled.id, "held"),
                (live.id, "edge"),
                (controlled.id, "held"),
            ]
            task = create_task(
                client.post(
                    _URL,
                    headers=headers,
                    json={
                        "targets": [
                            {"node_id": id, "instance_id": instance}
                            for id, instance in order
                        ]
                    },
                )
            )
            try:
                await wait_for(peer.pending.wait(), 2)
                async with timeout(1.5):
                    record = await client.get(
                        f"/admin/nodes/{live.id}", headers=headers
                    )
                    assert record.status_code == 200, record.text
                    assert not task.done()
            finally:
                peer.release.set()
                reply = await wait_for(task, 4)
            assert reply.status_code == 200, reply.text
            assert "private deadline detail" not in reply.text
            data = reply.json()["data"]
            assert [
                (row["node_id"], row["instance_id"]) for row in data
            ] == order
            assert [row["status"] for row in data] == [
                "observed",
                "timeout",
                "instance_not_found",
                "observed",
                "observed",
                "observed",
            ]
            assert data[0]["instance"]["state"] == "ready"
            assert data[0]["received_at"] is not None
            assert data[1]["received_at"] is None
            assert data[0] == data[4]
            assert data[3] == data[5]
            assert sorted(peer.calls) == ["held", "late"]
            assert len(peer.peers) == 1
    finally:
        await server.stop(None)
