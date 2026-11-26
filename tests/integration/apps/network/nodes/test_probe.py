"""Exercise the native scheduler, worker and persisted node observations."""

import asyncio
from contextlib import AsyncExitStack
from datetime import timedelta
from os import environ
from secrets import token_hex
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.uow import PGUnitOfWork, UnitOfWork
from papilio.utils.dates import utc_now
from sqlalchemy import update
from sqlmodel import col
from taskiq.receiver import Receiver

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.app.pipelines.probe import NodeProbePipeline
from src.apps.network.nodes.config import NodeHostConfig
from src.apps.network.nodes.domain.dtos.records import NodeCreate
from src.apps.network.nodes.domain.enums.host import HostStatsStatus
from src.apps.network.nodes.domain.results.host import HostStatsResult
from src.apps.network.nodes.domain.results.probe import NodeProbeTarget
from src.apps.network.nodes.infra.broker.config import BrokerConfig
from src.apps.network.nodes.infra.pg.tables import NodeTable
from src.bootstrap.scheduler import create_scheduler
from src.settings.config import CoreSettings, NatsConfig, SchedulerConfig

from .auth import admin_headers

pytestmark = pytest.mark.integration

NODE_KEY = "isolated-host-rpc-test-key"


class ControlledProbe:
    def __init__(self, held: int, failed: int) -> None:
        self.held = held
        self.failures = {failed}
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.calls: list[int] = []

    async def read(
        self, node_id: int, address: str, port: int
    ) -> HostStatsResult:
        assert UnitOfWork.current() is None
        self.calls.append(node_id)
        if node_id == self.held:
            self.entered.set()
            await self.release.wait()
        status = (
            HostStatsStatus.TIMEOUT
            if node_id in self.failures
            else HostStatsStatus.PARTIAL
        )
        return HostStatsResult(status)


