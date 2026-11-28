"""Public fields of a gateway configuration for the panel."""

from papilio.schemas.outputs import BaseOutput

from ...domain.dtos.configs import CardSelection, LinkExpiry
from ...domain.enums.records import GatewayKind


class ConfigOutput(BaseOutput):
    key: GatewayKind
    card_last_4: CardSelection | None = None
    expires_in: LinkExpiry | None = None
