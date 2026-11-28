"""Verify set admission and cancellation outside the Node transport."""

from asyncio import CancelledError, Event, create_task, wait_for
from unittest.mock import AsyncMock, Mock

import pytest

from src.apps.network.nodes.app.interfaces.endpoints import INodeEndpointQuery
from src.apps.network.nodes.domain.results.records import NodeEndpoint
from src.apps.network.xray.instances.app.interfaces.status import (
    IXrayStatusGateway,
)
from src.apps.network.xray.instances.app.queries.fleet_status import (
    XrayFleetStatusQuery,
)
from src.apps.network.xray.instances.app.services.status_fanout import (
    XrayStatusFanout,
)
from src.apps.network.xray.instances.domain.dtos.fleet_status import (
    XrayFleetStatusInput,
)
from src.apps.network.xray.instances.domain.dtos.identity import (
    XrayInstanceTarget,
)
from src.apps.network.xray.instances.domain.enums.status import XrayStatusCode
from src.apps.network.xray.instances.domain.results.status import (
    XrayStatusResult,
)

pytestmark = pytest.mark.unit


async def test_fleet_shares_capacity_and_releases_it_after_cancellation() -> (
    None
):
    endpoint = NodeEndpoint(10, "node.example.invalid", 443, True)
    nodes = Mock(spec=INodeEndpointQuery)
    nodes.get_endpoints = AsyncMock(return_value={10: endpoint})
    entered = Event()
    waiting = Event()
    gateway = Mock(spec=IXrayStatusGateway)

    async def read(
        node_id: int, address: str, port: int, instance_id: str
    ) -> XrayStatusResult:
        if instance_id == "held":
            entered.set()
            await waiting.wait()
        return XrayStatusResult(XrayStatusCode.UNAVAILABLE)

    gateway.read = AsyncMock(side_effect=read)
    fanout = XrayStatusFanout(gateway)
    fanout.capacity.total_tokens = 1
    first = XrayFleetStatusQuery(nodes, fanout)
    second = XrayFleetStatusQuery(nodes, fanout)
    held = XrayInstanceTarget(node_id=10, instance_id="held")
    ready = XrayInstanceTarget(node_id=10, instance_id="fresh")
    absent = XrayInstanceTarget(node_id=20, instance_id="fresh")

    task = create_task(first.get(XrayFleetStatusInput(targets=[held, held])))
    try:
        await wait_for(entered.wait(), 1)
        nodes.get_endpoints.assert_awaited_once_with((10,))
        snapshot = await wait_for(
            second.get(XrayFleetStatusInput(targets=[ready, absent, ready])), 1
        )
        assert [row.result.status for row in snapshot] == [
            XrayStatusCode.BUSY,
            XrayStatusCode.NODE_NOT_FOUND,
            XrayStatusCode.BUSY,
        ]
        nodes.get_endpoints.assert_awaited_with((10, 20))
        gateway.read.assert_awaited_once_with(
            10, endpoint.address, 443, "held"
        )
    finally:
        task.cancel()
        with pytest.raises(CancelledError):
            await task

    after = await second.get(XrayFleetStatusInput(targets=[ready, ready]))
    assert after[0] == after[1]
    assert after[0].result.status is XrayStatusCode.UNAVAILABLE
    assert gateway.read.await_count == 2
    assert fanout.capacity.borrowed_tokens == 0
