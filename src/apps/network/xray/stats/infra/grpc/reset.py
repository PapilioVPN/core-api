"""Submit exactly one reset to the versioned Node stats API."""

from grpc.aio import AioRpcError
from papilio.utils.dates import utc_now

from src.apps.network.nodes.infra.grpc.channels import NodeChannels

from ...domain.enums.reset import (
    ResetEffect,
    ResetKind,
    ResetReason,
    ResetState,
)
from ...domain.results.reset import (
    ResetCounterEvidence,
    ResetOutcome,
    ResetTarget,
)
from .reset_codec import (
    decode_failure,
    decode_pair,
    decode_scope,
    encode_direction,
)
from .traffic import encode_scope
from .v1 import traffic_pb2 as wire
from .v1.runtime_stats_pb2_grpc import XrayStatsServiceStub


class XrayResetGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def reset(self, target: ResetTarget) -> ResetOutcome:
        """Send one operation and map Node's explicit evidence."""
        remaining = (target.deadline_at - utc_now()).total_seconds()
        channel = self.channels.get(
            target.node_id, target.address, target.port
        )
        if remaining <= 0:
            result = ResetOutcome(
                ResetState.UNKNOWN, ResetReason.DISPATCH_EXPIRED
            )
        elif channel is None:
            result = ResetOutcome(
                ResetState.NOT_APPLIED, ResetReason.NOT_CONFIGURED
            )
        else:
            try:
                result = await self._send(
                    XrayStatsServiceStub(channel), target, remaining
                )
            except AioRpcError as error:
                selection = target.selection
                result = decode_failure(
                    error,
                    selection.name
                    if selection.kind is ResetKind.PAIR
                    else None,
                )
        return result

    async def _send(
        self, stub: XrayStatsServiceStub, target: ResetTarget, remaining: float
    ) -> ResetOutcome:
        selection = target.selection
        scope = encode_scope(selection.scope)
        id = target.instance_id
        if (
            selection.kind is ResetKind.COUNTER
            and selection.name is not None
            and selection.direction is not None
        ):
            reply = await stub.ResetTrafficCounter(
                wire.XrayTrafficResetRequest(
                    id=id,
                    scope=scope,
                    name=selection.name,
                    direction=encode_direction(selection.direction),
                ),
                timeout=min(remaining, 3),
            )
            counter = ResetCounterEvidence(
                name=selection.name,
                direction=selection.direction,
                effect=ResetEffect.ACKNOWLEDGED,
                previous_bytes=reply.previous_bytes,
            )
            result = ResetOutcome(ResetState.COMPLETE, counters=(counter,))
        elif selection.kind is ResetKind.PAIR and selection.name is not None:
            pair = await stub.ResetTrafficPair(
                wire.XrayTrafficPairResetRequest(
                    id=id,
                    scope=scope,
                    name=selection.name,
                ),
                timeout=min(remaining, 3),
            )
            result = decode_pair(selection.name, pair)
        elif (
            selection.kind is ResetKind.SCOPE
            and selection.max_counters is not None
        ):
            report = await stub.ResetTrafficScope(
                wire.XrayTrafficScopeResetRequest(
                    id=id,
                    scope=scope,
                    max_counters=selection.max_counters,
                ),
                timeout=min(remaining, 7),
            )
            result = decode_scope(report, selection.max_counters)
        else:
            result = ResetOutcome(ResetState.NOT_APPLIED, ResetReason.REJECTED)
        return result
