"""Verify the Panel, Outbox, worker and routing RPCs on isolated Xray."""

import ssl
from asyncio import create_subprocess_exec, sleep, timeout, wait_for
from contextlib import AsyncExitStack
from json import dumps
from os import environ
from pathlib import Path
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

from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)
from src.apps.network.nodes.registry.domain.dtos.records import NodeCreate
from src.apps.network.xray.routing.infra.broker.config import BrokerConfig
from src.bootstrap.events import create_events
from src.settings.config import CoreSettings, NatsConfig
from tests.integration.apps.network.nodes.credentials import enroll_nodes

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration


async def test_xray_live_routing(
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
    grpc_port, http_port, ca, source = node_process
    pool = "isolated / pool"
    source.write_text(
        dumps(
            {
                "outbounds": [
                    {"protocol": "freedom", "tag": "direct"},
                    {"protocol": "blackhole", "tag": "pool-a"},
                    {"protocol": "blackhole", "tag": "pool-b"},
                ],
                "routing": {
                    "balancers": [
                        {
                            "tag": pool,
                            "selector": ["pool-"],
                            "strategy": {"type": "roundRobin"},
                        },
                    ],
                    "rules": [
                        {
                            "type": "field",
                            "network": "tcp",
                            "ruleTag": "z-first",
                            "outboundTag": "direct",
                        },
                        {
                            "type": "field",
                            "network": "udp",
                            "balancerTag": pool,
                        },
                    ],
                },
            }
        )
    )
    tls = ssl.create_default_context()
    ca.configure_trust(tls)
    async with AsyncClient(
        verify=tls, headers={"X-API-Key": node_api_key}
    ) as node_client:
        started = await node_client.put(
            f"https://127.0.0.1:{http_port}/v1/xray/instances/edge/execution",
            timeout=10,
        )
        assert started.is_success, started.text
    headers = await admin_headers(
        app, client, mobile="09120000812", role_key="native-xray-routing"
    )
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        nodes = await scope.get(INodeService)
        node = await nodes.create(
            NodeCreate(
                name="Isolated routing", address="127.0.0.1", port=grpc_port
            )
        )
    await enroll_nodes(
        app,
        {
            node.id: (node_api_key, ca.cert_pem.bytes().decode()),
        },
    )
    pg.nats = NatsConfig(servers=[broker_url])
    base = f"/admin/nodes/{node.id}/xray/instances/edge/routing"

    async def tags() -> list[str]:
        reply = await client.get(f"{base}/rules", headers=headers)
        assert reply.status_code == 200, reply.text
        assert reply.headers["Cache-Control"] == "no-store"
        data = reply.json()["data"]
        assert data["status"] == "observed", data
        assert data["received_at"] is not None
        return [row["rule_tag"] for row in data["rules"]]

    async def assert_override(expected: str) -> None:
        reply = await client.get(
            f"{base}/balancer", params={"tag": pool}, headers=headers
        )
        assert reply.status_code == 200, reply.text
        result = reply.json()["data"]
        assert result["status"] == "observed", result
        assert result["balancer"]["override_target"] == expected

    async def mutate(
        method: str,
        path: str,
        *,
        json: dict[str, str | bool] | None = None,
        tag: str | None = None,
    ) -> int:
        reply = await client.request(
            method,
            f"{base}/{path}",
            json=json,
            params={"tag": tag} if tag is not None else None,
            headers={**headers, "Idempotency-Key": str(uuid4())},
        )
        assert reply.status_code == 202, reply.text
        operation_id = reply.json()["data"]["id"]
        async with timeout(8):
            while True:
                reply = await client.get(
                    f"{base}/operations/{operation_id}", headers=headers
                )
                assert reply.status_code == 200, reply.text
                operation = reply.json()["data"]
                if operation["state"] not in {"queued", "running"}:
                    break
                await sleep(0.05)
        assert operation["state"] == "acknowledged", operation
        return operation_id

    assert await tags() == ["z-first", ""]
    tested = await client.post(
        f"{base}/tests",
        headers=headers,
        json={
            "network": "tcp",
            "target_ip": "2001:db8::1",
            "target_port": 443,
        },
    )
    assert tested.status_code == 200, tested.text
    selected = tested.json()["data"]
    assert selected["status"] == "observed", selected
    assert selected["selection"]["outbound_tag"] == "direct"

    config = tmp_path / "routing-relay.yml"
    config.write_text(yaml.safe_dump(pg.model_dump(mode="json")))
    events = create_events(pg)
    async with AsyncExitStack() as stack:
        stack.push_async_callback(events.stop)
        await events.start()
        connection = await connect(broker_url)
        stack.push_async_callback(connection.close)
        relay = await create_subprocess_exec(
            str(Path(executable).with_name("faststream")),
            "run",
            "src.entrypoints.outbox:app",
            env={**environ, "PAPILIO_CONFIG": str(config)},
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
        appended = await mutate(
            "POST",
            "rules",
            json={
                "rule_json": dumps(
                    {
                        "type": "field",
                        "network": "tcp",
                        "ruleTag": "appended",
                        "outboundTag": "direct",
                    }
                )
            },
        )
        assert await tags() == ["z-first", "", "appended"]
        await mutate("DELETE", "rules", tag="appended")
        assert await tags() == ["z-first", ""]

        duplicate = await connection.jetstream().publish(
            BrokerConfig.requested, dumps({"operation_id": appended}).encode()
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
        assert await tags() == ["z-first", ""]

        await mutate(
            "PUT", "balancer-override", json={"target": "pool-b"}, tag=pool
        )
        await assert_override("pool-b")
        await mutate("DELETE", "balancer-override", tag=pool)
        await assert_override("")

        await mutate(
            "POST",
            "replacements",
            json={
                "rule_json": dumps(
                    {
                        "type": "field",
                        "network": "tcp",
                        "ruleTag": "replaced",
                        "outboundTag": "direct",
                    }
                ),
                "confirm_replace": True,
            },
        )
        assert await tags() == ["replaced"]
        balancer = await client.get(
            f"{base}/balancer", params={"tag": pool}, headers=headers
        )
        assert balancer.json()["data"]["status"] == "target_not_found"
