"""Authorize and track the first Xray execution on a registered Node."""

from asyncio import create_subprocess_exec, gather, sleep, timeout, wait_for
from contextlib import AsyncExitStack
from hashlib import sha256
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
from httpx import AsyncClient, Response
from nats import connect

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.config import NodeHostConfig
from src.apps.network.nodes.domain.dtos.records import NodeCreate
from src.apps.network.xray.instances.infra.broker.config import BrokerConfig
from src.bootstrap.events import create_events
from src.settings.config import CoreSettings, NatsConfig

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration


async def test_start_is_queued_once(app: FastAPI, client: AsyncClient) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000923", role_key="xray-start-queue"
    )
    created = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Xray start queue",
            "address": "xray-start.example.invalid",
            "port": 8081,
        },
    )
    assert created.status_code == 201, created.text
    node_id = created.json()["data"]["id"]
    path = f"/admin/nodes/{node_id}/xray/instances/edge/start-operations"
    key = str(uuid4())
    run_headers = {**headers, "Idempotency-Key": key}
    assert (await client.post(path, headers=headers)).status_code == 422
    first, repeated = await gather(
        client.post(path, headers=run_headers),
        client.post(path, headers=run_headers),
    )
    assert first.status_code == repeated.status_code == 202, first.text
    result = first.json()["data"]
    assert repeated.json()["data"] == result
    assert result["state"] == "queued"
    assert result["applied_config_sha256"] is None
    running_url = f"{path}/{result['id']}"
    other = await client.post(
        path, headers={**headers, "Idempotency-Key": str(uuid4())}
    )
    assert other.status_code == 409, other.text
    assert (await client.get(running_url, headers=headers)).json()["data"] == (
        result
    )
    assert (
        await client.get(
            running_url.replace("/edge/", "/other/"), headers=headers
        )
    ).status_code == 404


