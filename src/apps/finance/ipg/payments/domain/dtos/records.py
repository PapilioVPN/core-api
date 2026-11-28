"""Validated terms for issuing an internal IPG payment."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import RialType
from pydantic import AnyUrl, StringConstraints, UrlConstraints

from ....gateways.domain.enums.records import GatewayKind

type Description = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]
type CallbackURL = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]


class PaymentCreate(BaseDTO):
    kind: GatewayKind
    amount: RialType
    description: Description
    callback_url: CallbackURL
