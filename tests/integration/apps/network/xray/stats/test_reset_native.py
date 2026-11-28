"""Run the complete Panel, Outbox, worker and Node reset path."""

import ssl
from asyncio import (
    StreamReader,
    StreamWriter,
    create_subprocess_exec,
    sleep,
    start_server,
    timeout,
    wait_for,
)
from contextlib import AsyncExitStack
from json import dumps
from os import environ
from pathlib import Path
from socket import socket
from sys import executable
from typing import cast
from uuid import uuid4

import pytest
import trustme
import yaml
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from nats import connect

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.config import NodeHostConfig
from src.apps.network.nodes.domain.dtos.records import NodeCreate
from src.apps.network.xray.stats.infra.broker.config import BrokerConfig
from src.bootstrap.events import create_events
from src.settings.config import CoreSettings, NatsConfig

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration


@pytest.fixture
def node_xray_overrides() -> dict[str, bool]:
    return {"reset_engine_stats": True, "native_scope_reset": True}


async def _origin(reader: StreamReader, writer: StreamWriter) -> None:
    try:
        await reader.readuntil(b"\r\n\r\n")
        writer.write(
            b"HTTP/1.1 200 OK\r\nContent-Length: 7\r\n"
            b"Connection: close\r\n\r\ntraffic"
        )
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def test_xray_live_traffic_resets(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    tmp_path: Path,
    node_process: tuple[int, int, trustme.CA, Path],
    node_api_key: str,
) -> None:
    broker_url = environ.get("PAPILIOVPN_TEST_NATS_URL")
    if not broker_url:
        pytest.skip("Set PAPILIOVPN_TEST_NATS_URL to isolated JetStream")
    grpc_port, http_port, ca, config = node_process
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        nodes = await scope.get(INodeService)
        node = await nodes.create(
            NodeCreate(
                name="Isolated Xray counters",
                address="127.0.0.1",
                port=grpc_port,
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
    pg.nats = NatsConfig(servers=[broker_url])
    headers = await admin_headers(
        app, client, mobile="09120000774", role_key="native-traffic-reset"
    )
    base = f"/admin/nodes/{node.id}/xray/instances/edge/traffic"
    tls = ssl.create_default_context()
    ca.configure_trust(tls)
    origin = await start_server(_origin, "127.0.0.1", 0)
    origin_port = origin.sockets[0].getsockname()[1]
    with socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        proxy_port = reserved.getsockname()[1]
    config.write_text(
        dumps(
            {
                "stats": {},
                "policy": {
                    "system": {
                        "statsInboundUplink": True,
                        "statsInboundDownlink": True,
                        "statsOutboundUplink": True,
                        "statsOutboundDownlink": True,
                    }
                },
                "inbounds": [
                    {
                        "tag": "entry",
                        "listen": "127.0.0.1",
                        "port": proxy_port,
                        "protocol": "http",
                    }
                ],
                "outbounds": [{"tag": "direct", "protocol": "freedom"}],
            }
        )
    )
    async with AsyncClient(
        verify=tls, headers={"X-API-Key": node_api_key}
    ) as native:
        running = await native.put(
            f"https://127.0.0.1:{http_port}/v1/xray/instances/edge/execution",
            timeout=10,
        )
        assert running.is_success, running.text
    relay_config = tmp_path / "reset-relay.yml"
    relay_config.write_text(yaml.safe_dump(pg.model_dump(mode="json")))
    events = create_events(pg)

    async def counter() -> tuple[int, int]:
        reply = await client.get(
            f"{base}/outbound/counter",
            headers=headers,
            params={"name": "direct"},
        )
        assert reply.status_code == 200, reply.text
        data = reply.json()["data"]
        assert data["status"] == "observed", data
        return data["counter"]["uplink_bytes"], data["counter"][
            "downlink_bytes"
        ]

    async def reset(kind: str, data: dict[str, str | int | bool]) -> dict:
        result = await client.post(
            f"{base}/outbound/resets/{kind}",
            json=data,
            headers={**headers, "Idempotency-Key": str(uuid4())},
        )
        assert result.status_code == 202, result.text
        id = result.json()["data"]["id"]
        async with timeout(12):
            while True:
                result = await client.get(
                    f"{base}/resets/{id}", headers=headers
                )
                assert result.status_code == 200, result.text
                operation = result.json()["data"]
                if operation["state"] not in {"queued", "running"}:
                    break
                await sleep(0.05)
        return operation

    async with origin, AsyncExitStack() as stack:
        stack.push_async_callback(events.stop)
        await events.start()
        connection = await connect(broker_url)
        stack.push_async_callback(connection.close)
        relay = await create_subprocess_exec(
            str(Path(executable).with_name("faststream")),
            "run",
            "src.entrypoints.outbox:app",
            env={**environ, "PAPILIO_CONFIG": str(relay_config)},
        )

        async def stop_relay() -> None:
            if relay.returncode is None:
                relay.terminate()
                try:
                    await wait_for(relay.wait(), timeout=5)
                except TimeoutError:
                    relay.kill()
                    await relay.wait()

        stack.push_async_callback(stop_relay)
        async with AsyncClient(
            proxy=f"http://127.0.0.1:{proxy_port}"
        ) as proxy:
            probe = await proxy.get(f"http://127.0.0.1:{origin_port}/")
            assert probe.text == "traffic"
            before_up, before_down = await counter()
            assert before_up > 0 and before_down > 0

            rejected = await reset(
                "scope", {"max_counters": 1, "confirm": True}
            )
            assert rejected["state"] == "not_applied", rejected
            assert rejected["reason"] == "resource_limit"
            assert (await counter()) == (before_up, before_down)

            single = await reset(
                "counter", {"name": "direct", "direction": "uplink"}
            )
            assert single["state"] == "complete", single
            assert single["counters"] == [
                {
                    "name": "direct",
                    "direction": "uplink",
                    "effect": "acknowledged",
                    "previous_bytes": str(before_up),
                }
            ]
            assert (await counter()) == (0, before_down)
            pair = await reset("pair", {"name": "direct"})
            assert pair["state"] == "complete", pair
            assert [row["previous_bytes"] for row in pair["counters"]] == [
                "0",
                str(before_down),
            ]
            assert (await counter()) == (0, 0)

            probe = await proxy.get(f"http://127.0.0.1:{origin_port}/")
            assert probe.text == "traffic"
            seeded = await counter()
            duplicate = await connection.jetstream().publish(
                BrokerConfig.requested,
                dumps({"operation_id": pair["id"]}).encode(),
            )
            async with timeout(5):
                while True:
                    info = await connection.jetstream().consumer_info(
                        duplicate.stream, BrokerConfig.durable
                    )
                    if (
                        info.ack_floor is not None
                        and info.ack_floor.stream_seq >= duplicate.seq
                    ):
                        break
                    await sleep(0.05)
            assert (await counter()) == seeded
            report = await reset("scope", {"max_counters": 2, "confirm": True})
            assert report["state"] == "complete", report
            assert {
                row["direction"]: int(row["previous_bytes"])
                for row in report["counters"]
            } == dict(zip(("uplink", "downlink"), seeded, strict=True))
            assert (await counter()) == (0, 0)
