"""Exercise authorized SSE admission through the actual Panel routes."""

from asyncio import Event, sleep, timeout
from collections.abc import AsyncIterator
from typing import cast

import grpc
import pytest
import trustme
from dishka import AsyncContainer
from fastapi import FastAPI
from google.protobuf.timestamp_pb2 import Timestamp
from grpc import aio
from httpx import AsyncClient

from src.apps.network.hysteria.logs.infra.grpc.v1 import (
    hysteria_logs_pb2 as hysteria,
)
from src.apps.network.hysteria.logs.infra.grpc.v1 import (
    hysteria_logs_pb2_grpc as hysteria_grpc,
)
from src.apps.network.nodes.connections.infra.grpc import streams
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)
from src.apps.network.nodes.registry.domain.dtos.records import NodeCreate
from src.apps.network.openvpn.instances.infra.grpc.v1 import (
    openvpn_instances_pb2 as openvpn,
)
from src.apps.network.openvpn.instances.infra.grpc.v1 import (
    openvpn_instances_pb2_grpc as openvpn_grpc,
)
from src.apps.network.wireguard.diagnostics.infra.grpc.v1 import (
    wireguard_diagnostics_pb2 as wireguard,
)
from src.apps.network.wireguard.diagnostics.infra.grpc.v1 import (
    wireguard_diagnostics_pb2_grpc as wireguard_grpc,
)

from .nodes.auth import admin_headers
from .nodes.credentials import enroll_nodes
from .sse import events as _events
from .sse import panel as _panel

pytestmark = pytest.mark.integration
_WIDE = 9007199254740993
_KEY = "isolated-engine-logs-test"


async def test_engine_log_feeds_respect_registry_and_permissions(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000657", role_key="engine-log-registry"
    )
    node = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Engine log fixture",
            "address": "engine-log-fixture.example.invalid",
            "port": 8443,
        },
    )
    assert node.status_code == 201, node.text
    base = f"/admin/nodes/{node.json()['data']['id']}"
    paths = [
        f"{base}/{target}/logs"
        for target in (
            "wireguard/interfaces/wg-test",
            "openvpn/instances/edge",
            "hysteria/instances/edge",
        )
    ]
    for path in paths:
        assert (await client.get(path)).status_code == 401
        reply = await client.get(path, headers=headers)
        assert reply.status_code == 200, reply.text
        assert "private" in reply.headers["cache-control"]
        assert "no-store" in reply.headers["cache-control"]
        assert "event: end" in reply.text
        assert "not_configured" in reply.text
    disabled = await client.patch(
        base, headers=headers, json={"is_enabled": False}
    )
    assert disabled.status_code == 200, disabled.text
    for path in paths:
        reply = await client.get(path, headers=headers)
        assert reply.status_code == 200, reply.text
        assert "disabled" in reply.text
    invalid = await client.get(
        paths[1], params={"after_sequence": "1"}, headers=headers
    )
    assert invalid.status_code == 422, invalid.text


class WireGuardLogs(wireguard_grpc.WireGuardDiagnosticsServiceServicer):
    def __init__(self) -> None:
        self.closed = Event()

    async def GetLogs(
        self,
        request: wireguard.WireGuardDiagnosticsRequest,
        context: aio.ServicerContext[
            wireguard.WireGuardDiagnosticsRequest, wireguard.WireGuardLogEvent
        ],
    ) -> AsyncIterator[wireguard.WireGuardLogEvent]:
        assert request.name == "wg-test"
        assert ("x-api-key", _KEY) in (context.invocation_metadata() or ())
        await context.send_initial_metadata(())
        try:
            yield wireguard.WireGuardLogEvent(
                sequence=_WIDE,
                at=Timestamp(seconds=1_760_010_020, nanos=3),
                kind="peers_applied",
            )
            await Event().wait()
        finally:
            self.closed.set()


class HysteriaLogs(hysteria_grpc.HysteriaLogsServiceServicer):
    async def GetLogs(
        self,
        request: hysteria.HysteriaLogsRequest,
        context: aio.ServicerContext[
            hysteria.HysteriaLogsRequest, hysteria.HysteriaLogEvent
        ],
    ) -> AsyncIterator[hysteria.HysteriaLogEvent]:
        assert ("x-api-key", _KEY) in (context.invocation_metadata() or ())
        await context.send_initial_metadata(())
        if request.id == "incomplete":
            yield hysteria.HysteriaLogEvent()
        else:
            assert request.id == "edge"
            yield hysteria.HysteriaLogEvent(
                execution=_WIDE,
                sequence=7,
                received_unix_nano=1_760_010_020_000_000_007,
                event="client_connected",
            )