async def test_start_and_apply_execute_the_selected_source(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    tmp_path: Path,
    node_process: tuple[int, int, trustme.CA, Path],
    node_api_key: str,
) -> None:
    url = environ.get("PAPILIOVPN_TEST_NATS_URL")
    if not url:
        pytest.skip("Set PAPILIOVPN_TEST_NATS_URL to isolated JetStream")
    grpc_port, _, ca, source = node_process
    expected_digest = sha256(source.read_bytes()).hexdigest()
    headers = await admin_headers(
        app, client, mobile="09120000924", role_key="xray-start-native"
    )
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        nodes = await scope.get(INodeService)
        row = await nodes.create(
            NodeCreate(
                name="Isolated Xray start", address="127.0.0.1", port=grpc_port
            )
        )
    node_id = row.id
    instance_url = f"/admin/nodes/{node_id}/xray/instances/edge"
    start_url = f"{instance_url}/start-operations"
    pg.node_host = NodeHostConfig.model_validate(
        {
            "targets": {
                node_id: {
                    "address": "127.0.0.1",
                    "port": grpc_port,
                    "api_key": node_api_key,
                    "ca_pem": ca.cert_pem.bytes().decode(),
                }
            }
        }
    )
    pg.nats = NatsConfig(servers=[url])
    events = create_events(pg)
    relay_config = tmp_path / "relay.yml"
    relay_config.write_text(yaml.safe_dump(pg.model_dump(mode="json")))
    run_headers = {**headers, "Idempotency-Key": str(uuid4())}
    accepted = await client.post(start_url, headers=run_headers)
    assert accepted.status_code == 202, accepted.text
    result = accepted.json()["data"]
    operation_id = result["id"]
    operation_url = f"{start_url}/{operation_id}"
    assert result["state"] == "queued"

    async def wait_for_completion(path: str) -> Response:
        async with timeout(15):
            reply = await client.get(path, headers=headers)
            assert reply.status_code == 200, reply.text
            while reply.json()["data"]["state"] in {"queued", "running"}:
                await sleep(0.1)
                reply = await client.get(path, headers=headers)
                assert reply.status_code == 200, reply.text
        return reply

    async with AsyncExitStack() as stack:
        connection = await connect(url)
        stack.push_async_callback(connection.close)
        stack.push_async_callback(events.stop)
        await events.start()
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
        reply = await wait_for_completion(operation_url)
        result = reply.json()["data"]
        assert result["state"] == "succeeded", result
        assert result["applied_config_sha256"] == expected_digest
        assert result["started_at"] is not None
        assert result["finished_at"] is not None

        runtime = await client.get(
            f"{instance_url}/runtime-stats", headers=headers
        )
        assert runtime.status_code == 200, runtime.text
        metrics = runtime.json()["data"]
        assert metrics["status"] == "observed", metrics
        assert metrics["runtime"]["goroutines"] > 0
        assert metrics["received_at"] is not None

        outbound = await client.get(
            f"{instance_url}/outbound-health",
            params={"tag": "no-recorded-sample"},
            headers=headers,
        )
        assert outbound.status_code == 200, outbound.text
        data = outbound.json()["data"]
        assert data["status"] == "observed", data
        assert data["observations"] == [
            {
                "tag": "no-recorded-sample",
                "status": "no_sample",
                "delay_milliseconds": None,
                "last_seen_unix_seconds": None,
                "last_try_unix_seconds": None,
            }
        ]

        traffic = await client.get(
            f"{instance_url}/traffic/outbound", headers=headers
        )
        assert traffic.status_code == 200, traffic.text
        view = traffic.json()["data"]
        assert view["status"] == "observed", view
        assert view["entries"] == []
        counter = await client.get(
            f"{instance_url}/traffic/outbound/counter",
            params={"name": "missing-counter"},
            headers=headers,
        )
        assert counter.status_code == 200, counter.text
        assert counter.json()["data"]["status"] == "target_not_found"

        source.write_text(
            '{"outbounds":[{"protocol":"freedom","tag":"other"}]}'
        )
        replay = await client.post(start_url, headers=run_headers)
        assert replay.json()["data"] == result
        jetstream = connection.jetstream()
        duplicate = await jetstream.publish(
            BrokerConfig.start_requested,
            dumps({"operation_id": operation_id}).encode(),
        )
        async with timeout(5):
            while True:
                consumer = await jetstream.consumer_info(
                    duplicate.stream, BrokerConfig.start_durable
                )
                acked = consumer.ack_floor
                if acked is not None and acked.stream_seq >= duplicate.seq:
                    break
                await sleep(0.1)
        status = await client.get(instance_url, headers=headers)
        assert status.status_code == 200, status.text
        observed = status.json()["data"]
        assert observed["status"] == "observed", observed
        assert observed["instance"]["state"] == "ready"
        assert observed["instance"]["applied_config_sha256"] == expected_digest

        local_source = source.read_bytes()
        candidate = '{ "outbounds": [{"protocol":"freedom","tag":"saved"}] }\n'
        revision = await client.post(
            "/admin/xray/revisions",
            headers=headers,
            json={"config_json": candidate},
        )
        assert revision.status_code == 201, revision.text
        metadata = revision.json()["data"]
        revision_id = metadata["id"]
        applied_digest = sha256(candidate.encode()).hexdigest()
        assert metadata["config_sha256"] == applied_digest

        apply_url = (
            f"{instance_url}/config-revisions/{revision_id}/apply-operations"
        )
        apply_headers = {**headers, "Idempotency-Key": str(uuid4())}
        accepted = await client.post(apply_url, headers=apply_headers)
        assert accepted.status_code == 202, accepted.text
        operation = accepted.json()["data"]
        assert operation["revision_id"] == revision_id
        reply = await wait_for_completion(f"{apply_url}/{operation['id']}")
        applied = reply.json()["data"]
        assert applied["state"] == "succeeded", applied
        assert applied["applied_config_sha256"] == applied_digest
        assert (await client.post(apply_url, headers=apply_headers)).json()[
            "data"
        ] == applied
        status = await client.get(instance_url, headers=headers)
        assert status.status_code == 200, status.text
        observed = status.json()["data"]
        assert observed["status"] == "observed", observed
        assert observed["instance"]["applied_config_sha256"] == applied_digest
        assert source.read_bytes() == local_source

        rejected = await client.post(
            "/admin/xray/revisions",
            headers=headers,
            json={
                "config_json": '{"outbounds":[{"protocol":"unknown-test"}]}'
            },
        )
        assert rejected.status_code == 201, rejected.text
        bad_revision = rejected.json()["data"]["id"]
        revisions_url = f"{instance_url}/config-revisions"
        bad_restart = f"{revisions_url}/{bad_revision}/restart-operations"
        accepted = await client.post(
            bad_restart, headers={**headers, "Idempotency-Key": str(uuid4())}
        )
        assert accepted.status_code == 202, accepted.text
        operation = accepted.json()["data"]
        reply = await wait_for_completion(f"{bad_restart}/{operation['id']}")
        result = reply.json()["data"]
        assert result["state"] == "failed"
        assert result["reason"] == "rejected"
        assert result["stopped_at"] is None
        status = await client.get(instance_url, headers=headers)
        assert status.json()["data"]["instance"]["state"] == "ready"

        restart_url = f"{revisions_url}/{revision_id}/restart-operations"
        accepted = await client.post(
            restart_url, headers={**headers, "Idempotency-Key": str(uuid4())}
        )
        assert accepted.status_code == 202, accepted.text
        operation = accepted.json()["data"]
        reply = await wait_for_completion(f"{restart_url}/{operation['id']}")
        result = reply.json()["data"]
        assert result["state"] == "succeeded", result
        assert result["stopped_at"] is not None
        assert result["applied_config_sha256"] == applied_digest

        stop_url = f"{instance_url}/stop-operations"
        accepted = await client.post(
            stop_url, headers={**headers, "Idempotency-Key": str(uuid4())}
        )
        assert accepted.status_code == 202, accepted.text
        operation = accepted.json()["data"]
        reply = await wait_for_completion(f"{stop_url}/{operation['id']}")
        assert reply.json()["data"]["state"] == "succeeded"
        status = await client.get(instance_url, headers=headers)
        assert status.json()["data"]["instance"]["state"] == "stopped"
