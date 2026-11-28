"""Verify ordered Xray comparisons against one bounded local selection."""

from asyncio import create_task, wait_for
from typing import Any, cast
from uuid import uuid4

import grpc
import pytest
import trustme
from dishka import AsyncContainer
from fastapi import FastAPI
from grpc import aio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.network.nodes.config import NodeHostConfig
from src.apps.network.xray.instances.app.interfaces.status import (
    IXrayStatusFanout,
)
from src.apps.network.xray.instances.app.services.status_fanout import (
    XrayStatusFanout,
)
from src.apps.network.xray.instances.infra.grpc.v1.instances_pb2 import (
    XrayInstanceRequest,
    XrayInstanceState,
    XrayInstanceStatus,
)
from src.apps.network.xray.instances.infra.grpc.v1.instances_pb2_grpc import (
    add_XrayInstancesServiceServicer_to_server,
)
from src.bootstrap.api import create_api
from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers
from ..instances.test_status import _KEY, StatusPeer
from .test_records import ASSIGNMENT_PATH

pytestmark = pytest.mark.integration
_URL = "/admin/nodes/xray/instances/desired-revision/comparison"


async def test_fleet_comparison_reports_each_missing_target(
    app: FastAPI, client: AsyncClient
) -> None:
    target = {"node_id": 9999999, "instance_id": "edge"}
    payload = {"targets": [target, target]}
    denied = await client.post(_URL, json=payload)
    assert denied.status_code == 401, denied.text
    headers = await admin_headers(
        app, client, mobile="09120000766", role_key="xray-fleet-comparison"
    )
    response = await client.post(_URL, headers=headers, json=payload)
    assert response.status_code == 200, response.text
    assert "no-store" in response.headers["Cache-Control"]
    assert (
        response.json()["data"]
        == [
            {
                **target,
                "state": "unknown",
                "desired": None,
                "observed": {
                    **target,
                    "status": "node_not_found",
                    "instance": None,
                    "received_at": None,
                },
            }
        ]
        * 2
    )
    for selection in (
        [],
        [target] * 17,
        [{**target, "node_id": True}],
        [{**target, "instance_id": "INVALID"}],
    ):
        invalid = await client.post(
            _URL, headers=headers, json={"targets": selection}
        )
        assert invalid.status_code == 422, invalid.text


@pytest.mark.parametrize(
    ("permission", "expected"),
    [(AdminPermission.READ, 200), (AdminPermission.CREATE, 403)],
)
async def test_fleet_comparison_requires_the_read_grant(
    app: FastAPI,
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    permission: AdminPermission,
    expected: int,
) -> None:
    async def identity() -> AdminIdentity:
        return AdminIdentity(1, 1, {"network": permission}, uuid4(), False)

    monkeypatch.setitem(app.dependency_overrides, current_admin, identity)
    response = await client.post(
        _URL, json={"targets": [{"node_id": 9999999, "instance_id": "edge"}]}
    )
    assert response.status_code == expected, response.text


class ComparisonPeer(StatusPeer):
    digest: str

    async def GetStatus(
        self,
        request: XrayInstanceRequest,
        context: aio.ServicerContext[XrayInstanceRequest, XrayInstanceStatus],
    ) -> XrayInstanceStatus:
        reply = await super().GetStatus(request, context)
        if request.id in ("matched", "held"):
            reply.applied_config_sha256 = self.digest
        elif request.id == "stopped":
            reply.state = XrayInstanceState.XRAY_INSTANCE_STATE_STOPPED
        if request.id in ("stopped", "digestless"):
            reply.ClearField("applied_config_sha256")
        return reply


async def test_fleet_comparison_limits_sql_and_preserves_live_outcomes(
    pg: CoreSettings,
) -> None:
    assert pg.db is not None
    pg.db.pool_size = 1
    pg.db.max_overflow = 0
    ca = trustme.CA()
    cert = ca.issue_cert("127.0.0.1")
    server = aio.server()
    peer = ComparisonPeer()
    add_XrayInstancesServiceServicer_to_server(peer, server)
    port = server.add_secure_port(
        "127.0.0.1:0",
        grpc.ssl_server_credentials(
            [(cert.private_key_pem.bytes(), cert.cert_chain_pems[0].bytes())],
        ),
    )
    app = create_api(pg)
    await server.start()
    try:
        async with (
            app.router.lifespan_context(app),
            AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client,
        ):
            headers = await admin_headers(
                app, client, mobile="09120000767", role_key="xray-live-compare"
            )
            container = cast(AsyncContainer, app.state.dishka_container)
            fanout = cast(
                XrayStatusFanout, await container.get(IXrayStatusFanout)
            )
            await _verify_comparison(
                client, headers, pg.node_host, ca, port, peer, fanout
            )
    finally:
        await server.stop(0)


