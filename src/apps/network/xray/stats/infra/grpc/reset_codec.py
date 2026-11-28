"""Decode actual reset effects from replies and rich gRPC failure details."""

from google.protobuf.message import DecodeError
from google.rpc.status_pb2 import Status
from grpc import StatusCode
from grpc.aio import AioRpcError

from ...domain.enums.reset import (
    ResetEffect,
    ResetReason,
    ResetState,
    TrafficDirection,
)
from ...domain.results.reset import ResetCounterEvidence, ResetOutcome
from .v1 import traffic_pb2 as wire

_DIRECTIONS = {
    TrafficDirection.UPLINK: wire.XRAY_TRAFFIC_DIRECTION_UPLINK,
    TrafficDirection.DOWNLINK: wire.XRAY_TRAFFIC_DIRECTION_DOWNLINK,
}
_WIRE_DIRECTIONS = {value: key for key, value in _DIRECTIONS.items()}
_EFFECT = wire.XrayTrafficDirectionReset
_EFFECTS = {
    _EFFECT.ACKNOWLEDGED: ResetEffect.ACKNOWLEDGED,
    _EFFECT.MISSING: ResetEffect.MISSING,
    _EFFECT.NOT_APPLIED: ResetEffect.NOT_APPLIED,
    _EFFECT.NOT_ATTEMPTED: ResetEffect.NOT_ATTEMPTED,
}
_REASONS = {
    StatusCode.NOT_FOUND: ResetReason.TARGET_NOT_FOUND,
    StatusCode.PERMISSION_DENIED: ResetReason.REJECTED,
    StatusCode.UNAUTHENTICATED: ResetReason.REJECTED,
    StatusCode.INVALID_ARGUMENT: ResetReason.REJECTED,
    StatusCode.FAILED_PRECONDITION: ResetReason.REJECTED,
    StatusCode.RESOURCE_EXHAUSTED: ResetReason.RESOURCE_LIMIT,
    StatusCode.UNIMPLEMENTED: ResetReason.UNSUPPORTED,
    StatusCode.DEADLINE_EXCEEDED: ResetReason.TIMEOUT,
    StatusCode.UNAVAILABLE: ResetReason.UNAVAILABLE,
    StatusCode.ABORTED: ResetReason.INTERRUPTED,
}


def encode_direction(
    direction: TrafficDirection,
) -> wire.XrayTrafficDirection:
    """Translate the exact action direction to the Node enum."""
    return _DIRECTIONS[direction]


def _evidence(
    name: str,
    direction: TrafficDirection,
    value: wire.XrayTrafficDirectionReset,
) -> ResetCounterEvidence:
    effect = _EFFECTS.get(value.effect, ResetEffect.UNKNOWN)
    previous = None
    if effect is ResetEffect.ACKNOWLEDGED:
        if value.HasField("previous_bytes"):
            previous = value.previous_bytes
        else:
            effect = ResetEffect.UNKNOWN
    return ResetCounterEvidence(
        name=name, direction=direction, effect=effect, previous_bytes=previous
    )


def _report(
    counters: tuple[ResetCounterEvidence, ...],
    *,
    interrupted: bool,
    reason: ResetReason | None = None,
) -> ResetOutcome:
    effects = {counter["effect"] for counter in counters}
    if ResetEffect.UNKNOWN in effects:
        state = ResetState.UNKNOWN
        reason = reason or ResetReason.UNCONFIRMED
    elif interrupted or effects & {
        ResetEffect.NOT_APPLIED,
        ResetEffect.NOT_ATTEMPTED,
    }:
        state = (
            ResetState.PARTIAL
            if ResetEffect.ACKNOWLEDGED in effects
            else ResetState.NOT_APPLIED
        )
        reason = reason or ResetReason.INTERRUPTED
    else:
        state = ResetState.COMPLETE
    return ResetOutcome(state, reason, counters)


def decode_pair(
    name: str,
    reply: wire.XrayTrafficPairResetResult,
    *,
    reason: ResetReason | None = None,
) -> ResetOutcome:
    """Preserve progress for both directions, including missing values."""
    return _report(
        (
            _evidence(name, TrafficDirection.UPLINK, reply.uplink),
            _evidence(name, TrafficDirection.DOWNLINK, reply.downlink),
        ),
        interrupted=reason is not None,
        reason=reason,
    )


def decode_scope(
    reply: wire.XrayTrafficScopeResetResult, limit: int
) -> ResetOutcome:
    """Keep the scope-level outcome and every bounded reported counter."""
    counters = []
    valid = len(reply.counters) <= limit
    seen: set[tuple[str, TrafficDirection]] = set()
    for row in reply.counters[:limit]:
        direction = _WIRE_DIRECTIONS.get(row.direction)
        if direction is None or not row.name or (row.name, direction) in seen:
            valid = False
        else:
            seen.add((row.name, direction))
            counters.append(_evidence(row.name, direction, row.result))
    report = tuple(counters)
    outcomes = wire.XrayTrafficScopeResetResult
    if not valid or reply.outcome not in (
        outcomes.COMPLETE,
        outcomes.INTERRUPTED,
    ):
        result = ResetOutcome(
            ResetState.UNKNOWN, ResetReason.UNCONFIRMED, report
        )
    else:
        result = _report(
            report, interrupted=reply.outcome == outcomes.INTERRUPTED
        )
    return result


def _details(error: AioRpcError) -> Status:
    status = Status()
    metadata = error.trailing_metadata()
    if metadata is not None:
        for key, value in metadata:
            if key == "grpc-status-details-bin" and isinstance(value, bytes):
                try:
                    status.ParseFromString(value)
                except DecodeError:
                    status.Clear()
                break
        if status.code != error.code().value[0]:
            status.Clear()
    return status


def decode_failure(error: AioRpcError, pair_name: str | None) -> ResetOutcome:
    """Classify only explicit failure effects as known."""
    reason = _REASONS.get(error.code(), ResetReason.UNCONFIRMED)
    outcome = ResetOutcome(ResetState.UNKNOWN, reason)
    for detail in _details(error).details:
        failure = wire.XrayTrafficResetFailure()
        pair = wire.XrayTrafficPairResetResult()
        try:
            if pair_name is not None and detail.Unpack(pair):
                outcome = decode_pair(pair_name, pair, reason=reason)
                break
            if (
                detail.Unpack(failure)
                and failure.effect == failure.NOT_APPLIED
            ):
                outcome = ResetOutcome(ResetState.NOT_APPLIED, reason)
                break
        except DecodeError:
            continue
    return outcome
