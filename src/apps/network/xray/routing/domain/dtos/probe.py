"""Select a route using the active Xray execution without publication."""

from typing import Annotated, Literal

from papilio.schemas.inputs import BaseDTO
from pydantic import AfterValidator, Field, IPvAnyAddress

from .identity import RoutingText
from .validators.probe import require_attribute_budget, require_unscoped_ip

type RouteIP = Annotated[IPvAnyAddress, AfterValidator(require_unscoped_ip)]
type RouteAttributes = Annotated[
    dict[RoutingText, RoutingText],
    Field(max_length=32),
    AfterValidator(require_attribute_budget),
]


class XrayRouteProbe(BaseDTO):
    inbound_tag: RoutingText = ""
    network: Literal["", "tcp", "udp"] = ""
    target_ip: RouteIP | None = None
    target_domain: RoutingText = ""
    target_port: int = Field(default=0, ge=0, le=65535, strict=True)
    protocol: RoutingText = ""
    user: RoutingText = Field(default="", repr=False)
    attributes: RouteAttributes = Field(default_factory=dict, repr=False)
