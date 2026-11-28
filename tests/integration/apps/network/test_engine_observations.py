"""Expose typed status and validation for the other Node engines."""

from asyncio import create_subprocess_exec, timeout, wait_for
from asyncio.subprocess import PIPE
from base64 import b64encode
from collections.abc import AsyncIterator
from json import dumps, loads
from os import environ
from pathlib import Path
from shutil import which
from typing import cast

import grpc
import pytest
import trustme
import yaml
from dishka import AsyncContainer
from fastapi import FastAPI
from google.protobuf.timestamp_pb2 import Timestamp
from grpc import aio
from httpx import AsyncClient

from src.apps.network.hysteria.stats.infra.grpc.v1 import (
    hysteria_stats_pb2 as hysteria_pb2,
)
from src.apps.network.hysteria.stats.infra.grpc.v1 import (
    hysteria_stats_pb2_grpc as hysteria_pb2_grpc,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)
from src.apps.network.nodes.registry.domain.dtos.records import NodeCreate
from src.apps.network.openvpn.instances.infra.grpc.v1 import (
    openvpn_instances_pb2 as openvpn_pb2,
)
from src.apps.network.openvpn.instances.infra.grpc.v1 import (
    openvpn_instances_pb2_grpc as openvpn_pb2_grpc,
)
from src.apps.network.wireguard.diagnostics.infra.grpc.v1 import (
    wireguard_diagnostics_pb2 as wireguard_pb2,
)
from src.apps.network.wireguard.diagnostics.infra.grpc.v1 import (
    wireguard_diagnostics_pb2_grpc as wireguard_pb2_grpc,
)
from src.settings.config import CoreSettings
from tests.integration.apps.network.nodes.credentials import enroll_nodes

from .nodes.auth import admin_headers

pytestmark = pytest.mark.integration
_NODE_KEY = "isolated-engine-observations-key"
_HYSTERIA_SOURCE = (
    'listen: ":443"\n'
    "tls: {cert: tls.crt, key: tls.key}\n"
    "auth: {type: password, password: isolated-test}\n"
    'trafficStats: {listen: "127.0.0.1:9900", secret: isolated-stats}\n'
)