async def test_schedule_updates_registry(
    pg: CoreSettings, app: FastAPI, client: AsyncClient
) -> None:
    nats = environ.get("PAPILIOVPN_TEST_NATS_URL")
    if not nats:
        pytest.skip("Set PAPILIOVPN_TEST_NATS_URL to an isolated JetStream")
    suffix = token_hex(6)
    pg.nats = NatsConfig(servers=[nats])
    pg.scheduler = SchedulerConfig(
        stream=f"node_probes_{suffix}",
        subject=f"node.probes.{suffix}",
        durable=f"node_probes_{suffix}",
        rate_refresh_interval=None,
    )
    headers = await admin_headers(
        app, client, mobile="09120000917", role_key="node-probe-test"
    )
    container = cast(AsyncContainer, app.state.dishka_container)
    ids: dict[str, int] = {}
    previous_updates = {}
    targets = {}
    addresses = {}
    async with container() as scope:
        nodes = await scope.get(INodeService)
        for label in (
            "fast",
            "failed",
            "held",
            "disabled",
            "mismatch",
            "other",
        ):
            address = f"batch-probe-{label}.example.invalid"
            addresses[label] = address
            node = await nodes.create(
                NodeCreate(
                    name=f"BatchProbe {label}",
                    address=address,
                    port=8443,
                    is_enabled=label != "disabled",
                )
            )
            assert node.id is not None and node.updated_at is not None
            ids[label] = node.id
            previous_updates[label] = node.updated_at
            if label != "other":
                targets[node.id] = {
                    "address": address,
                    "port": 8444 if label == "mismatch" else 8443,
                    "api_key": NODE_KEY,
                }
    pg.node_host = NodeHostConfig.model_validate(
        {
            "targets": targets,
            "checks": {
                "interval_seconds": 60,
                "stale_after_seconds": 180,
                "batch_size": 3,
                "concurrency": 2,
            },
        }
    )
    gateway = ControlledProbe(ids["held"], ids["failed"])

    async def detail(label: str) -> dict:
        response = await client.get(
            f"/admin/nodes/{ids[label]}", headers=headers
        )
        assert response.status_code == 200, response.text
        return response.json()["data"]

    broker, beat = create_scheduler(pg)
    broker.is_worker_process = True
    async with AsyncExitStack() as stack:
        stack.push_async_callback(broker.shutdown)
        await broker.startup()
        schedules = []
        for source in beat.sources:
            await source.startup()
            stack.push_async_callback(source.shutdown)
            schedules.extend(
                (source, schedule)
                for schedule in await source.get_schedules()
                if schedule.task_name == BrokerConfig.probe_task
            )
        [(source, schedule)] = schedules
        assert schedule.interval == 60
        assert not schedule.args and not schedule.kwargs
        worker = cast(AsyncContainer, broker.state.papilio_container)
        pipeline = await worker.get(NodeProbePipeline)
        pipeline.gateway = gateway

        messages = broker.listen()
        stack.push_async_callback(messages.aclose)
        await beat.on_ready(source, schedule)
        wire = await asyncio.wait_for(anext(messages), timeout=4)
        receiver = Receiver(broker, run_startup=False, max_async_tasks=1)
        running = asyncio.create_task(receiver.callback(wire))
        try:
            await asyncio.wait_for(gateway.entered.wait(), timeout=4)
            async with asyncio.timeout(4):
                while (await detail("fast"))[
                    "connection_status"
                ] != "reachable":
                    await asyncio.sleep(0.02)
            duplicate = await pipeline.run()
            assert duplicate.selected == 0
            protected = await pipeline.execution.claim(
                (NodeProbeTarget(ids["held"], addresses["held"], 8443),),
                delay=timedelta(microseconds=1),
                reclaim_after=timedelta(minutes=1),
                limit=1,
            )
            assert not protected

            path = f"/admin/nodes/{ids['held']}"
            for address in ("new-target.example.invalid", addresses["held"]):
                changed = await client.patch(
                    path, headers=headers, json={"address": address}
                )
                assert changed.status_code == 200, changed.text
        finally:
            gateway.release.set()
            await asyncio.wait_for(running, timeout=4)

        assert sorted(gateway.calls) == sorted(
            ids[label] for label in ("fast", "failed", "held")
        )
        page = await client.get(
            "/admin/nodes", params={"q": "BatchProbe"}, headers=headers
        )
        assert page.status_code == 200, page.text
        rows = {row["id"]: row for row in page.json()["data"]}
        assert len(rows) == 6
        success = rows[ids["fast"]]
        assert success["connection_status"] == "reachable"
        assert success["connection_stale"] is False
        assert success["last_checked_at"] == success["last_seen_at"]
        assert success["last_seen_at"] is not None
        original_updated = (
            previous_updates["fast"].isoformat().replace("+00:00", "Z")
        )
        assert success["updated_at"] == original_updated
        assert rows[ids["failed"]]["connection_status"] == "timeout"
        assert rows[ids["failed"]]["last_seen_at"] is None
        for label in ("held", "disabled", "mismatch", "other"):
            row = rows[ids[label]]
            assert row["connection_status"] == "unchecked"
            assert row["last_checked_at"] is None

        async with container() as scope:
            uow = await scope.get(PGUnitOfWork)
            old = utc_now() - timedelta(minutes=5)
            stmt = (
                update(NodeTable)
                .where(col(NodeTable.id) == ids["fast"])
                .values(probe_started_at=old, last_checked_at=old)
            )
            async with uow.transaction():
                await uow.execute(stmt)
        stale = await detail("fast")
        assert stale["connection_stale"] is True
        assert stale["connection_status"] == "reachable"
        gateway.failures.add(ids["fast"])
        await pipeline.run()
        failed = await detail("fast")
        assert failed["connection_status"] == "timeout"
        assert failed["connection_stale"] is False
        assert failed["last_seen_at"] == success["last_seen_at"]
