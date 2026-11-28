"""Public fields of a gateway configuration for the panel."""

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.records import GatewayKind


class ConfigOutput(BaseOutput):
    key: GatewayKind
    configured: bool