@pytest.mark.parametrize(
    ("resource", "field"),
    [
        ("wireguard/interfaces/wg-test", "config_json"),
        ("openvpn/instances/edge", "config_text"),
        ("hysteria/instances/edge", "config_yaml"),
    ],
)
async def test_engine_uses_configured_node_only(
    app: FastAPI, client: AsyncClient, resource: str, field: str
) -> None:
    engine = resource.split("/")[0]
    suffix = {"wireguard": "1", "openvpn": "2", "hysteria": "3"}[engine]
    headers = await admin_headers(
        app, client, mobile=f"0912000080{suffix}", role_key=f"{engine}-observe"
    )
    created = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": f"Unconfigured {engine}",
            "address": f"{engine}-test.example.invalid",
            "port": 8081,
        },
    )
    assert created.status_code == 201, created.text
    node_id = created.json()["data"]["id"]
    base = f"/admin/nodes/{node_id}/{resource}"
    response = await client.get(base, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "not_configured"
    observation = "sessions/count" if engine == "openvpn" else "runtime-stats"
    observed = await client.get(f"{base}/{observation}", headers=headers)
    assert observed.status_code == 200, observed.text
    assert observed.json()["data"]["status"] == "not_configured"
    assert observed.headers["Cache-Control"] == "private, no-store"
    assert (await client.get(f"{base}/{observation}")).status_code == 401

    url = f"{base}/config-validations"
    no_source = await client.post(url, headers=headers, json={})
    assert no_source.status_code == 422, no_source.text
    proposed = "private test source"
    response = await client.post(url, headers=headers, json={field: proposed})
    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "not_configured"
    assert proposed not in response.text
    assert (await client.get(base)).status_code == 401

    disabled = await client.patch(
        f"/admin/nodes/{node_id}", headers=headers, json={"is_enabled": False}
    )
    assert disabled.status_code == 200, disabled.text
    response = await client.get(base, headers=headers)
    assert response.json()["data"]["status"] == "disabled"
    observed = await client.get(f"{base}/{observation}", headers=headers)
    assert observed.json()["data"]["status"] == "disabled"
    response = await client.post(url, headers=headers, json={field: proposed})
    assert response.json()["data"]["status"] == "disabled"


@pytest.fixture
async def native_node(tmp_path: Path) -> AsyncIterator[tuple[int, trustme.CA]]:
    binary = environ.get("PAPILIOVPN_TEST_NODE_BIN")
    openvpn = which("openvpn")
    if not binary or openvpn is None:
        pytest.skip("Provide an isolated Node executable and OpenVPN binary")
    ca = trustme.CA()
    cert = ca.issue_cert("127.0.0.1")
    cert.private_key_pem.write_to_path(tmp_path / "tls.key")
    cert.cert_chain_pems[0].write_to_path(tmp_path / "tls.crt")
    (tmp_path / "openvpn.conf").write_text("proto udp\n")
    (tmp_path / "hysteria.yml").write_text(_HYSTERIA_SOURCE)
    config = {
        "management": {
            "http_address": "127.0.0.1:0",
            "grpc_address": "127.0.0.1:0",
            "api_key": _NODE_KEY,
            "tls": {"cert_file": "tls.crt", "key_file": "tls.key"},
        },
        "wireguard": {"interface": "wg-core-fixture"},
        "openvpn": {
            "id": "edge",
            "executable": openvpn,
            "config_file": "openvpn.conf",
        },
        "hysteria": {
            "instances": [
                {
                    "id": "edge",
                    "executable": "/bin/false",
                    "config_file": "hysteria.yml",
                    "runtime_directory": ".",
                }
            ]
        },
    }
    (tmp_path / "node.yml").write_text(yaml.safe_dump(config))
    process = await create_subprocess_exec(
        str(Path(binary).resolve()),
        "-config",
        "node.yml",
        cwd=tmp_path,
        stderr=PIPE,
    )
    try:
        assert process.stderr is not None
        async with timeout(10):
            while line := await process.stderr.readline():
                event = loads(line)
                if event.get("msg") == "management listeners ready":
                    break
            else:
                pytest.fail(
                    "Node exited before its management listeners bound"
                )
        yield event["grpc"]["Port"], ca
    finally:
        if process.returncode is None:
            process.terminate()
            try:
                await wait_for(process.communicate(), timeout=5)
            except TimeoutError:
                process.kill()
                await process.communicate()


async def test_engine_observations_over_real_node(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    native_node: tuple[int, trustme.CA],
) -> None:
    port, ca = native_node
    headers = await admin_headers(
        app,
        client,
        mobile="09120000804",
        role_key="native-engine-observations",
    )
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        nodes = await scope.get(INodeService)
        node = await nodes.create(
            NodeCreate(name="Isolated engines", address="127.0.0.1", port=port)
        )
    await enroll_nodes(
        app,
        {
            node.id: (_NODE_KEY, ca.cert_pem.bytes().decode()),
        },
    )
    base = f"/admin/nodes/{node.id}"
    for engine in ("openvpn", "hysteria"):
        reply = await client.get(
            f"{base}/{engine}/instances/edge", headers=headers
        )
        assert reply.status_code == 200, reply.text
        data = reply.json()["data"]
        assert data["status"] == "observed", data
        assert data["instance"]["state"] == "stopped"
        assert data["instance"]["applied_config_sha256"] is None
        assert data["received_at"] is not None

    wireguard = f"{base}/wireguard/interfaces/wg-core-fixture"
    reply = await client.get(wireguard, headers=headers)
    assert reply.json()["data"]["status"] == "target_not_found"
    for path, expected in (
        (f"{wireguard}/runtime-stats", "unavailable"),
        (f"{wireguard}/egress-probe", "unavailable"),
        (
            f"{base}/openvpn/instances/edge/sessions/count",
            "precondition_failed",
        ),
        (
            f"{base}/hysteria/instances/edge/runtime-stats",
            "precondition_failed",
        ),
    ):
        reply = await client.get(path, headers=headers)
        assert reply.status_code == 200, reply.text
        assert reply.json()["data"]["status"] == expected, reply.text
    key = b64encode(bytes(range(1, 33))).decode()
    wireguard_source = dumps(
        {"private_key": key, "addresses": ["192.0.2.8/32"]}
    )
    for resource, body, rejected, issue in (
        (
            wireguard,
            {"config_json": wireguard_source},
            {"config_json": "{"},
            "invalid_json",
        ),
        (
            f"{base}/openvpn/instances/edge",
            {"config_text": "proto udp\n"},
            {"config_text": "unsupported-test-directive\n"},
            "unsupported_directive",
        ),
        (
            f"{base}/hysteria/instances/edge",
            {"config_yaml": _HYSTERIA_SOURCE},
            {"config_yaml": "["},
            "invalid_yaml",
        ),
    ):
        url = f"{resource}/config-validations"
        reply = await client.post(url, headers=headers, json=body)
        assert reply.status_code == 200, reply.text
        data = reply.json()["data"]
        assert data["status"] == "observed", data
        assert data["validation"]["valid"] is True
        if "/hysteria/" in resource:
            assert data["validation"]["scope"] == "node_preflight"
        reply = await client.post(url, headers=headers, json=rejected)
        assert reply.status_code == 200, reply.text
        data = reply.json()["data"]
        assert data["status"] == "observed", data
        assert data["validation"]["valid"] is False
        assert data["validation"]["issue"] == issue


class RuntimeWireGuard(wireguard_pb2_grpc.WireGuardDiagnosticsServiceServicer):
    async def GetRuntimeStats(
        self,
        request: wireguard_pb2.WireGuardDiagnosticsRequest,
        context: aio.ServicerContext[
            wireguard_pb2.WireGuardDiagnosticsRequest,
            wireguard_pb2.WireGuardRuntimeStats,
        ],
    ) -> wireguard_pb2.WireGuardRuntimeStats:
        if request.name not in {"wg-reported", "wg-absent"}:
            await context.abort(grpc.StatusCode.NOT_FOUND)
        reply = wireguard_pb2.WireGuardRuntimeStats(heap_bytes=(1 << 64) - 1)
        if request.name == "wg-reported":
            reply.uptime_seconds = 0
        return reply

    async def ProbeEgress(
        self,
        request: wireguard_pb2.WireGuardDiagnosticsRequest,
        context: aio.ServicerContext[
            wireguard_pb2.WireGuardDiagnosticsRequest,
            wireguard_pb2.WireGuardEgressProbe,
        ],
    ) -> wireguard_pb2.WireGuardEgressProbe:
        if request.name not in {"wg-reported", "wg-absent"}:
            await context.abort(grpc.StatusCode.NOT_FOUND)
        reachable = request.name == "wg-reported"
        return wireguard_pb2.WireGuardEgressProbe(
            reachable=reachable,
            http_status=503 if reachable else 0,
            elapsed_nanoseconds=10,
            observed_at=Timestamp(seconds=1_760_010_020, nanos=3),
        )


class RuntimeHysteria(hysteria_pb2_grpc.HysteriaStatsServiceServicer):
    async def GetRuntimeStats(
        self,
        request: hysteria_pb2.HysteriaStatsRequest,
        context: aio.ServicerContext[
            hysteria_pb2.HysteriaStatsRequest,
            hysteria_pb2.HysteriaRuntimeStats,
        ],
    ) -> hysteria_pb2.HysteriaRuntimeStats:
        if request.id == "incomplete":
            return hysteria_pb2.HysteriaRuntimeStats()
        if request.id != "edge":
            await context.abort(grpc.StatusCode.NOT_FOUND)
        return hysteria_pb2.HysteriaRuntimeStats(
            execution=7,
            ready_since_unix_nano=1_760_010_020_000_000_003,
            uptime_seconds=0,
        )


class RuntimeOpenVPN(openvpn_pb2_grpc.OpenVPNOperationsServiceServicer):
    async def ListSessions(
        self,
        request: openvpn_pb2.OpenVPNInstanceRequest,
        context: aio.ServicerContext[
            openvpn_pb2.OpenVPNInstanceRequest,
            openvpn_pb2.OpenVPNSessionReport,
        ],
    ) -> openvpn_pb2.OpenVPNSessionReport:
        if request.id not in {"edge", "empty"}:
            await context.abort(grpc.StatusCode.NOT_FOUND)
        sessions = (
            [
                openvpn_pb2.OpenVPNSession(
                    id=1,
                    common_name="private-subscriber",
                    remote_address="198.51.100.31:5000",
                ),
            ]
            if request.id == "edge"
            else []
        )
        return openvpn_pb2.OpenVPNSessionReport(
            execution_id="run-5", observed_at=1_760_010_020, sessions=sessions
        )


async def test_runtime_observations_preserve_presence_and_scope(
    app: FastAPI, client: AsyncClient
) -> None:
    ca = trustme.CA()
    cert = ca.issue_cert("127.0.0.1")
    server = aio.server()
    wireguard_pb2_grpc.add_WireGuardDiagnosticsServiceServicer_to_server(
        RuntimeWireGuard(), server
    )
    hysteria_pb2_grpc.add_HysteriaStatsServiceServicer_to_server(
        RuntimeHysteria(), server
    )
    openvpn_pb2_grpc.add_OpenVPNOperationsServiceServicer_to_server(
        RuntimeOpenVPN(), server
    )
    port = server.add_secure_port(
        "127.0.0.1:0",
        grpc.ssl_server_credentials(
            [(cert.private_key_pem.bytes(), cert.cert_chain_pems[0].bytes())]
        ),
    )
    await server.start()
    try:
        headers = await admin_headers(
            app, client, mobile="09120000805", role_key="runtime-observations"
        )
        created = await client.post(
            "/admin/nodes",
            headers=headers,
            json={
                "name": "Runtime fixture",
                "address": "127.0.0.1",
                "port": port,
                "api_key": _NODE_KEY,
                "ca_pem": ca.cert_pem.bytes().decode(),
            },
        )
        assert created.status_code == 201, created.text
        base = f"/admin/nodes/{created.json()['data']['id']}"

        async def observe(relative_path: str) -> dict:
            reply = await client.get(
                f"{base}/{relative_path}", headers=headers
            )
            assert reply.status_code == 200, reply.text
            assert reply.headers["Cache-Control"] == "private, no-store"
            return reply.json()["data"]

        for name, uptime in (("wg-reported", "0"), ("wg-absent", None)):
            observed = await observe(
                f"wireguard/interfaces/{name}/runtime-stats"
            )
            assert observed["name"] == name
            assert observed["status"] == "observed"
            assert observed["received_at"]
            assert observed["runtime"]["heap_bytes"] == str((1 << 64) - 1)
            assert observed["runtime"]["uptime_seconds"] == uptime
            probe = await observe(f"wireguard/interfaces/{name}/egress-probe")
            reachable = name == "wg-reported"
            assert probe["status"] == "observed"
            assert probe["egress"] == {
                "reachable": reachable,
                "http_status": 503 if reachable else None,
                "elapsed_nanoseconds": "10",
                "observed_at_unix_nanoseconds": "1760010020000000003",
            }
        observed = await observe("hysteria/instances/edge/runtime-stats")
        assert observed["status"] == "observed"
        assert observed["runtime"] == {
            "execution": "7",
            "ready_since_unix_nanoseconds": "1760010020000000003",
            "uptime_seconds": "0",
        }
        observed = await observe("hysteria/instances/incomplete/runtime-stats")
        assert observed["status"] == "failed"
        assert observed["runtime"] is None
        for id, count in (("edge", 1), ("empty", 0)):
            observed = await observe(f"openvpn/instances/{id}/sessions/count")
            assert observed["status"] == "observed"
            assert observed["sessions"] == {
                "execution_id": "run-5",
                "observed_at_unix_seconds": "1760010020",
                "session_count": count,
            }
    finally:
        await server.stop(None)
