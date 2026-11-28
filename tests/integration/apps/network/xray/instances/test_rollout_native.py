"""Run an ordered restart across two real Nodes and recover its cursor."""

import ssl
from asyncio import Event, create_subprocess_exec, sleep, timeout, wait_for
from contextlib import AsyncExitStack
from os import environ
from pathlib import Path
from sys import executable
from typing import cast
from uuid import uuid4

import pytest
import yaml
from dishka import AsyncContainer
from fastapi import FastAPI
from faststream.exceptions import NackMessage
from httpx import AsyncClient

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.config import NodeHostConfig, NodeHostTarget
from src.apps.network.nodes.domain.dtos.records import NodeCreate
from src.apps.network.xray.instances.app.pipelines.control import (
    XrayControlPipeline,
)
from src.bootstrap.events import create_events
from src.settings.config import CoreSettings, NatsConfig

from ...nodes.auth import admin_headers
from ..conftest import RunningXrayNode
from .test_rollout import ROLLOUT_PATH

pytestmark = pytest.mark.integration


async def test_real_rollout_recovers_after_worker_exit_and_halts_on_rejection(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    tmp_path: Path,
    node_pair: tuple[RunningXrayNode, RunningXrayNode],
    node_api_key: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broker = environ.get("PAPILIOVPN_TEST_NATS_URL")
    if not broker:
        pytest.skip("Set PAPILIOVPN_TEST_NATS_URL to isolated JetStream")
    headers = await admin_headers(
        app, client, mobile="09120000787", role_key="xray-rollout-native"
    )
    container = cast(AsyncContainer, app.state.dishka_container)
    targets = {}
    for index, (grpc_port, http_port, ca, _) in enumerate(node_pair):
        tls = ssl.create_default_context()
        ca.configure_trust(tls)
        async with AsyncClient(
            verify=tls, headers={"X-API-Key": node_api_key}
        ) as native:
            started = await native.put(
                f"https://127.0.0.1:{http_port}/v1/xray/instances/edge/execution",
                timeout=10,
            )
            assert started.is_success, started.text
        async with container() as scope:
            nodes = await scope.get(INodeService)
            node = await nodes.create(
                NodeCreate(
                    name=f"Restart rollout {index}",
                    address="127.0.0.1",
                    port=grpc_port,
                )
            )
        targets[node.id] = NodeHostTarget.model_validate(
            {
                "address": node.address,
                "port": grpc_port,
                "api_key": node_api_key,
                "ca_pem": ca.cert_pem.bytes().decode(),
            }
        )
    pg.node_host = NodeHostConfig(targets=targets)
    pg.nats = NatsConfig(servers=[broker], graceful_timeout=1)
    selection = {
        "targets": [{"node_id": id, "instance_id": "edge"} for id in targets]
    }

    async def submit(source: str) -> tuple[str, dict]:
        revision = await client.post(
            "/admin/xray/revisions",
            headers=headers,
            json={"config_json": source},
        )
        assert revision.status_code == 201, revision.text
        base = ROLLOUT_PATH.format(revision_id=revision.json()["data"]["id"])
        reply = await client.post(
            base,
            headers={**headers, "Idempotency-Key": str(uuid4())},
            json=selection,
        )
        assert reply.status_code == 202, reply.text
        plan = reply.json()["data"]
        return f"{base}/{plan['id']}", plan

    async def read(path: str) -> dict:
        reply = await client.get(path, headers=headers)
        assert reply.status_code == 200, reply.text
        return reply.json()["data"]

    async def wait_terminal(path: str) -> dict:
        async with timeout(20):
            while True:
                result = await read(path)
                if result["state"] != "running":
                    break
                await sleep(0.05)
        return result

    path, plan = await submit(
        '{"outbounds":[{"protocol":"freedom","tag":"rollout"}]}'
    )
    first_id = plan["steps"][0]["operation"]["id"]
    interrupted = Event()
    original_control = XrayControlPipeline.run

    async def interrupt_after_commit(
        self: XrayControlPipeline, id: int
    ) -> None:
        await original_control(self, id)
        if id == first_id and not interrupted.is_set():
            interrupted.set()
            raise NackMessage(delay=3)

    relay_config = tmp_path / "restart-rollout-relay.yml"
    relay_config.write_text(yaml.safe_dump(pg.model_dump(mode="json")))
    async with AsyncExitStack() as stack:
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
        with monkeypatch.context() as patch:
            patch.setattr(XrayControlPipeline, "run", interrupt_after_commit)
            old_worker = create_events(pg)
            await old_worker.start()
            try:
                await wait_for(interrupted.wait(), 12)
                paused = await read(path)
                assert paused["state"] == "running"
                assert [item["state"] for item in paused["steps"]] == [
                    "succeeded",
                    "pending",
                ]
                successful_first = paused["steps"][0]["operation"]
            finally:
                await old_worker.stop()

        worker = create_events(pg)
        stack.push_async_callback(worker.stop)
        await worker.start()
        completed = await wait_terminal(path)
        assert completed["state"] == "succeeded", completed
        one, two = [step["operation"] for step in completed["steps"]]
        assert one == successful_first
        assert one["finished_at"] <= two["started_at"]
        assert one["stopped_at"] and two["stopped_at"]
        assert (
            one["applied_config_sha256"]
            == two["applied_config_sha256"]
            == plan["config_sha256"]
        )

        bad_path, _ = await submit(
            '{"outbounds":[{"protocol":"unknown-rollout-test"}]}'
        )
        halted = await wait_terminal(bad_path)
        assert (halted["state"], halted["reason"]) == (
            "halted",
            "target_failed",
        )
        assert [item["state"] for item in halted["steps"]] == [
            "failed",
            "pending",
        ]
        assert halted["steps"][0]["operation"]["reason"] == "rejected"
        assert halted["steps"][0]["operation"]["stopped_at"] is None
        assert halted["steps"][1]["operation"] is None
        for id in targets:
            reply = await client.get(
                f"/admin/nodes/{id}/xray/instances/edge", headers=headers
            )
            engine = reply.json()["data"]["instance"]
            assert engine["state"] == "ready"
            assert engine["applied_config_sha256"] == plan["config_sha256"]
