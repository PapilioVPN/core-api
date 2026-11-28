"""Dispatch typed routing mutations through the pinned Node protocol."""

from grpc import StatusCode
from grpc.aio import AioRpcError
from papilio.utils.dates import utc_now

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels

from ...domain.dtos.mutations import RoutingIntent
from ...domain.enums.operation import (
    RoutingAction,
    RoutingFailure,
    RoutingState,
)
from ...domain.results.operation import RoutingOutcome, RoutingTarget
from .v1 import routing_pb2 as wire
from .v1.routing_pb2_grpc import XrayRoutingServiceStub

_FAILED = {
    StatusCode.NOT_FOUND: RoutingFailure.TARGET_NOT_FOUND,
    StatusCode.ALREADY_EXISTS: RoutingFailure.ALREADY_EXISTS,
    StatusCode.FAILED_PRECONDITION: RoutingFailure.FENCED,
    StatusCode.RESOURCE_EXHAUSTED: RoutingFailure.RESOURCE_LIMIT,
    StatusCode.INVALID_ARGUMENT: RoutingFailure.REJECTED,
    StatusCode.UNAUTHENTICATED: RoutingFailure.REJECTED,
    StatusCode.PERMISSION_DENIED: RoutingFailure.REJECTED,
    StatusCode.UNIMPLEMENTED: RoutingFailure.UNSUPPORTED,
}
_UNKNOWN = {
    StatusCode.DEADLINE_EXCEEDED: RoutingFailure.TIMEOUT,
    StatusCode.UNAVAILABLE: RoutingFailure.UNAVAILABLE,
}


class XrayRoutingGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def mutate(
        self, target: RoutingTarget, intent: RoutingIntent
    ) -> RoutingOutcome:
        """Issue one routing RPC without repeating an ambiguous delivery.

        Args:
            target: The pinned Node management endpoint and dispatch window.
            intent: Authenticated, decoded operator intent.

        Returns:
            Node acknowledgement, a definite rejection or uncertainty.
            Caller cancellation propagates.
        """
        channel = await self.channels.get(target.node)
        remaining = (target.deadline_at - utc_now()).total_seconds()
        if remaining <= 0:
            outcome = RoutingOutcome(
                RoutingState.UNKNOWN, RoutingFailure.DISPATCH_EXPIRED
            )
        elif channel is None:
            outcome = RoutingOutcome(
                RoutingState.FAILED, RoutingFailure.NOT_CONFIGURED
            )
        else:
            try:
                await self._send(
                    XrayRoutingServiceStub(channel),
                    target.instance_id,
                    intent,
                    min(remaining, 2),
                )
            except AioRpcError as error:
                code = error.code()
                failure = _FAILED.get(code)
                outcome = (
                    RoutingOutcome(RoutingState.FAILED, failure)
                    if failure is not None
                    else RoutingOutcome(
                        RoutingState.UNKNOWN,
                        _UNKNOWN.get(code, RoutingFailure.UNCONFIRMED),
                    )
                )
            else:
                outcome = RoutingOutcome(RoutingState.ACKNOWLEDGED)
        return outcome

    async def _send(
        self,
        stub: XrayRoutingServiceStub,
        instance_id: str,
        intent: RoutingIntent,
        timeout: float,
    ) -> None:
        match intent.action:
            case RoutingAction.APPEND | RoutingAction.REPLACE:
                replace = intent.action is RoutingAction.REPLACE
                modes = wire.XrayRoutingRuleMode
                await stub.AddRoutingRule(
                    wire.XrayAddRoutingRuleRequest(
                        id=instance_id,
                        rule_json=intent.rule.rule_json.encode(),
                        mode=modes.XRAY_ROUTING_RULE_MODE_REPLACE
                        if replace
                        else modes.XRAY_ROUTING_RULE_MODE_APPEND,
                        confirm_replace=replace,
                    ),
                    timeout=timeout,
                )
            case RoutingAction.REMOVE:
                await stub.RemoveRoutingRule(
                    wire.XrayRemoveRoutingRuleRequest(
                        id=instance_id, rule_tag=intent.tag
                    ),
                    timeout=timeout,
                )
            case RoutingAction.OVERRIDE | RoutingAction.CLEAR:
                await stub.OverrideBalancerTarget(
                    wire.XrayOverrideBalancerTargetRequest(
                        id=instance_id,
                        tag=intent.tag,
                        target=intent.override.target
                        if intent.action is RoutingAction.OVERRIDE
                        else "",
                    ),
                    timeout=timeout,
                )