class OpenVPNLogs(openvpn_grpc.OpenVPNOperationsServiceServicer):
    def __init__(self) -> None:
        self.publish = Event()

    async def GetLogs(
        self,
        request: openvpn.OpenVPNLogsRequest,
        context: aio.ServicerContext[
            openvpn.OpenVPNLogsRequest, openvpn.OpenVPNLogBatch
        ],
    ) -> AsyncIterator[openvpn.OpenVPNLogBatch]:
        assert ("x-api-key", _KEY) in (context.invocation_metadata() or ())
        assert request.id == "edge"
        assert request.execution_id == "test-execution"
        assert request.after_sequence == _WIDE
        await self.publish.wait()
        yield openvpn.OpenVPNLogBatch(
            execution_id=request.execution_id,
            dropped=_WIDE,
            entries=[
                openvpn.OpenVPNLog(
                    sequence=2 * _WIDE + 1,
                    timestamp=1_760_010_020,
                    level="I",
                    message="OpenVPN test fixture",
                ),
            ],
        )


async def test_native_engine_log_payloads_and_stream_cleanup(
    app: FastAPI, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(streams, "_MAX_STREAMS", 1)
    ca = trustme.CA()
    cert = ca.issue_cert("127.0.0.1")
    credentials = grpc.ssl_server_credentials(
        [(cert.private_key_pem.bytes(), cert.cert_chain_pems[0].bytes())]
    )
    server = aio.server()
    wireguard_logs = WireGuardLogs()
    openvpn_logs = OpenVPNLogs()
    wireguard_grpc.add_WireGuardDiagnosticsServiceServicer_to_server(
        wireguard_logs, server
    )
    hysteria_grpc.add_HysteriaLogsServiceServicer_to_server(
        HysteriaLogs(), server
    )
    openvpn_grpc.add_OpenVPNOperationsServiceServicer_to_server(
        openvpn_logs, server
    )
    port = server.add_secure_port("127.0.0.1:0", credentials)
    await server.start()
    try:
        container = cast(AsyncContainer, app.state.dishka_container)
        async with container() as scope:
            nodes = await scope.get(INodeService)
            node = await nodes.create(
                NodeCreate(
                    name="Native logs fixture", address="127.0.0.1", port=port
                )
            )
        await enroll_nodes(
            app, {node.id: (_KEY, ca.cert_pem.bytes().decode())}
        )
        headers = await admin_headers(
            app, client, mobile="09120000658", role_key="native-engine-logs"
        )
        base = f"/admin/nodes/{node.id}"
        async with _panel(app) as panel:
            async with panel.stream(
                "GET",
                f"{base}/wireguard/interfaces/wg-test/logs",
                headers=headers,
            ) as reply:
                assert reply.status_code == 200
                events = _events(reply)
                assert await anext(events) == (
                    "ready",
                    {"node_id": node.id, "name": "wg-test"},
                )
                assert await anext(events) == (
                    "log",
                    {
                        "sequence": str(_WIDE),
                        "observed_at_unix_nanoseconds": "1760010020000000003",
                        "kind": "peers_applied",
                    },
                )
                assert not wireguard_logs.closed.is_set()
                busy = await client.get(
                    f"{base}/openvpn/instances/edge/logs", headers=headers
                )
                assert [event async for event in _events(busy)] == [
                    ("end", {"status": "busy"})
                ]

            async with timeout(5):
                await wireguard_logs.closed.wait()

            reply = await panel.get(
                f"{base}/hysteria/instances/edge/logs", headers=headers
            )
            assert [event async for event in _events(reply)] == [
                ("ready", {"node_id": node.id, "instance_id": "edge"}),
                (
                    "log",
                    {
                        "execution": str(_WIDE),
                        "sequence": "7",
                        "received_unix_nano": "1760010020000000007",
                        "event": "client_connected",
                    },
                ),
                ("end", {"status": "ended"}),
            ]
            reply = await panel.get(
                f"{base}/hysteria/instances/incomplete/logs", headers=headers
            )
            assert [event async for event in _events(reply)] == [
                ("ready", {"node_id": node.id, "instance_id": "incomplete"}),
                ("end", {"status": "interrupted"}),
            ]

            monkeypatch.setattr(streams, "_OPEN_TIMEOUT", 0.02)
            async with panel.stream(
                "GET",
                f"{base}/openvpn/instances/edge/logs",
                params={
                    "execution_id": "test-execution",
                    "after_sequence": str(_WIDE),
                },
                headers=headers,
            ) as reply:
                assert reply.status_code == 200
                await sleep(0.04)
                openvpn_logs.publish.set()
                assert [event async for event in _events(reply)] == [
                    ("ready", {"node_id": node.id, "instance_id": "edge"}),
                    (
                        "log",
                        {
                            "execution_id": "test-execution",
                            "dropped": str(_WIDE),
                            "entries": [
                                {
                                    "sequence": str(2 * _WIDE + 1),
                                    "timestamp_unix_seconds": "1760010020",
                                    "level": "I",
                                    "message": "OpenVPN test fixture",
                                }
                            ],
                        },
                    ),
                    ("end", {"status": "ended"}),
                ]
    finally:
        await server.stop(0)
