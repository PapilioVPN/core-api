"""Follow real Xray stdout and stderr through the Panel's HTTP stream."""

import ssl
from asyncio import (
    StreamReader,
    StreamWriter,
    create_task,
    sleep,
    start_server,
    timeout,
)
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from json import dumps, loads
from pathlib import Path
from socket import socket
from typing import cast

import pytest
import trustme
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, Response
from uvicorn import Config, Server

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.config import NodeHostConfig
from src.apps.network.nodes.domain.dtos.records import NodeCreate
from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration


@asynccontextmanager
async def _panel(app: FastAPI) -> AsyncIterator[AsyncClient]:
    with socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = Server(
            Config(
                app,
                lifespan="off",
                ws="none",
                log_config=None,
                access_log=False,
            )
        )
        task = create_task(server.serve(sockets=[listener]))
        try:
            async with timeout(5):
                while not server.started:
                    assert not task.done()
                    await sleep(0.01)
            async with AsyncClient(
                base_url=f"http://127.0.0.1:{port}", timeout=5
            ) as client:
                yield client
        finally:
            server.should_exit = True
            async with timeout(5):
                await task


async def _origin(reader: StreamReader, writer: StreamWriter) -> None:
    try:
        await reader.readuntil(b"\r\n\r\n")
        writer.write(b"HTTP/1.1 204 No Content\r\nConnection: close\r\n\r\n")
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def _events(
    reply: Response,
) -> AsyncIterator[tuple[str, dict[str, str | int | bool | None]]]:
    event = ""
    data = None
    async for line in reply.aiter_lines():
        if line.startswith("event: "):
            event = line[7:]
        elif line.startswith("data: "):
            data = loads(line[6:])
        elif not line and data is not None:
            yield event, data
            data = None


async def test_xray_live_logs(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    node_process: tuple[int, int, trustme.CA, Path],
    node_api_key: str,
) -> None:
    grpc_port, http_port, ca, source = node_process
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        nodes = await scope.get(INodeService)
        node = await nodes.create(
            NodeCreate(
                name="Isolated logs", address="127.0.0.1", port=grpc_port
            )
        )
    pg.node_host = NodeHostConfig.model_validate(
        {
            "targets": {
                node.id: {
                    "address": node.address,
                    "port": grpc_port,
                    "api_key": node_api_key,
                    "ca_pem": ca.cert_pem.bytes().decode(),
                }
            }
        }
    )
    headers = await admin_headers(
        app, client, mobile="09120000778", role_key="native-xray-logs"
    )
    path = f"/admin/nodes/{node.id}/xray/instances/edge/logs"
    not_running = await client.get(path, headers=headers)
    assert not_running.status_code == 200, not_running.text
    assert [event async for event in _events(not_running)] == [
        ("end", {"status": "not_running"})
    ]

    tls = ssl.create_default_context()
    ca.configure_trust(tls)
    native_path = f"https://127.0.0.1:{http_port}/v1/xray/instances/edge"
    origin = await start_server(_origin, "127.0.0.1", 0)
    async with (
        origin,
        _panel(app) as panel,
        AsyncClient(verify=tls, headers={"X-API-Key": node_api_key}) as native,
        AsyncExitStack() as peers,
    ):
        origin_port = origin.sockets[0].getsockname()[1]
        with socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            proxy_port = reserved.getsockname()[1]
        source.write_text(
            dumps(
                {
                    "log": {"error": "/dev/stderr", "loglevel": "info"},
                    "inbounds": [
                        {
                            "listen": "127.0.0.1",
                            "port": proxy_port,
                            "protocol": "http",
                            "tag": "proxy",
                        }
                    ],
                    "outbounds": [
                        {
                            "tag": "direct",
                            "protocol": "freedom",
                            "settings": {
                                "redirect": f"127.0.0.1:{origin_port}"
                            },
                        }
                    ],
                }
            )
        )
        started = await native.put(f"{native_path}/execution", timeout=10)
        assert started.is_success, started.text
        ready = ("ready", {"node_id": node.id, "instance_id": "edge"})
        async with panel.stream("GET", path, headers=headers) as surviving:
            assert surviving.status_code == 200
            assert surviving.headers["x-accel-buffering"] == "no"
            events = _events(surviving)
            assert await anext(events) == ready

            # Fill the Node's real 16-slot limit with 14 independent peers
            # plus two Panel streams. A saturated call has no ready event.
            for _ in range(14):
                peer = await peers.enter_async_context(
                    native.stream("GET", f"{native_path}/logs")
                )
                assert peer.status_code == 200
            async with panel.stream("GET", path, headers=headers) as closing:
                closing_events = _events(closing)
                assert await anext(closing_events) == ready
                async with native.stream("GET", f"{native_path}/logs") as full:
                    assert full.status_code == 429
                async with panel.stream("GET", path, headers=headers) as busy:
                    busy_events = _events(busy)
                    reports = [event async for event in busy_events]
                    assert reports == [("end", {"status": "busy"})]

            # Closing only the second Panel request must release one Node
            # slot without closing the channel borrowed by the first.
            async with timeout(5):
                while True:
                    async with panel.stream(
                        "GET", path, headers=headers
                    ) as reopened:
                        reopened_events = _events(reopened)
                        first = await anext(reopened_events)
                        if first == ready:
                            break
                        assert first == ("end", {"status": "busy"})
                    await sleep(0.02)

            async with AsyncClient(
                proxy=f"http://127.0.0.1:{proxy_port}", timeout=5
            ) as proxy:
                probe = await proxy.get("http://xray-live-log.invalid/")
            assert probe.status_code == 204, probe.text
            sources = set()
            sequences = []
            async with timeout(5):
                while sources != {"stdout", "stderr"}:
                    event, data = await anext(events)
                    assert event == "log", (event, data)
                    assert isinstance(data["execution"], str)
                    assert isinstance(data["sequence"], str)
                    assert isinstance(data["received_unix_nano"], str)
                    assert data["truncated"] is False
                    assert data["encoding_replaced"] is False
                    sequences.append(int(data["sequence"]))
                    if "xray-live-log.invalid" in str(data["message"]):
                        sources.add(data["source"])
            assert sorted(set(sequences)) == sequences
            stopped = await native.delete(f"{native_path}/execution")
            assert stopped.is_success, stopped.text
            async with timeout(5):
                tail = [event async for event in events]
            assert tail[-1] == ("end", {"status": "ended"})
