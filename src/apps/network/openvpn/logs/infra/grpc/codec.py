"""Decode the native OpenVPN replay batches and their dropped counts."""

from ....instances.infra.grpc.v1 import openvpn_instances_pb2 as wire
from ...domain.results.logs import OpenVPNLogBatch, OpenVPNLogLine


def decode(
    reply: wire.OpenVPNLogBatch, *, expected_execution: str | None
) -> OpenVPNLogBatch | None:
    result = None
    if (
        reply.execution_id
        and reply.entries
        and (
            not expected_execution or expected_execution == reply.execution_id
        )
    ):
        result = OpenVPNLogBatch(
            execution_id=reply.execution_id,
            dropped=reply.dropped,
            entries=tuple(
                OpenVPNLogLine(
                    sequence=entry.sequence,
                    timestamp_unix_seconds=entry.timestamp,
                    level=entry.level,
                    message=entry.message,
                )
                for entry in reply.entries
            ),
        )
    return result
