"""Call Xray's versioned validation RPC using the shared Node transport."""

from grpc import StatusCode
from grpc.aio import AioRpcError

from src.apps.network.nodes.infra.grpc.channels import NodeChannels

from ...domain.enums.dry_run import XrayValidationStatus
from ...domain.results.dry_run import XrayValidationOutcome
from .codec import decode_validation
from .v1.configs_pb2 import ValidateXrayConfigRequest, XrayConfigValidation
from .v1.configs_pb2_grpc import XrayConfigsServiceStub

# Leave one second for transport beyond Node's four-second validation budget.
_VALIDATION_DEADLINE_SECONDS = 5

_RPC_OUTCOMES = {
    StatusCode.NOT_FOUND: XrayValidationStatus.INSTANCE_NOT_FOUND,
    StatusCode.ABORTED: XrayValidationStatus.BUSY,
    StatusCode.RESOURCE_EXHAUSTED: XrayValidationStatus.RESOURCE_LIMIT,
    StatusCode.DEADLINE_EXCEEDED: XrayValidationStatus.TIMEOUT,
    StatusCode.UNAVAILABLE: XrayValidationStatus.UNAVAILABLE,
    StatusCode.UNAUTHENTICATED: XrayValidationStatus.REJECTED,
    StatusCode.PERMISSION_DENIED: XrayValidationStatus.REJECTED,
    StatusCode.UNIMPLEMENTED: XrayValidationStatus.UNSUPPORTED,
}


class XrayConfigGateway:
    def __init__(self, channels: NodeChannels) -> None:
        """Borrow the shared Node management channels."""
        self.channels = channels

    async def validate(
        self,
        *,
        node_id: int,
        address: str,
        port: int,
        instance_id: str,
        source: bytes,
    ) -> XrayValidationOutcome:
        """Ask the exact configured target to validate the proposal.

        Args:
            node_id: Registry identity bound to the management credentials.
            address: Registered management address.
            port: Registered management port.
            instance_id: Instance selected by the administrator.
            source: Exact candidate bytes, never the node's configured file.

        Returns:
            A validation or transport outcome without raw diagnostics.
            Caller cancellation remains native.
        """
        channel = self.channels.get(node_id, address, port)
        if channel is None:
            outcome = XrayValidationOutcome(
                XrayValidationStatus.NOT_CONFIGURED
            )
        else:
            stub = XrayConfigsServiceStub(channel)
            try:
                reply: XrayConfigValidation = await stub.ValidateConfig(
                    ValidateXrayConfigRequest(
                        id=instance_id, config_json=source
                    ),
                    timeout=_VALIDATION_DEADLINE_SECONDS,
                )
            except AioRpcError as error:
                status = _RPC_OUTCOMES.get(
                    error.code(), XrayValidationStatus.FAILED
                )
                outcome = XrayValidationOutcome(status)
            else:
                outcome = decode_validation(reply, instance_id)
        return outcome
