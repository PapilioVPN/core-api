"""Hysteria log bodies with precise cursors and timestamps."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    UInt64Text,
)


class HysteriaLogEventOutput(BaseOutput):
    execution: UInt64Text
    sequence: UInt64Text
    received_unix_nano: UInt64Text
    event: str