async def _verify_comparison(
    client: AsyncClient,
    headers: dict[str, str],
    config: NodeHostConfig,
    ca: trustme.CA,
    port: int,
    peer: ComparisonPeer,
    fanout: XrayStatusFanout,
) -> None:
    live = await client.post(
        "/admin/nodes",
        headers=headers,
        json={"name": "Comparison live", "address": "127.0.0.1", "port": port},
    )
    disabled = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Comparison disabled",
            "address": "comparison-disabled.example.invalid",
            "port": 81,
            "is_enabled": False,
        },
    )
    assert live.status_code == disabled.status_code == 201
    live_id = live.json()["data"]["id"]
    disabled_id = disabled.json()["data"]["id"]
    configured = NodeHostConfig.model_validate(
        {
            "targets": {
                live_id: {
                    "address": "127.0.0.1",
                    "port": port,
                    "ca_pem": ca.cert_pem.bytes().decode(),
                    "api_key": _KEY,
                }
            }
        }
    )
    config.targets.update(configured.targets)
    created = await client.post(
        "/admin/xray/revisions",
        headers=headers,
        json={"config_json": '{"remarks":"fleet comparison"}'},
    )
    assert created.status_code == 201, created.text
    revision = created.json()["data"]
    peer.digest = revision["config_sha256"]
    assigned = (
        "matched",
        "different",
        "stopped",
        "digestless",
        "late",
        "held",
    )
    for id, instance in [
        *((live_id, key) for key in assigned),
        (disabled_id, "edge"),
    ]:
        path = ASSIGNMENT_PATH.format(node_id=id, instance_id=instance)
        reply = await client.put(
            path, headers=headers, json={"revision_id": revision["id"]}
        )
        assert reply.status_code == 200, reply.text

    pairs = [
        (live_id, "matched"),
        (9999999, "edge"),
        (live_id, "late"),
        (live_id, "unassigned"),
        (disabled_id, "edge"),
        (live_id, "different"),
        (live_id, "stopped"),
        (live_id, "digestless"),
        (live_id, "matched"),
    ]
    rows = await _check_sql_growth(client, headers, pairs)
    assert [(row["node_id"], row["instance_id"]) for row in rows] == pairs
    assert rows[0] == rows[-1]
    assert rows[0]["desired"]["config_sha256"] == revision["config_sha256"]
    assert rows[0]["observed"]["received_at"] is not None, rows[0]
    assert [row["state"] for row in rows] == [
        "matched",
        "unknown",
        "unknown",
        "unassigned",
        "unknown",
        "different",
        "stopped",
        "unknown",
        "matched",
    ]
    observed = [row["observed"] for row in rows]
    assert [row["status"] if row else None for row in observed] == [
        "observed",
        "node_not_found",
        "timeout",
        None,
        "disabled",
        "observed",
        "observed",
        "observed",
        "observed",
    ]
    assert sorted(peer.calls) == sorted([*assigned[:-1], "matched"])

    fanout.capacity.total_tokens = 1
    task = create_task(
        client.post(
            _URL,
            headers=headers,
            json={"targets": [{"node_id": live_id, "instance_id": "held"}]},
        )
    )
    try:
        await wait_for(peer.pending.wait(), 2)
        path = ASSIGNMENT_PATH.format(node_id=live_id, instance_id="held")
        stored = await wait_for(client.get(path, headers=headers), 1.5)
        assert stored.status_code == 200, stored.text
        assert not task.done()
        status = await client.post(
            "/admin/nodes/xray/instances/status",
            headers=headers,
            json={"targets": [{"node_id": live_id, "instance_id": "matched"}]},
        )
        assert status.status_code == 200, status.text
        assert status.json()["data"][0]["status"] == "busy"
    finally:
        peer.release.set()
        reply = await wait_for(task, 4)
    assert reply.json()["data"][0]["state"] == "matched"
    assert fanout.capacity.borrowed_tokens == 0


async def _check_sql_growth(
    client: AsyncClient, headers: dict[str, str], pairs: list[tuple[int, str]]
) -> list[dict[str, Any]]:
    captured: list[str] = []

    def capture_sql(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        sql = statement.strip().lower()
        if any(name in sql for name in ("tbl_nodes", "tbl_xray_")):
            captured.append(sql)

    event.listen(Engine, "before_cursor_execute", capture_sql)
    try:
        for selection in (pairs[:1], pairs):
            captured.clear()
            response = await client.post(
                _URL,
                headers=headers,
                json={
                    "targets": [
                        {"node_id": id, "instance_id": key}
                        for id, key in selection
                    ]
                },
            )
            assert response.status_code == 200, response.text
            assert "private deadline detail" not in response.text
            assert len(captured) == 2, captured
            assert all(
                sql.startswith("select") and " in (" in sql for sql in captured
            )
            assert "join tbl_xray_revisions" in captured[1]
    finally:
        event.remove(Engine, "before_cursor_execute", capture_sql)
    return response.json()["data"]
