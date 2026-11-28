"""Check live-log loss markers and bounded transport admission."""

from asyncio import Event
from unittest.mock import AsyncMock, Mock

import pytest
from grpc import StatusCode

from src.apps.network.nodes.connections.infra.grpc import streams
from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.observations.domain.enums.logs import LogStreamEnd
from src.apps.network.nodes.registry.domain.models.records import NodeModel
from src.apps.network.xray.logs.infra.grpc import live
from src.apps.network.xray.logs.infra.grpc.codec import decode_line
from src.apps.network.xray.logs.infra.grpc.v1 import logs_pb2 as wire
from src.apps.network.xray.logs.routers.schemas.live import XrayLogLineOutput

pytestmark = pytest.mark.unit


def test_log_line_preserves_gap_precision_and_decode_loss() -> None:
    message = wire.XrayLogEvent(
        execution=9007199254740993,
        sequence=9007199254741000,
        source=wire.XRAY_LOG_SOURCE_STDERR,
        received_unix_nano=1790000000000000001,
        message=b"broken \xff byte",
        truncated=True,
    )
    first = decode_line(message, None)
    assert first.missed_before is None
    assert decode_line(message, 9007199254740999).missed_before == 0
    line = decode_line(message, 9007199254740995)
    assert XrayLogLineOutput.from_line(line).model_dump(mode="json") == {
        "execution": "9007199254740993",
        "sequence": "9007199254741000",
        "received_unix_nano": "1790000000000000001",
        "source": "stderr",
        "message": "broken \ufffd byte",
        "truncated": True,
        "encoding_replaced": True,
        "missed_before": "4",
    }


async def test_no_wait_admission_releases_only_the_owned_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(streams, "_MAX_STREAMS", 1)
    channel = Mock()
    channels = Mock(spec=NodeChannels)
    channels.get.return_value = channel
    calls = [Mock(done=Mock(return_value=False)) for _ in range(2)]
    for call in calls:
        call.initial_metadata = AsyncMock()
    start = Mock(side_effect=calls)
    monkeypatch.setattr(
        live, "XrayLogsServiceStub", Mock(return_value=Mock(GetLogs=start))
    )
    gateway = live.XrayLogsGateway(streams.NodeLogStreams(channels))
    node = NodeModel(id=3, name="Logs", address="logs.invalid", port=81)
    async with gateway.follow(node, "edge") as first:
        assert first.entries is not None
        async with gateway.follow(node, "edge") as rejected:
            assert rejected.end is LogStreamEnd.BUSY
        assert start.call_count == 1
        calls[0].cancel.assert_not_called()
    calls[0].cancel.assert_called_once()
    async with gateway.follow(node, "edge") as reopened:
        assert reopened.entries is not None
        calls[1].cancel.assert_not_called()
    calls[1].cancel.assert_called_once()
    channel.close.assert_not_called()


async def test_stalled_open_times_out_before_any_log_arrives(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(streams, "_OPEN_TIMEOUT", 0.01)
    call = Mock(initial_metadata=AsyncMock(side_effect=Event().wait))
    start = Mock(return_value=call)
    monkeypatch.setattr(
        live, "XrayLogsServiceStub", Mock(return_value=Mock(GetLogs=start))
    )
    transport = streams.NodeLogStreams(Mock(spec=NodeChannels))
    gateway = live.XrayLogsGateway(transport)
    node = NodeModel(id=3, name="Logs", address="logs.invalid", port=81)
    async with gateway.follow(node, "edge") as outcome:
        assert outcome.end is LogStreamEnd.TIMEOUT
    call.cancel.assert_called_once()
    assert transport.capacity.borrowed_tokens == 0


async def test_closed_rpc_drains_buffered_lines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = AsyncMock()
    call.done = Mock(return_value=True)
    call.cancel = Mock(return_value=False)
    call.code.return_value = StatusCode.OK
    buffered = wire.XrayLogEvent(sequence=1)
    call.__aiter__.return_value = [buffered]
    monkeypatch.setattr(
        live,
        "XrayLogsServiceStub",
        Mock(return_value=Mock(GetLogs=Mock(return_value=call))),
    )
    transport = streams.NodeLogStreams(Mock(spec=NodeChannels))
    gateway = live.XrayLogsGateway(transport)
    node = NodeModel(id=3, name="Logs", address="logs.invalid", port=81)

    async with gateway.follow(node, "edge") as feed:
        assert feed.entries is not None
        assert [event async for event in feed.entries] == [
            decode_line(buffered, None),
            LogStreamEnd.ENDED,
        ]
    call.cancel.assert_called_once()
